import json
import tempfile
import unittest
from pathlib import Path

from aab import business_case, lake, policy_digest, portfolio, synth, value_stream

ROOT = Path(__file__).resolve().parent.parent
RUN_DATE = "2026-11-27"


class LakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        synth.write_all(base / "raw")
        cls.res = lake.run(base / "raw", base / "lake", RUN_DATE)
        cls.base = base

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_injected_usage_defect_is_caught(self):
        checks = self.res["quality"]["ai_usage_events"]["checks"]
        for reason in ("duplicate row", "missing or unknown user_id", "quality_rating not in 1-5",
                       "event_date outside pilot window", "unknown tool"):
            self.assertGreaterEqual(checks.get(reason, 0), 1, reason)
        self.assertEqual(self.res["quality"]["ai_usage_events"]["quarantined"], 5)

    def test_quarantine_keeps_rejected_rows_with_reason(self):
        q = (self.base / "lake" / "silver" / "quarantine" / "ai_usage_events.csv").read_text(encoding="utf-8")
        self.assertIn("_reason", q.splitlines()[0])
        self.assertEqual(len(q.strip().splitlines()) - 1, 5)

    def test_personal_data_is_masked_in_silver(self):
        silver = (self.base / "lake" / "silver" / "ai_usage_events.csv").read_text(encoding="utf-8")
        self.assertNotIn("jane.doe@example.com", silver)
        self.assertIn("[EMAIL]", silver)

    def test_bronze_is_an_unchanged_copy_with_lineage(self):
        manifest = json.loads((self.base / "lake" / "bronze" / "_manifest.json").read_text())
        self.assertEqual({m["dataset"] for m in manifest}, {"users", "ai_usage_events", "policy_news"})
        raw = (self.base / "raw" / "policy_news.jsonl").read_bytes()
        copied = next((self.base / "lake" / "bronze" / "policy_news").rglob("*.jsonl")).read_bytes()
        self.assertEqual(raw, copied)

    def test_news_duplicates_and_missing_market_quarantined(self):
        checks = self.res["quality"]["policy_news"]["checks"]
        self.assertGreaterEqual(checks["duplicate item"], 1)
        self.assertEqual(checks["missing market"], 1)

    def test_gold_kpis_are_consistent(self):
        g = self.res["gold"]
        self.assertEqual(len(g["kpi_weekly"]), synth.WEEKS)
        self.assertEqual(sum(r["licensed_users"] for r in g["kpi_adoption_by_region"]), 240)
        for r in g["kpi_adoption_by_region"]:
            self.assertTrue(0 <= r["adoption_rate"] <= 1)
        self.assertEqual(len(g["fact_usage"]), self.res["quality"]["ai_usage_events"]["accepted"])
        self.assertAlmostEqual(sum(t["hours_saved"] for t in g["kpi_by_tool"]),
                               sum(w["hours_saved"] for w in g["kpi_weekly"]), delta=1.0)

    def test_regions_start_at_their_rollout_wave(self):
        users = {u["user_id"]: u for u in self.res["users"]}
        first = {}
        for e in self.res["usage"]:
            region = users[e["user_id"]]["region"]
            first[region] = min(first.get(region, 99), lake.week_of(e["event_date"]))
        self.assertEqual(first, synth.WAVES)

    def test_star_schema_keys_join(self):
        g = self.res["gold"]
        users = {u["user_id"] for u in g["dim_user"]}
        dates = {d["date_key"] for d in g["dim_date"]}
        tools = {t["tool"] for t in g["dim_tool"]}
        for f in g["fact_usage"]:
            self.assertIn(f["user_id"], users)
            self.assertIn(f["date_key"], dates)
            self.assertIn(f["tool"], tools)

    def test_catalog_names_an_owner_for_every_dataset(self):
        cat = json.loads((self.base / "lake" / "catalog.json").read_text())
        self.assertTrue(all(c["owner"] for c in cat))


