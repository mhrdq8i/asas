# SRE Incident Report

**Telecommunications Platform**

---

## **1. Incident Overview**

- **Incident ID**: INC-2023-045
- **Title**: Fiber Cut Impacting Mobile Data and VoLTE in Southeast Asia
- **Date/Time**: 2023-10-23 (09:15 UTC) to 2023-10-23 (12:45 UTC)
- **Severity**: Sev 1 (Critical)
- **Status**: Resolved

---

## **2. Affected Services/Components**

- **Services**: Mobile Data (4G/5G), VoLTE, IoT Connectivity
- **Regions/Networks**: Southeast Asia (Philippines, Indonesia), Fiber Backbone Route SEA-07
- **Customers Impacted**: ~2.3 million subscribers

---

## **3. Incident Summary**

A fiber optic cable cut near Manila, Philippines, caused a complete outage of mobile data and VoLTE services for users in Southeast Asia. Subscribers reported dropped calls, inability to send SMS, and degraded IoT device connectivity (e.g., smart meters, logistics trackers).

> **Key Symptoms**:
>
> - 70% drop in mobile data throughput.
> - VoLTE call setup failures exceeding 85%.
> - IoT device disconnects at a rate of 12,000/hour.

---

## **4. Timeline**

| Time (UTC) | Event                                                            |
| ---------- | ---------------------------------------------------------------- |
| 09:15      | Users report service degradation via SMS and social media.       |
| 09:30      | SRE detects loss of BGP routes for SEA-07 fiber backbone.        |
| 09:45      | NOC confirms physical fiber cut due to third-party construction. |
| 10:00      | Traffic rerouted to backup fiber route SEA-08 (50% capacity).    |
| 11:30      | Repair team dispatched to splice fiber.                          |
| 12:45      | Fiber restored, services normalized by 13:00.                    |

---

## **5. Impact Analysis**

- **Service Metrics**:
  - Mobile data throughput: 30% of baseline (from 1.2 Tbps to 360 Gbps).
  - VoLTE success rate: 15% (baseline: 99.5%).
- **Customer Impact**:
  - 2.3 million subscribers affected for 3.5 hours.
  - 120,000 IoT devices disconnected, impacting logistics partners.
- **Financial Impact**: Estimated $180,000 in lost revenue (based on SLA penalties).

---

## **6. Root Cause Analysis**

- **Primary Cause**: Third-party construction crew severed SEA-07 fiber cable near Manila.
- **Contributing Factors**:
  - Lack of redundant fiber routes for SEA-07 (single point of failure).
  - Delayed detection of BGP route loss due to misconfigured alerts.

---

## **7. Corrective Actions**

- **Immediate Mitigation**:
  - Rerouted traffic to SEA-08 fiber backbone.
  - Activated satellite backup for critical IoT services.
- **Long-Term Fixes**:
  - Deploy redundant fiber route SEA-09 by Q1 2024.
  - Revise BGP monitoring to trigger alerts within 5 minutes of route loss.
  - Partner with local authorities to mark fiber routes in construction zones.

---

## **8. Communication Log**

| Audience       | Channel               | Message                                                                                                 |
| -------------- | --------------------- | ------------------------------------------------------------------------------------------------------- |
| Internal Teams | Slack #network-alerts | "SEA-07 fiber cut – 2.3M subs impacted. Rerouting traffic now."                                         |
| Customers      | SMS/Status Page       | "Network outage in Southeast Asia – engineers working on restoration. Updates every 30 mins."           |
| Executives     | Email                 | "Incident report: 3.5-hour outage due to fiber cut. Financial impact: $180K. Mitigation plan approved." |

---

## **9. Post-Incident Tasks**

- **Action Items**:
  - [ ] Finalize SEA-09 fiber deployment (Owner: Network Eng, Due: 2024-03-01).
  - [ ] Conduct BGP failover drill (Owner: SRE, Due: 2023-11-15).
- **Post-Mortem Meeting**: 2023-10-25 @ 14:00 UTC

---

## **10. References**

- Monitoring Dashboards: [Fiber Route Health (SEA-07)](https://grafana.example.com/d/sea07)
- Incident Logs: [Syslog entries for BGP route loss](https://splunk.example.com/app/search/search?q=SEA-07)
- Runbooks: [Fiber Cut Response Guide](https://wiki.example.com/sre/fiber-cut)

---

**Prepared by**: SRE Team Lead
**Approved by**: VP of Network Operations
**Date**: 2023-10-24

---

This example reflects a **telecom-specific incident** with realistic metrics (e.g., fiber routes, BGP, VoLTE) and operational workflows. Adjust details to match your platform’s architecture!
