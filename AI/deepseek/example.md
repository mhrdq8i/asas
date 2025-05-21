# SRE Incident Template - Telecommunications Platform

## Incident Overview

| **Field**                | **Details**                                                 |
| ------------------------ | ----------------------------------------------------------- |
| **Incident Title**       | Nationwide SMS Service Outage                               |
| **Incident ID**          | INC-2023-045                                                |
| **Status**               | Resolved                                                    |
| **Severity Level**       | Sev1                                                        |
| **Detection Time (UTC)** | 2023-05-15 08:30                                            |
| **Reported By**          | Monitoring Alert (Prometheus) / Customer Support Escalation |

---

## Incident Summary

**Description**:

SMS delivery failure rates spiked to 98% across all regions, causing widespread customer outages. Initial investigation revealed API timeouts between the SMS gateway and the core messaging database.

**Affected Services**:

- SMS/MMS Gateway
- Core Messaging Database (Cassandra Cluster)
- Customer Notification API

**Service Owners**:

- Messaging Team (SRE Lead: Jane Doe)
- Database Operations Team (Owner: John Smith)

**Severity Justification**:

- **Customer Impact**: 12 million users unable to send/receive SMS.
- **Revenue Impact**: Estimated loss of $250K/hour due to SLA penalties.
- **Regulatory Risk**: Violation of FCC uptime requirements for emergency SMS services.

---

## Timeline (Chronological Updates)

| **Timestamp (UTC)** | **Update**                                                                                              | **Owner**      |
| ------------------- | ------------------------------------------------------------------------------------------------------- | -------------- |
| 2023-05-15 08:30    | Alert triggered: SMS gateway API latency > 10s (Prometheus).                                            | Monitoring Bot |
| 2023-05-15 08:35    | On-call SRE (Alex Lee) declares Sev1 incident.                                                          | Alex Lee       |
| 2023-05-15 08:40    | Identified Cassandra cluster node failures in US-East-1 (3/6 nodes down).                               | John Smith     |
| 2023-05-15 08:50    | Failover initiated to US-West-2 replica cluster.                                                        | John Smith     |
| 2023-05-15 09:15    | Partial recovery (60% success rate). Latency still elevated.                                            | Jane Doe       |
| 2023-05-15 09:30    | Root cause confirmed: Code deployment introduced a bug in query retry logic, overwhelming the database. | Alex Lee       |
| 2023-05-15 09:45    | Rolled back faulty deployment (v2.1.3 → v2.1.2).                                                        | Jane Doe       |
| 2023-05-15 10:00    | Full service restoration confirmed.                                                                     | Alex Lee       |

---

## Impact Analysis

**Scope**:

- **Regions**: US, Canada, Mexico
- **Customers Impacted**: 100% of SMS users (12M+) for 1.5 hours.
- **Segments**: All prepaid/postpaid and enterprise clients.

**Business Impact**:

- **Revenue Loss**: ~$375K (1.5 hours × $250K/hour).
- **Customer Tickets**: 45,000+ complaints via support channels.
- **SLA Penalties**: 3 enterprise clients triggered penalty clauses.

**Root Cause (Preliminary)**:

- **Technical Cause**: Faulty query retry logic in v2.1.3 caused exponential load on Cassandra cluster.
- **Contributing Factors**:
  - Insufficient load testing for the new retry logic.
  - Delayed cluster health alerts (30-minute delay).

---

## Resolution

**Mitigation Steps**:

1. Rolled back deployment to v2.1.2.
2. Restarted unhealthy Cassandra nodes.
3. Disabled aggressive retries via hotfix.

**Resolution Time (UTC)**: 2023-05-15 10:00
**Verified By**: Jane Doe (Messaging Team Lead)
**Verification Steps**:

- Confirmed SMS success rate at 99.95% via Grafana dashboard.
- Validated end-to-end delivery via test scripts in Staging.

---

## Post-Mortem (Completed)

**Root Cause Analysis (RCA)**:

- A code change in v2.1.3 introduced unbounded retries for failed database queries under high latency.
- Cassandra nodes became overloaded, triggering cascading failures. Logs show CPU saturation at 95% for 30 minutes.

**Contributing Factors**:

- **Process Gap**: No canary deployment for database-critical changes.
- **Tooling Gap**: Cluster health alerts relied on disk/memory metrics, not query throughput.

**Lessons Learned**:

1. Canary deployments required for all database-impacting changes.
2. Improve alerting on query-per-second (QPS) thresholds.

**Action Items**:

| **Task**                             | **Owner**       | **Due Date** | **Status**  |
| ------------------------------------ | --------------- | ------------ | ----------- |
| Implement canary deployment pipeline | CI/CD Team      | 2023-06-01   | In Progress |
| Update Cassandra alerts for QPS      | Monitoring Team | 2023-05-25   | Completed   |
| Add load-testing for retry logic     | Messaging Team  | 2023-06-15   | Open        |

---

## Supporting Information

- **Logs**: [Cassandra Node Logs (US-East-1)](https://internal-logs/INC-2023-045)
- **Metrics**: ![Grafana Dashboard](https://internal-dashboards/grafana/sms-latency-inc-045)
- **Communication**: [Slack Thread](https://internal-slack/inc-045-comms)

---

## Incident Participants

- **Incident Commander**: Alex Lee
- **SRE Team**: Jane Doe, John Smith
- **Customer Support Lead**: Maria Garcia
- **Third-Party Vendor**: AWS Support (Case ID: 789456)

---

### **Approvals**

| **Role**            | **Name**      | **Date**   |
| ------------------- | ------------- | ---------- |
| Incident Lead       | Alex Lee      | 2023-05-16 |
| Engineering Manager | Sarah Johnson | 2023-05-16 |
