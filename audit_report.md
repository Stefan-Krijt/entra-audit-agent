# Microsoft Entra ID Security Audit Report

**Tool:** Custom AI Security Auditor Agent
**Target Environment:** Pearson Lab Tenant
**Execution Date:** 2026-10-29

## Executive Summary
The AI agent was tasked with scanning the target Entra ID tenant for high-privilege Service Principals and identifying potential privilege escalation paths. The live scan successfully identified three high-privilege service principals, including a deliberately vulnerable SP (`EntraGoat-Vulnerable-SP`). The AI generated a detailed analysis of the exploitation chain an adversary could use to gain Global Administrator access.

## Scan Results: High-Privilege Service Principals
The following Service Principals were flagged by the agent's Graph API tool:

1. **ProvisioningHealthPME**  
   - **Object ID:** `092896a7-0461-46eb-8870-29ee80880700`  
   - **Assessment:** Likely related to Microsoft provisioning/monitoring functions. Requires validation to ensure least privilege.

2. **managedenvironments-ar-tenant-connector-ame**  
   - **Object ID:** `9c31b56e-7e56-45f9-8274-336725d26bc9`  
   - **Assessment:** Associated with managed environments/tenant connectivity. High privilege requires monitoring.

3. **EntraGoat-Vulnerable-SP**  
   - **Object ID:** `0b97b491-8c85-436a-9bf5-4698033fb1ea`  
   - **Assessment:** Flagged as highly vulnerable. Contains excessive Microsoft Graph API permissions (`RoleManagement.ReadWrite.Directory`).

---

## Threat Analysis: Privilege Escalation Path
The agent was instructed to analyze `EntraGoat-Vulnerable-SP`. Below is the generated escalation path an attacker could use if this Service Principal's credentials were compromised.

### 1. Initial Access & Token Acquisition
An attacker obtains usable credentials for `EntraGoat-Vulnerable-SP` (e.g., via a compromised client secret, exposed certificate, or misconfigured CI/CD pipeline). Using these, the attacker requests an OAuth2 token and assumes the identity of the SP.

### 2. Abuse of High-Impact Permissions
The SP possesses dangerous Graph permissions, notably:
- `RoleManagement.ReadWrite.Directory`
- `Directory.ReadWrite.All`
- `Application.ReadWrite.All`

### 3. Application Modification & Consent
Using these permissions, the attacker can:
1. Register a new, malicious application.
2. Add high-privilege permissions (like Global Admin role management) to the new app.
3. Grant tenant-wide admin consent to the malicious app (since the compromised SP has the rights to do so).

### 4. Full Tenant Compromise
With the newly consented permissions, the attacker can assign the Global Administrator role to their own identity, modify existing admin accounts, disable Conditional Access policies, and establish long-term persistence via backdoor service principals.

## Remediation Recommendations
1. **Revoke Excessive Permissions:** The `RoleManagement.ReadWrite.Directory` permission should immediately be removed from `EntraGoat-Vulnerable-SP`.
2. **Audit Service Principal Ownership:** Ensure that all high-privilege service principals have active, monitored owners.
3. **Implement Workload Identities Protection:** Monitor for anomalous token acquisition or role assignments initiated by service principals.
4. **Least Privilege:** Ensure no automation SP has more permissions than it strictly needs to operate.
