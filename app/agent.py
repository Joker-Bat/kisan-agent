import os
from dotenv import load_dotenv

from google.adk.apps import App
from google.adk.workflow import Workflow, START

from app.core.constants import ROUTE_SYNTHESIS
from app.agents.orchestrator_agent import orchestrator
from app.agents.router_node import dynamic_router
from app.agents.synthesis_agent import prepare_synthesis, synthesizer

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Define the Graph Edges
edges = [
    ('START', orchestrator),
    (orchestrator, dynamic_router),
    
    # Route: synthesis
    (dynamic_router, {ROUTE_SYNTHESIS: prepare_synthesis}),
    (prepare_synthesis, synthesizer),
    
    # Route: direct_response is handled by default fall-through if no matching edge exists, 
    # ADK just outputs the event payload directly.
]

root_agent = Workflow(
    name="kisan_workflow",
    edges=edges,
    description="A multi-agent graph workflow for Indian farmers."
)

app = App(
    root_agent=root_agent,
    name="kisan-app"
)
