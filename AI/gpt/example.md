# SRE Incident Report

_Telecommunications Platform_

---

## Incident Metadata

- **Incident ID:** SRE‑TELCO‑0012
- **Title:** Voice Call Setup Failures in EU Region
- **Severity:** Sev‑1
- **Date/Time Detected (UTC):** 2025‑05‑18 07:42
- **Detected By:** Prometheus Alert (SIP 5xx error rate)
- **Incident Commander:** Maria Schuster, **Runbook:** https://confluence.example.com/sre/runbooks/sbc-failover

---

## 1. Incident Summary

**Short Description:**

> A configuration change on the EU Session Border Controller caused SIP 5xx errors, dropping ~10 % of all call setups between 07:42 and 08:50 UTC.

**Services Affected:**

- **SIP Proxy**
- **Media Gateway**
- **Call Detail Record (CDR) Ingestion**

**Regions Affected:**

- Europe (DE, FR, UK)

---

## 2. Impact & Diagnostics

| Metric                    | Baseline | Observed | Threshold |
| ------------------------- | -------- | -------- | --------- |
| Call Setup Success Rate   | ≥ 99.9 % | 89.7 %   | ≤ 99.0 %  |
| Average Call Latency (ms) | 150 ms   | 360 ms   | ≥ 300 ms  |
| SIP 5xx Error Rate (%)    | ≤ 0.1 %  | 12.4 %   | ≥ 1.0 %   |
| CDR Ingestion Lag (min)   | ≤ 1 min  | 5 min    | ≥ 2 min   |

**Business Impact:**

- **Failed Call Attempts:** ~ 46 000 calls
- **Estimated Revenue Loss:** \$18 400/hr
- **SLA Breach Window:** 07:42 – 08:50 UTC

---

## 3. Timeline of Events

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

---

## 4. Root Cause Analysis

- **What Happened:**
  A new SIP header‑rewrite rule was deployed without validating the custom “X-Operator-Route” header, causing proxy mismatches and 5xx responses.

- **Why It Happened:**

  1. Deployment skipped end‑to‑end SIP tests in the EU pre‑prod environment.
  2. CI pipeline lacked automated SIP compliance checks.
  3. The rollback procedure did not include traffic‑shift instructions.

- **Detection Mechanism:**
  - Automated Prometheus alert on “SIP 5xx error rate”
  - Elevated customer support tickets in Germany and France

---

## 5. Resolution & Mitigation

### Short‑Term Remediation

1. **Rollback:** Reverted SBC config to pre‑change version (v3.4.7).
2. **Traffic Shift:** Diverted 30 % of EU SIP traffic to DR proxy cluster.
3. **Alert Adjustment:** Raised threshold for CDR lag alerts to prevent noise.

### Long‑Term Preventative Measures

- **Automated SIP Tests:** Add CI jobs validating header‑rewrite rules against live‑like SIP traffic.
- **Staging Expansion:** Mirror full SBC+Media Gateway topology for EU in staging.
- **Runbook Enhancements:**
  - Include explicit traffic‑shift steps.
  - Add quick‑verify tests post‑rollback.

---

## 6. Communications Log

| Time (UTC) | Channel            | Message                                                           |
| ---------- | ------------------ | ----------------------------------------------------------------- |
| 07:47      | #sre-ops (Slack)   | “High SIP 5xx error rate detected in EU. Investigating.”          |
| 07:58      | Status Page (Web)  | “Partial voice service degradation in Europe. Working on fix.”    |
| 08:10      | #all-hands (Email) | “Incident update: rollback in progress; partial traffic shifted.” |
| 08:55      | Status Page (Web)  | “Full service restored. Monitoring continues.”                    |

---

## 7. Post‑Incident Review & Action Items

| Owner           | Task                                                        | Due Date   | Status |
| --------------- | ----------------------------------------------------------- | ---------- | ------ |
| Networking SRE  | Implement SIP header‑rewrite compliance tests in CI         | 2025‑05‑25 | ☐ Open |
| QA Team         | Deploy full EU SBC+Gateway topology in staging              | 2025‑06‑01 | ☐ Open |
| Documentation   | Update SBC rollback runbook with traffic‑shift procedure    | 2025‑05‑22 | ☐ Open |
| Monitoring Team | Create synthetic SIP call simulation to catch header errors | 2025‑05‑27 | ☐ Open |

---

## 8. Sign‑Off

- **Incident Commander:** Maria Schuster  **Date:** 2025‑05‑18
- **SRE Manager:** Lars Becker  **Date:** 2025‑05‑19
- **Telecom Ops Lead:** Antoine Dubois  **Date:** 2025‑05‑19

---

> _This report captures all critical details of the EU voice‑service incident on 2025‑05‑18. Please schedule a blameless post‑mortem review by 2025‑05‑21._
