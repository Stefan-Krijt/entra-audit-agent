import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

PROJECT_ENDPOINT = "https://aoai-audit-agent-v2.services.ai.azure.com/api/projects/proj-default"
MODEL_DEPLOYMENT = "audit-model"

print("Authenticating and connecting to Foundry...")
project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()

# 1. Define the local Python function
def get_current_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 2. Describe the tool to the AI
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

print("Asking the AI for the time...")
messages = [{"role": "user", "content": "What time is it right now?"}]

# 3. Send the prompt with tools included
response = openai_client.chat.completions.create(
    model=MODEL_DEPLOYMENT,
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

response_message = response.choices[0].message
messages.append(response_message)

# 4. Check if the AI decided to call the tool
if response_message.tool_calls:
    print("AI requested a tool call!")
    for tool_call in response_message.tool_calls:
        if tool_call.function.name == "get_current_time":
            # Execute the Python function
            result = get_current_time()
            print(f"Executed local tool. Result: {result}")
            
            # Send the result back to the AI
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
            
    # Get the final answer
    final_response = openai_client.chat.completions.create(
        model=MODEL_DEPLOYMENT,
        messages=messages
    )
    print("\nFinal AI Response:")
    print(final_response.choices[0].message.content)
else:
    print("AI answered directly without a tool:")
    print(response_message.content)
