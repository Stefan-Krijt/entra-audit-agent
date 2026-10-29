(.venv) lokiyn@fedora:~/Documents/entra-audit-agent$ python agent_graph.py
Agent is ready. Asking it to fetch users...
AI requested live tenant data. Executing Graph API call...

Final AI Response:
Here’s the current set of high‑privilege service principals detected in your Entra ID tenant:

1. **ProvisioningHealthPME**  
   - **Object ID:** `092896a7-0461-46eb-8870-29ee80880700`  
   - Flagged as: High‑privilege service principal (likely related to provisioning/monitoring functions).

2. **managedenvironments-ar-tenant-connector-ame**  
   - **Object ID:** `9c31b56e-7e56-45f9-8274-336725d26bc9`  
   - Flagged as: High‑privilege service principal (appears to be associated with managed environments / AR tenant connectivity).

3. **EntraGoat-Vulnerable-SP**  
   - **Object ID:** `0b97b491-8c85-436a-9bf5-4698033fb1ea`  
   - Flagged as: High‑privilege service principal explicitly labeled as vulnerable.

If you want, I can next focus on one of these (for example, **EntraGoat-Vulnerable-SP**) and walk through what its elevated access likely implies and what to review in its configuration and assignments.
(.venv) lokiyn@fedora:~/Documents/entra-audit-agent$ nano agent_graph.py
(.venv) lokiyn@fedora:~/Documents/entra-audit-agent$ python agent_graph.py
Agent is ready. Asking it to fetch users...
AI requested live tenant data. Executing Graph API call...

Final AI Response:
Here’s the escalation path, step by step, specifically for **EntraGoat‑Vulnerable‑SP**, based on its presence in the **high‑privilege service principals** list:

> Assumption from the tool:  
> Being flagged as *high‑privilege* indicates this SP has one or more powerful roles/permissions (e.g., Directory/Role/Group admin‑level access) that are misconfigured in a way that allows privilege escalation to tenant‑wide admin.

I’ll walk through the standard escalation chain this kind of vulnerable SP typically enables.

---

## 1. Attacker gains control of EntraGoat‑Vulnerable‑SP

The attacker first obtains usable credentials or a token for **EntraGoat‑Vulnerable‑SP** by any of these routes:

- Compromised client secret, certificate, or MSI (managed identity)
- Exploited application vulnerability where this SP is used as the app identity
- Misconfigured deployment pipeline that exposes the SP credentials

Once they can successfully acquire a token as this SP (e.g., Microsoft Graph or ARM token), they effectively “are” EntraGoat‑Vulnerable‑SP inside the tenant.

---

## 2. Existing high‑impact permissions on the SP

Since the SP appears in the **high‑privilege list**, it has one or more of the following *effective* capabilities (typical for this scenario):

- **Directory write / management permissions**, such as:
  - `Directory.AccessAsUser.All`
  - `Directory.ReadWrite.All`
  - `Application.ReadWrite.All`
  - `Group.ReadWrite.All`
- Or it is **assigned a privileged Entra role**, such as:
  - `Cloud Application Administrator`
  - `Application Administrator`
  - `Privileged Role Administrator`
  - `Global Administrator` (less common but immediately terminal)

These permissions allow the SP to manage **applications, service principals, roles, and/or groups**—crucial building blocks for escalation.

---

## 3. Escalation via application/service principal management

A very common path for a “vulnerable” high‑priv SP is:

1. **Create or modify another application** in Entra ID:
   - Using `Application.ReadWrite.All` or app‑admin role, the attacker (as EntraGoat‑Vulnerable‑SP) can:
     - Register a new malicious application
     - Or modify an existing application/service principal the tenant trusts

2. **Add powerful permissions to the malicious app**:
   - Assign **graph permissions** such as:
     - `Directory.ReadWrite.All`
     - `RoleManagement.ReadWrite.Directory`
     - `User.ReadWrite.All`
   - Or equivalent resource permissions on other APIs (e.g. Azure Resource Manager) that allow RBAC changes.

3. **Grant admin consent to those permissions**:
   - If EntraGoat‑Vulnerable‑SP has sufficient directory privileges (or is itself in an admin role that can consent), it can:
     - Grant tenant‑wide admin consent for these delegated or application permissions.
   - This makes the malicious app a **tenant‑wide backdoor** with broad directory access.

4. **Use the malicious app to perform high‑impact changes**:
   - With those newly consented permissions, the attacker can:
     - Create a new service principal and assign themselves elevated roles.
     - Modify existing admin accounts (password, MFA, UPN, etc.).
     - Add themselves to high‑privileged Entra ID roles via Graph role management APIs.

This path takes the attacker from “compromise of one SP” → “owning the whole directory”.

---

## 4. Escalation via role or group assignment (RBAC path)

If **EntraGoat‑Vulnerable‑SP** has **role or group management capabilities**, there’s another direct route:

1. **Role/Directory management**:
   - With `RoleManagement.ReadWrite.Directory` or a role like `Privileged Role Administrator`, the SP can:
     - Assign privileged directory roles (e.g., Global Administrator, Security Administrator) to arbitrary principals the attacker controls.

2. **Group‑based privilege escalation**:
   - If high‑priv roles are assigned to certain groups (common for Azure RBAC or PIM scenarios), and EntraGoat‑Vulnerable‑SP can:
     - `Group.ReadWrite.All`  
     it can:
     - Add the attacker’s account/service principal into those high‑priv groups.
   - The attacker then inherits all role assignments those groups hold (e.g., subscription Owner, Global Admin, etc.).

This is often “quieter” than app‑permission escalation and is typical for EntraGoat‑style vulnerable configurations.

---

## 5. Final stage: Full tenant compromise

Once the attacker has used EntraGoat‑Vulnerable‑SP to:

- Grant admin consent to malicious applications **and/or**
- Assign **high‑privilege Entra roles** or **high‑priv groups** to identities they control,

they achieve:

- Ability to create, delete, or change user accounts, including admins
- Ability to manage conditional access and MFA (disabling or weakening protections)
- Control over applications, service principals, secrets/certs, and possibly subscriptions (if Azure RBAC is in play)
- Long‑term persistence via:
  - Additional high‑priv SPs
  - Hidden app registrations
  - Backdoor role/group assignments

---

## Concise privilege escalation chain (attacker’s viewpoint)

1. **Obtain access** to EntraGoat‑Vulnerable‑SP credentials.
2. Use its **high‑priv directory/app/role permissions**.
3. **Register or modify** an application/service principal.
4. **Grant admin consent** to powerful Graph/ARM permissions for that app.
5. Or **add attacker‑controlled identities** to high‑privileged roles/groups.
6. Use those elevated identities to become **Global Admin / equivalent**, fully compromising the tenant.

If you want, I can next enumerate the exact role/permission combinations that most commonly make SPs like EntraGoat‑Vulnerable‑SP exploitable, based on what this auditing tool treats as “high privilege.”
