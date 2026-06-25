import os
from dotenv import load_dotenv

from google.adk.apps import App
from google.adk.workflow import Workflow, START, END

from app.core.constants import ROUTE_SYNTHESIS, ROUTE_DIRECT_RESPONSE
from app.agents.orchestrator_agent import orchestrator_node
from app.agents.synthesis_agent import synthesis_node
from app.agents.router_node import dynamic_router

# Removed Monkeypatch

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Define the Graph Edges
edges = [
    ('START', orchestrator_node),
    (orchestrator_node, dynamic_router),
    
    # Conditional routing from dynamic_router
    (dynamic_router, {
        ROUTE_SYNTHESIS: synthesis_node,
        ROUTE_DIRECT_RESPONSE: END,
        "__default__": END
    }),
]

from app.core.schemas import GraphState

root_agent = Workflow(
    name="kisan_workflow",
    edges=edges,
    description="A multi-agent graph workflow for Indian farmers.",
    state_schema=GraphState
)

app = App(
    root_agent=root_agent,
    name="app"
)
