import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("PEARSON_TENANT_ID")
CLIENT_ID = os.getenv("PEARSON_CLIENT_ID")
CLIENT_SECRET = os.getenv("PEARSON_CLIENT_SECRET")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

print("Authenticating with Pearson Tenant...")

# 1. Authenticate using MSAL
app = msal.ConfidentialClientApplication(
    CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
)
result = app.acquire_token_silent(SCOPES, account=None)

if not result:
    result = app.acquire_token_for_client(scopes=SCOPES)

if "access_token" in result:
    print("Authentication successful! Fetching users...")
    access_token = result['access_token']
    
    # 2. Call Microsoft Graph API
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Get top 5 users just to test
    response = requests.get('https://graph.microsoft.com/v1.0/users?$top=5', headers=headers)
    
    if response.status_code == 200:
        users = response.json().get('value', [])
        print(f"\nSuccessfully retrieved {len(users)} users:")
        for user in users:
            print(f"- {user.get('displayName')} ({user.get('userPrincipalName')})")
    else:
        print(f"Failed to fetch users: {response.status_code}")
        print(response.text)
else:
    print("Authentication failed.")
    print(result.get("error_description"))
