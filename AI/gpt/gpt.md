# SRE Incident Report Template

_Telecommunications Platform_

---

## Incident Metadata

- **Incident ID:** SRE‑TELCO‑\_\_\_\_
- **Title:** _(e.g. “Voice Call Drop Rate Spike in EU Region”)_
- **Severity:** Sev‑1 / Sev‑2 / Sev‑3
- **Date/Time Detected (UTC):** YYYY‑MM‑DD HH:MM
- **Detected By:** _(Monitoring Alert / Pager Duty / Customer Report)_
- **Incident Commander:** _(Name)_, **Runbook:** _(Link to playbook)_

---

## 1. Incident Summary

**Short Description:**

> _One‑sentence summary of what happened and impact._

**Services Affected:**

- **SIP Proxy**
- **Media Gateway**
- **SMS Gateway**

**Regions Affected:**

- Europe (DE, FR, UK)
- North America (US‑East)

---

## 2. Impact & Diagnostics

| Metric                    | Baseline | Observed | Threshold |
| ------------------------- | -------- | -------- | --------- |
| Call Setup Success Rate   | ≥ 99.9 % | 92.4 %   | ≤ 99.0 %  |
| Average Call Latency (ms) | 150 ms   | 450 ms   | ≥ 300 ms  |
| Packet Loss (%)           | ≤ 0.1 %  | 2.3 %    | ≥ 1.0 %   |
| SMS Delivery Rate (%)     | ≥ 99.5 % | 85.7 %   | ≤ 98.0 %  |

**Business Impact:**

- Number of failed calls: ~ 24 000 in first hour
- Estimated revenue loss: \$12 000/hr
- SLA breach window: 00:15 – 02:45 UTC

---

## 3. Timeline of Events

| Time (UTC)            | Event                                          | Owner/Team         |
| --------------------- | ---------------------------------------------- | ------------------ |
| `T₀` YYYY‑MM‑DD HH:MM | Alert: SIP error rate > 5 %                    | Monitoring Team    |
| `T₀+5m`               | Incident declared                              | Incident Commander |
| `T₀+10m`              | Initial triage: increased 502s at SBC proxy    | Networking SRE     |
| `T₀+20m`              | Scoped to EU region; rolled back latest config | Release Team       |
| `T₀+35m`              | Partial recovery; error rate down to 3 %       | On‑call SRE        |
| `T₀+50m`              | Full traffic shift to standby gateway cluster  | Networking SRE     |
| `T₀+60m`              | Services restored to normal levels             | Incident Commander |
| `T₀+75m`              | Post‑incident monitoring                       | Monitoring Team    |
| `T₀+90m`              | Incident resolved; begin post‑mortem prep      | Incident Lead      |

_(Add more rows as needed)_

---

## 4. Root Cause Analysis

- **What Happened:**
  A recent configuration change on the Session Border Controller (SBC) introduced an incorrect SIP header rewrite rule, causing upstream proxy errors and increased call setup failures.

- **Why It Happened:**

  1. Change deployed without end‑to‑end staging in a mirrored EU environment.
  2. No automated SIP compliance tests in CI pipeline.
  3. Insufficient rollback playbook for SBC configs.

- **Detection Mechanism:**
  - Automated alert on “SIP 5xx error rate” triggered by Prometheus → PagerDuty.
  - Customer support tickets spiked in EU region.

---

## 5. Resolution & Mitigation

### Short‑Term Remediation

1. Reverted SBC header‑rewrite rule to last known good config.
2. Shifted traffic to DR (disaster‑recovery) proxy cluster.
3. Throttled configuration push pipeline.

### Long‑Term Preventative Measures

- **Automate SIP Compliance Tests**
  Add CI job to validate SIP message headers against spec.
- **Improve Staging Coverage**
  Mirror production SBC and proxy topology in EU sandbox.
- **Enhance Runbooks**
  - Develop clear rollback steps for SBC changes.
  - Add traffic‑shift playbook for failover to DR.

---

## 6. Communications Log

| Time (UTC) | Channel              | Message                                                                     |
| ---------- | -------------------- | --------------------------------------------------------------------------- |
| `T₀+2m`    | #ops‑channel (Slack) | “Investigating elevated SIP 5xx errors in EU region.”                       |
| `T₀+15m`   | Customer Status Page | “Partial service degradation affecting call setup in Europe. Updates soon.” |
| `T₀+40m`   | #all‑hands (Email)   | “Major incident resolved. Full service restoration at HH:MM UTC.”           |

---

## 7. Post‑Incident Review & Action Items

| Owner           | Task                                                       | Due Date   | Status |
| --------------- | ---------------------------------------------------------- | ---------- | ------ |
| Networking SRE  | Add SIP‑header rewrite tests to CI pipeline                | YYYY‑MM‑DD | ☐ Open |
| QA Team         | Deploy EU‑sandbox replica for full end‑to‑end validation   | YYYY‑MM‑DD | ☐ Open |
| Incident Lead   | Update SBC rollback runbook                                | YYYY‑MM‑DD | ☐ Open |
| Monitoring Team | Tune alert thresholds for call‑setup errors (reduce noise) | YYYY‑MM‑DD | ☐ Open |

---

## 8. Sign‑Off

- **Incident Commander:** ****\*\*****\_\_****\*\***** Date: \***\*\_\_\*\***
- **SRE Manager:** ******\*\*******\_******\*\******* Date: \***\*\_\_\*\***
- **Telecom Ops Lead:** ****\*\*****\_\_\_\_****\*\***** Date: \***\*\_\_\*\***

---

> _Use this template to capture all critical details in real time. After resolution, convene a blameless post‑mortem to validate root cause, close action items, and refine SLOs & runbooks._
