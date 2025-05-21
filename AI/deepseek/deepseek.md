# SRE Incident Template - Telecommunications Platform

## Incident Overview

| **Field**                | **Details**                                                        |
| ------------------------ | ------------------------------------------------------------------ |
| **Incident Title**       | [Short, Descriptive Title (e.g., "Nationwide SMS Service Outage")] |
| **Incident ID**          | [Unique Identifier (e.g., INC-2023-001)]                           |
| **Status**               | [Active/Resolved/Mitigated]                                        |
| **Severity Level**       | [Sev0/Sev1/Sev2/Sev3]                                              |
| **Detection Time (UTC)** | [Timestamp when incident was detected]                             |
| **Reported By**          | [Name/Team/Channel (e.g., Monitoring Alert, Customer Support)]     |

---

## Incident Summary

**Description**:
[Brief summary of the incident, including symptoms and initial observations.]
**Affected Services**:

- [Voice Services]
- [SMS/MMS]
- [Mobile Data]
- [API Gateways]
- [Billing System]
- [Other critical components]

**Service Owners**:

- [Team/Person responsible for the affected service(s)]

**Severity Justification**:

- [Impact on customers, revenue, SLA breaches, or regulatory compliance.]

---

## Timeline (Chronological Updates)

| **Timestamp (UTC)** | **Update**                                                           | **Owner**       |
| ------------------- | -------------------------------------------------------------------- | --------------- |
| [2023-01-01 12:00]  | Incident detected via [alerting tool]. SMS failure rate exceeds 95%. | [Engineer Name] |
| [2023-01-01 12:05]  | On-call engineer begins investigation.                               | [Engineer Name] |
| [2023-01-01 12:15]  | Identified root cause: [Database cluster overload].                  | [Engineer Name] |
| [2023-01-01 12:30]  | Mitigation steps initiated: [Failover to redundant cluster].         | [Engineer Name] |
| [2023-01-01 13:00]  | Service restored. Monitoring recovery metrics.                       | [Engineer Name] |

---

## Impact Analysis

**Scope**:

- [Geographic regions affected (e.g., North America, APAC)]
- [% of customers impacted]
- [Specific user segments (e.g., prepaid/postpaid, enterprise clients)]

**Business Impact**:

- [Estimated revenue loss]
- [Customer complaints/tickets raised]
- [Regulatory/SLA penalties (if applicable)]

**Root Cause (Preliminary)**:

- [Technical cause (e.g., misconfiguration, code bug, network partition)]
- [Contributing factors (e.g., insufficient capacity planning)]

---

## Resolution

**Mitigation Steps**:

1. [Step 1: Restarted overloaded servers]
2. [Step 2: Rolled back faulty deployment]
3. [Step 3: Scaled horizontally to handle traffic]

**Resolution Time (UTC)**: [2023-01-01 13:00]
**Verified By**: [Engineer/Team Name]
**Verification Steps**:

- [Confirmed SMS delivery success rate back to 99.9%]
- [Checked monitoring dashboards (e.g., Grafana, Prometheus)]

---

## Post-Mortem (To Be Completed Post-Incident)

**Root Cause Analysis (RCA)**:

- [Detailed technical explanation with evidence (logs, metrics, traces).]

**Contributing Factors**:

- [Process gaps (e.g., missed load testing)]
- [Human error (e.g., misconfigured deployment)]

**Lessons Learned**:

- [Example: Improve auto-scaling thresholds for peak traffic.]

**Action Items**:
| **Task** | **Owner** | **Due Date** | **Status** |
|-----------------------------------|-----------------|--------------|------------|
| [Implement circuit breakers] | [Team Name] | [2023-02-01] | [Open] |
| [Update runbooks for SMS service] | [Engineer Name] | [2023-01-15] | [In Progress] |

---

## Supporting Information

- **Logs**: [Links to relevant logs (e.g., Kibana, CloudWatch)]
- **Metrics**: [Screenshots of dashboards showing anomaly]
- **Communication**: [Slack/Email threads with stakeholders]

---

## Incident Participants

- **Incident Commander**: [Name]
- **SRE Team**: [Names]
- **Customer Support Lead**: [Name]
- **Third-Party Vendor (if applicable)**: [Vendor Name/Contact]

---

**Approvals**
| **Role** | **Name** | **Date** |
|----------------------|----------|----------------|
| Incident Lead | [Name] | [2023-01-02] |
| Engineering Manager | [Name] | [2023-01-02] |
