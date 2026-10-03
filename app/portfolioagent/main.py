from strands import Agent
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamable_http_client
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlencode
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
load_dotenv()
import os

REGION = os.getenv("AWS_REGION")
RUNTIME_ID = os.getenv("MCP_RUNTIME_ID")
ACCOUNT_ID =os.getenv("AWS_ACCOUNT_ID")

url = f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{RUNTIME_ID}/invocations?qualifier=DEFAULT&accountId={ACCOUNT_ID}"


mcp_client = MCPClient(
    lambda: aws_iam_streamablehttp_client(
        aws_service="bedrock-agentcore",
        aws_region=REGION,
        endpoint=url,
    )
)

app = BedrockAgentCoreApp()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.entrypoint
async def agent_invocation(payload):
    """Handler for agent invocation"""
   
    user_message = payload.get(
        "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    )
    
    history = payload.get("history","")
    
    with mcp_client:
        agent = Agent(tools=mcp_client.list_tools_sync(),
        system_prompt=f"""You are a portfolio assistant of Robert Meszaros, with access to portfolio tools.
        Give concise answer in markdown format highlighting important parts of the answer considering the history of the conversation.
        If a tool returns a json format, then return that json to the user!
        
        Chat history: {history}
        
        """)
        stream = agent.stream_async(user_message)
        async for event in stream:
            print(event)
            yield (event)

if __name__ == "__main__":
    app.run()