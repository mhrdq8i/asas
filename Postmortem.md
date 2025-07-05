# Post-Mortem (Completed)

## Metadata

- **Incident number**
- **Status**
- **Document link**

## Root Cause Analysis (Deep RCA)

Completed part of the **Shallow RCA**

- A code change in v2.1.3 introduced unbounded retries for failed database queries under high latency.
- Cassandra nodes became overloaded, triggering cascading failures. Logs show CPU saturation at 95% for 30 minutes.

### Long‑Term Preventative Measures

- **Automated SIP Tests:** Add CI jobs validating header‑rewrite rules against live‑like SIP traffic.
- **Staging Expansion:** Mirror full SBC+Media Gateway topology for EU in staging.
- **Runbook Enhancements:**
  - Include explicit traffic‑shift steps.
  - Add quick‑verify tests post‑rollback.

## Contributing Factors

- **Process Gap**: No canary deployment for database-critical changes.
- **Tooling Gap**: Cluster health alerts relied on disk/memory metrics, not query throughput.

## Lessons Learned

1. Canary deployments required for all database-impacting changes.
2. Improve alerting on query-per-second (QPS) thresholds.

## Action Items

Completed part of the **_Long‑Term Preventative Measures_**

| **Task**                             | **Owner**       | **Due Date** | **Status**  |
| ------------------------------------ | --------------- | ------------ | ----------- |
| Implement canary deployment pipeline | CI/CD Team      | 2023-06-01   | In Progress |
| Update Cassandra alerts for QPS      | Monitoring Team | 2023-05-25   | Completed   |
| Add load-testing for retry logic     | Messaging Team  | 2023-06-15   | Open        |

## Approvals

| **Role**            | **Name**      | **Date**   |
| ------------------- | ------------- | ---------- |
| Incident Lead       | Alex Lee      | 2023-05-16 |
| Engineering Manager | Sarah Johnson | 2023-05-16 |
