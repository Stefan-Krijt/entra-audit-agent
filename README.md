# Entra ID AI Security Auditor Agent

## Overview
This project bridges an Azure OpenAI (Foundry) instance in the Cybersteps tenant with a live Entra ID lab tenant (Pearson). It uses Python, the Microsoft Graph API, and AI tool-calling to audit identity configurations and detect privilege escalation risks.

## Architecture
- **Cybersteps Tenant**: Hosts the Microsoft Foundry project and `gpt-4o` model.
- **Pearson Tenant**: Hosts the App Registration (`AI-Audit-Agent`) with `Directory.Read.All`, `User.Read.All`, and `AuditLog.Read.All` permissions.
- **Local Machine**: Runs `agent_graph.py`, authenticating to both environments and orchestrating the tool-calling loop.

## Files
- `agent_graph.py`: The main AI agent and Graph API tool definitions.
- `.env`: Contains the Pearson Tenant ID, Client ID, and Client Secret (excluded from version control).
- `get_users.py`: A standalone script used for initial Graph API testing.

## Setup Instructions
1. Ensure Python 3.x is installed.
2. Run `pip install msal requests python-dotenv azure-identity azure-ai-projects`.
3. Authenticate via Azure CLI: `az login`.
4. Configure the `.env` file with Pearson App Registration credentials.
5. Run `python agent_graph.py`.

## Implemented Audit Tools
- `get_pearson_users()`: Fetches live users.
- `get_global_admins()`: Identifies permanent Global Administrators.
- `get_users_without_mfa()`: Checks MFA registration status.
- `get_high_privilege_service_principals()`: Scans App Registrations for `RoleManagement.ReadWrite.Directory`.
