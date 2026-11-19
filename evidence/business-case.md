# Business case (synthetic pilot data)

Pilot run rate over the last 4 weeks: 109.9 self-reported hours saved per week, 156 active users out of 240.

## Assumptions

| Item | Value |
|---|---:|
| loaded cost eur per hour | 65 |
| licence eur per user month | 28 |
| users in scope | 240 |
| build and run eur year | 60,000 |
| change management eur year | 25,000 |

## Licences for every user in scope: 240 licences, annual cost EUR 168,269

| Scenario | Share of reported savings counted | Hours per year | Benefit | Net | ROI |
|---|---:|---:|---:|---:|---:|
| low | 25% | 1,429 | EUR 92,866 | EUR -75,404 | -45% |
| base | 40% | 2,286 | EUR 148,585 | EUR -19,684 | -12% |
| high | 55% | 3,143 | EUR 204,304 | EUR 36,035 | 21% |

## Licences for active users only: 156 licences, annual cost EUR 140,045

| Scenario | Share of reported savings counted | Hours per year | Benefit | Net | ROI |
|---|---:|---:|---:|---:|---:|
| low | 25% | 1,429 | EUR 92,866 | EUR -47,180 | -34% |
| base | 40% | 2,286 | EUR 148,585 | EUR 8,540 | 6% |
| high | 55% | 3,143 | EUR 204,304 | EUR 64,259 | 46% |

## Reading

With a licence for everyone, the base case returns -12%: licences for people who rarely use the tools cost more than the time saved. Licensing active users only moves the base case to 6%. The agents (Policy Digest, Rapid Response) save the most hours per euro, so scaling them before widening generic licences is the better order.

Decision rule proposed: scale a use case when the low scenario is at least break-even and quality ratings stay at 4/5 or above. Re-measure time saved with a sample of timed tasks, not self-reports only.
