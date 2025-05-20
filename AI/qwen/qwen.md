# SRE Incident Report Template

**Telecommunications Platform**

---

## **1. Incident Overview**

- **Incident ID**: [Unique identifier, e.g., INC-2023-001]
- **Title**: [Brief description, e.g., "Voice Service Outage in Region X"]
- **Date/Time**: [Start and end time in UTC]
- **Severity**: [Sev 1 (Critical) / Sev 2 (High) / Sev 3 (Medium) / Sev 4 (Low)]
- **Status**: [Investigating / Identified / Mitigated / Resolved / Closed]

---

## **2. Affected Services/Components**

- **Services**: [e.g., Voice Calls, SMS, Data Connectivity, VoLTE, 5G Core]
- **Regions/Networks**: [e.g., North America, LTE Network, Fiber Backbone]
- **Customers Impacted**: [Estimated number or percentage]

---

## **3. Incident Summary**

[Brief description of the incident, including symptoms and scope.]

> **Example**:
> Starting at 14:00 UTC, users in Region X reported failed voice calls and SMS delivery delays. The outage affected 15% of active subscribers, with a 40% drop in successful call setup rates.

---

## **4. Timeline**

| Time (UTC) | Event                                                                      |
| ---------- | -------------------------------------------------------------------------- |
| 14:00      | First user-reported issues via support portal.                             |
| 14:15      | SRE team detects elevated error rates in VoLTE signaling (SIP 503 errors). |
| 14:30      | Escalated to Network Operations Center (NOC).                              |
| 14:45      | Identified faulty core router (Router-7) causing packet loss.              |
| 15:10      | Router reboot initiated; services restored by 15:25.                       |

---

## **5. Impact Analysis**

- **Service Metrics**:
  - Voice call success rate: 60% ↓ (baseline: 99.9%)
  - SMS latency: 12s ↑ (baseline: 2s)
- **Customer Impact**:
  - 500,000 subscribers affected.
  - 2,500 support tickets generated.
- **Financial Impact**: [Estimate, if applicable]

---

## **6. Root Cause Analysis**

- **Primary Cause**: [Hardware failure / Software bug / Configuration error / External dependency / etc.]
  > **Example**:
  > Degraded firmware on Router-7 caused BGP session flapping, leading to routing instability in the core network.
- **Contributing Factors**:
  - Lack of redundancy for Router-7.
  - Delayed alerting for BGP session failures.

---

## **7. Corrective Actions**

- **Immediate Mitigation**:
  - Rebooted Router-7 and restored BGP sessions.
  - Redirected traffic via backup paths.
- **Long-Term Fixes**:
  - Replace Router-7 with redundant hardware by [date].
  - Implement automated failover for core routers.
  - Update monitoring to track BGP session health.

---

## **8. Communication Log**

| Audience       | Channel           | Message                                                     |
| -------------- | ----------------- | ----------------------------------------------------------- |
| Internal Teams | Slack #sre-alerts | "Voice service outage in Region X – investigating."         |
| Customers      | Status Page       | "Ongoing voice call issues – ETA to resolution: 15:30 UTC." |
| Executives     | Email             | Post-incident summary sent at 16:00 UTC.                    |

---

## **9. Post-Incident Tasks**

- **Action Items**:
  - [ ] Review router firmware update schedule (Owner: Network Team, Due: [date]).
  - [ ] Test failover automation in staging (Owner: SRE, Due: [date]).
- **Post-Mortem Meeting**: [Date/Time]

---

## **10. References**

- Monitoring Dashboards: [Link to Grafana/Splunk]
- Incident Logs: [Link to syslog/audit logs]
- Runbooks: [Link to relevant SRE documentation]

---

**Prepared by**: [Name/Team]
**Approved by**: [Manager/Lead]
**Date**: [YYYY-MM-DD]
