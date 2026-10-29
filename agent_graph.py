import os
import requests
import msal
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

# --- 1. PEARSON (Graph API) SETUP ---
TENANT_ID = os.getenv("PEARSON_TENANT_ID")
CLIENT_ID = os.getenv("PEARSON_CLIENT_ID")
CLIENT_SECRET = os.getenv("PEARSON_CLIENT_SECRET")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

# Authenticate once and get the token
app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
result = app.acquire_token_for_client(scopes=SCOPES)
GRAPH_TOKEN = result.get("access_token")

# --- 2. FOUNDRY (AI) SETUP ---
PROJECT_ENDPOINT = "https://aoai-audit-agent-v2.services.ai.azure.com/api/projects/proj-default"
MODEL_DEPLOYMENT = "audit-model"

project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()

# --- 3. DEFINE THE GRAPH API TOOL ---
def get_pearson_users():
    """Fetches the list of users from the Pearson tenant."""
    if not GRAPH_TOKEN:
        return "Error: Could not authenticate to Pearson."
    
    headers = {'Authorization': f'Bearer {GRAPH_TOKEN}'}
    response = requests.get('https://graph.microsoft.com/v1.0/users?$select=displayName,userPrincipalName&$top=10', headers=headers)
    
    if response.status_code == 200:
        users = response.json().get('value', [])
        # Format as a simple string for the AI
        user_list = "\n".join([f"- {u.get('displayName')} ({u.get('userPrincipalName')})" for u in users])
        return user_list
    else:
        return f"Error fetching users: {response.status_code}"

def get_global_admins():
    """Fetches members of the Global Administrator role."""
    if not GRAPH_TOKEN:
        return "Error: Could not authenticate."
    
    headers = {'Authorization': f'Bearer {GRAPH_TOKEN}'}
    
    # 1. Get the role ID for Global Administrator
    roles_url = "https://graph.microsoft.com/v1.0/directoryRoles?$filter=displayName eq 'Global Administrator'"
    role_res = requests.get(roles_url, headers=headers)
    
    if role_res.status_code != 200 or not role_res.json().get('value'):
        return "Could not find Global Administrator role."
    
    role_id = role_res.json()['value'][0]['id']
    
    # 2. Get the members of that role
    members_url = f"https://graph.microsoft.com/v1.0/directoryRoles/{role_id}/members"
    members_res = requests.get(members_url, headers=headers)
    
    if members_res.status_code == 200:
        admins = members_res.json().get('value', [])
        if not admins:
            return "No Global Admins found."
        return "\n".join([f"- {a.get('displayName')} ({a.get('userPrincipalName')})" for a in admins])
    else:
        return f"Error fetching admins: {members_res.status_code}"

def get_users_without_mfa():
    """Fetches users who do NOT have any authentication methods registered."""
    if not GRAPH_TOKEN:
        return "Error: Could not authenticate."
    
    headers = {'Authorization': f'Bearer {GRAPH_TOKEN}'}
    
    # Get users (we limit to 20 for speed, ignoring guests)
    users_url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,userPrincipalName&$top=20"
    users_res = requests.get(users_url, headers=headers)
    
    if users_res.status_code != 200:
        return f"Error fetching users: {users_res.status_code}"

    users = users_res.json().get('value', [])
    users_without_mfa = []

    for user in users:
        user_id = user['id']
        # Check if the user has any authentication methods registered
        auth_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/authentication/methods"
        auth_res = requests.get(auth_url, headers=headers)
        
        if auth_res.status_code == 200:
            methods = auth_res.json().get('value', [])
            # If the only method is a password, they don't have MFA
            # (If they have Microsoft Authenticator, FIDO2, etc., the list will be longer)
            if not methods or (len(methods) == 1 and methods[0].get('@odata.type') == '#microsoft.graph.passwordAuthenticationMethod'):
                users_without_mfa.append(f"- {user.get('displayName')} ({user.get('userPrincipalName')})")
    
    if not users_without_mfa:
        return "All checked users have MFA registered."
    
    return "\n".join(users_without_mfa)

def get_high_privilege_service_principals():
    """Finds Service Principals with dangerously high Graph API permissions."""
    if not GRAPH_TOKEN:
        return "Error: Could not authenticate."
    
    headers = {'Authorization': f'Bearer {GRAPH_TOKEN}'}
    
    # The specific role ID for RoleManagement.ReadWrite.Directory
    high_priv_role_id = "9e3f62cf-ca93-4989-b6ce-bf83c28f9fe8"
    
    # Query all appRoleAssignments for Microsoft Graph
    url = "https://graph.microsoft.com/v1.0/servicePrincipals(appId='00000003-0000-0000-c000-000000000000')/appRoleAssignedTo"
    res = requests.get(url, headers=headers)
    
    if res.status_code != 200:
        return f"Error checking assignments: {res.status_code}"
        
    assignments = res.json().get('value', [])
    
    vulnerable_sps = []
    for assignment in assignments:
        if assignment.get('appRoleId') == high_priv_role_id:
            sp_name = assignment.get('principalDisplayName')
            sp_id = assignment.get('principalId')
            vulnerable_sps.append(f"- {sp_name} (Object ID: {sp_id})")
            
    if not vulnerable_sps:
        return "No over-privileged service principals found."
        
    return "\n".join(vulnerable_sps)



# --- 4. DESCRIBE THE TOOL TO THE AI ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_pearson_users",
            "description": "Get a list of users from the Pearson Entra ID tenant",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_global_admins",
            "description": "Get a list of users who have the Global Administrator role",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_users_without_mfa",
            "description": "Get a list of users who do not have Multi-Factor Authentication (MFA) registered",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_high_privilege_service_principals",
            "description": "Find Service Principals that have excessive Microsoft Graph API permissions (like RoleManagement.ReadWrite.Directory), which can lead to privilege escalation.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# --- 5. THE AGENT LOOP ---
print("Agent is ready. Asking it to fetch users...")

messages = [
    {"role": "system", "content": "You are an automated Entra ID auditing agent. You MUST use your provided tools to answer questions. Do not give general advice or PowerShell scripts. If the user asks about Service Principals, you MUST call the get_high_privilege_service_principals tool to get the live list, and then analyze the results."},
    {"role": "user", "content": "Run the get_high_privilege_service_principals tool, focus specifically on EntraGoat-Vulnerable-SP, and explain the exact privilege escalation path an attacker could use."}
]

response = openai_client.chat.completions.create(
    model=MODEL_DEPLOYMENT,
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

response_message = response.choices[0].message
messages.append(response_message)

# Check if the AI wants to call the tool
if response_message.tool_calls:
    print("AI requested live tenant data. Executing Graph API call...")
    for tool_call in response_message.tool_calls:
        result = ""
        if tool_call.function.name == "get_pearson_users":
            result = get_pearson_users()
        elif tool_call.function.name == "get_global_admins":
            result = get_global_admins()
        elif tool_call.function.name == "get_users_without_mfa":
            result = get_users_without_mfa()
        elif tool_call.function.name == "get_high_privilege_service_principals":
            result = get_high_privilege_service_principals()
        else:
            result = "Unknown tool."

        # Send the live data back to the AI
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })
        
    # Get the AI's final analysis
    final_response = openai_client.chat.completions.create(
        model=MODEL_DEPLOYMENT,
        messages=messages
    )
    print("\nFinal AI Response:")
    print(final_response.choices[0].message.content)
else:
    print("AI answered directly without using the tool.")
    print(response_message.content)