class BusinessCaseTests(unittest.TestCase):
    def test_math_and_licence_models(self):
        weekly = [{"week": i, "hours_saved": 100.0, "cost_eur": 10.0} for i in range(1, 13)]
        bc = business_case.compute(weekly, active_last_4_weeks=120)
        a = business_case.ASSUMPTIONS
        base = bc["models"]["all_users"]["scenarios"]["base"]
        self.assertEqual(base["hours_per_year"], round(100 * 0.40 * 52))
        cost_all = a["licence_eur_per_user_month"] * 12 * 240 + a["build_and_run_eur_year"] + a["change_management_eur_year"] + 520
        self.assertEqual(bc["models"]["all_users"]["annual_cost_eur"], round(cost_all))
        self.assertLess(bc["models"]["active_users_only"]["annual_cost_eur"], bc["models"]["all_users"]["annual_cost_eur"])

    def test_scenarios_are_ordered(self):
        weekly = [{"week": i, "hours_saved": 80.0, "cost_eur": 5.0} for i in range(1, 13)]
        s = business_case.compute(weekly, 100)["scenarios"]
        self.assertLess(s["low"]["net_eur"], s["base"]["net_eur"])
        self.assertLess(s["base"]["net_eur"], s["high"]["net_eur"])


class ValueStreamTests(unittest.TestCase):
    def test_metrics(self):
        steps = [{"touch_h": 1, "wait_h": 3, "future": {"touch_h": 0.5, "wait_h": 0.5}}]
        self.assertEqual(value_stream.metrics(steps)["flow_efficiency"], 0.25)
        self.assertEqual(value_stream.metrics(steps, future=True)["lead_h"], 1.0)

    def test_future_is_better_for_both_streams(self):
        _, rows = value_stream.report(ROOT / "blueprint" / "value_streams.json")
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertLess(r["future"]["lead_h"], r["current"]["lead_h"])
            self.assertLess(r["future"]["touch_h"], r["current"]["touch_h"])
            self.assertTrue(r["bottleneck"])

    def test_mermaid_has_one_node_per_step(self):
        cfg = json.loads((ROOT / "blueprint" / "value_streams.json").read_text())
        s = cfg["streams"][0]
        self.assertEqual(value_stream.mermaid(s, False).count('["'), len(s["steps"]))


class DigestAndPortfolioTests(unittest.TestCase):
    def test_high_severity_goes_to_rapid_response(self):
        news = [
            {"id": "1", "published": "2026-11-25", "region": "Europe", "market": "France", "topic": "taxation",
             "severity": "high", "title": "t1", "text": "France announces a decree. More text.", "source": "s1"},
            {"id": "2", "published": "2026-11-24", "region": "Europe", "market": "Italy", "topic": "trade",
             "severity": "low", "title": "t2", "text": "Italy opens a consultation. More.", "source": "s2"},
            {"id": "3", "published": "2026-10-01", "region": "Europe", "market": "Poland", "topic": "trade",
             "severity": "high", "title": "old", "text": "Old item.", "source": "s3"},
        ]
        md, queue = policy_digest.digest(news, "2026-11-27")
        self.assertEqual([q["id"] for q in queue], ["1"])
        self.assertIn("[source](s1)", md)
        self.assertNotIn("old", md)
        self.assertIn("reviewed", md)

    def test_portfolio_flags_pilots_without_reviews(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.csv"
            p.write_text("use_case,stream,owner,stage,tools,value_hypothesis,risk_level,responsible_ai_review,"
                         "privacy_review,next_step\nA,x,o,pilot,t,v,low,to do,done,n\nB,x,o,idea,t,v,low,to do,to do,n\n",
                         encoding="utf-8")
            _, blocked = portfolio.summary(p)
            self.assertEqual([b["use_case"] for b in blocked], ["A"])

    def test_shipped_portfolio_has_no_blocked_pilot(self):
        _, blocked = portfolio.summary(ROOT / "governance" / "ai_portfolio.csv")
        self.assertEqual(blocked, [])


class CoworkSkillTests(unittest.TestCase):
    def test_every_skill_has_name_and_description(self):
        skills = sorted((ROOT / "copilot-cowork" / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 2)
        for f in skills:
            text = f.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f)
            front = text.split("---")[1]
            fields = dict(line.split(":", 1) for line in front.strip().splitlines())
            self.assertEqual(fields["name"].strip(), f.parent.name)
            self.assertTrue(fields["description"].strip())
            self.assertIn("approval", text.lower())


if __name__ == "__main__":
    unittest.main()
