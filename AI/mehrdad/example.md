# Incident Template

## Incident Metadata

- **Incident ID:** UUID
- **Title:** Main incident title
- **Severity:** Sev-Levels
- **Date/Time Detected (UTC):** 2025‑05‑18 07:42
- **Detected By:** Prometheus Alert (SIP 5xx error rate)
- **Incident Commander:** Maria Schuster
- **Status**: [Open, Doing, Resolved]

## Summary

### Short Description

A configuration change on the EU Session Border Controller caused SIP 5xx errors, dropping ~10 % of all call setups between 07:42 and 08:50 UTC.

## Affects

### **Services Affected:**

- **SIP Proxy**
- **Media Gateway**
- **Call Detail Record (CDR) Ingestion**

### Regions/Networks Affected

Southeast Asia (Philippines, Indonesia), Fiber Backbone Route SEA-07

## Impacts

### Customer Impact

- 2.3 million subscribers affected for 3.5 hours.
- 120,000 IoT devices disconnected, impacting logistics partners.

### Business Impact

- Estimated $180,000 in lost revenue (based on SLA penalties).

## Root Cause Analysis (Preliminary)

### What Happened

A new SIP header‑rewrite rule was deployed without validating the custom “X-Operator-Route” header, causing proxy mismatches and 5xx responses.

### Why It Happened

1. Deployment skipped end‑to‑end SIP tests in the EU pre‑prod environment.
2. CI pipeline lacked automated SIP compliance checks.
3. The rollback procedure did not include traffic‑shift instructions.

### Technical Cause

Faulty query retry logic in v2.1.3 caused exponential load on Cassandra cluster.

### Detection Mechanism

- Automated Prometheus alert on “SIP 5xx error rate”
- Elevated customer support tickets in Germany and France

## Timeline of Events (Chronological Updates)

| Time (UTC) | Event                                             | Owner/Team      |
| ---------- | ------------------------------------------------- | --------------- |
| 07:42      | Prometheus alert: SIP 5xx error rate at 2 %       | Monitoring Team |
| 07:45      | Incident declared                                 | Maria Schuster  |
| 07:50      | Identified recent SBC config push at 07:30 UTC    | Networking SRE  |
| 07:56      | Rolled back SBC header‑rewrite rule               | Release Team    |
| 08:05      | Error rate still 8 % → shifted 30 % traffic to DR | Networking SRE  |
| 08:20      | Call success rate improves to 96.3 %              | On‑call SRE     |
| 08:35      | Full traffic shifted to standby cluster           | Networking SRE  |
| 08:50      | Metrics returned to baseline; incident resolved   | Maria Schuster  |
| 09:00      | Post‑incident monitoring started                  | Monitoring Team |

## Resolution & Mitigation

### Short‑Term Remediation (Mitigation Steps)

1. **Rollback:** Reverted SBC config to pre‑change version (v3.4.7).
2. **Traffic Shift:** Diverted 30 % of EU SIP traffic to DR proxy cluster.
3. **Alert Adjustment:** Raised threshold for CDR lag alerts to prevent noise.
4. **Restarted unhealthy** Cassandra nodes.

### Resolution Time (UTC)

2023-05-15 10:00

### Long‑Term Preventative Measures

- **Automated SIP Tests:** Add CI jobs validating header‑rewrite rules against live‑like SIP traffic.
- **Staging Expansion:** Mirror full SBC+Media Gateway topology for EU in staging.
- **Runbook Enhancements:**
  - Include explicit traffic‑shift steps.
  - Add quick‑verify tests post‑rollback.

## Communications Log

| Time (UTC) | Channel            | Message                                                           |
| ---------- | ------------------ | ----------------------------------------------------------------- |
| 07:47      | #sre-ops (Slack)   | “High SIP 5xx error rate detected in EU. Investigating.”          |
| 07:58      | Status Page (Web)  | “Partial voice service degradation in Europe. Working on fix.”    |
| 08:10      | #all-hands (Email) | “Incident update: rollback in progress; partial traffic shifted.” |
| 08:55      | Status Page (Web)  | “Full service restored. Monitoring continues.”                    |

## Sign‑Off

| **Role**             | **Approver**   | **Date**     |
| -------------------- | -------------- | ------------ |
| Incident Commander   | Maria Schuster |   2025‑05‑18 |
| SRE Manager          | Lars Becker    |   2025‑05‑19 |
| Telecom Ops Lead     | Antoine Dubois |   2025‑05‑19 |

---

---

## Post-Mortem (Completed)

### Metadata

- Incident number
- status

### Root Cause Analysis (RCA)

- A code change in v2.1.3 introduced unbounded retries for failed database queries under high latency.
- Cassandra nodes became overloaded, triggering cascading failures. Logs show CPU saturation at 95% for 30 minutes.

### Contributing Factors

- **Process Gap**: No canary deployment for database-critical changes.
- **Tooling Gap**: Cluster health alerts relied on disk/memory metrics, not query throughput.

### Lessons Learned

1. Canary deployments required for all database-impacting changes.
2. Improve alerting on query-per-second (QPS) thresholds.

### Action Items

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
