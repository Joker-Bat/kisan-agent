import os
from dotenv import load_dotenv

from google.adk.apps import App
from google.adk.workflow import Workflow, START, JoinNode

from app.agents.orchestrator_agent import orchestrator_node
from app.agents.synthesis_agent import synthesis_node
from app.agents.router_node import dynamic_router
from app.agents.direct_response_node import direct_response_node
from app.agents.weather_agent import weather_node
from app.agents.market_agent import market_node
from app.agents.crop_agent import crop_node
from app.agents.crop_agent import crop_node
from app.agents.scheme_agent import scheme_node
from app.core.constants import NODE_WEATHER, NODE_MARKET, NODE_CROP, NODE_SCHEME

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

join_node = JoinNode(name="merge_specialists")

# Define the Graph Edges
edges = [
    ('START', orchestrator_node),
    (orchestrator_node, dynamic_router),
    
    # Conditional route: Either direct response or Fan-out to all specialists
    (dynamic_router, {
        "specialists": (weather_node, market_node, crop_node, scheme_node),
        "__default__": direct_response_node
    }),
    
    # Native Fan-In: Wait for any triggered specialist branches to complete
    ((weather_node, market_node, crop_node, scheme_node), join_node),
    
    # Pass the merged output to synthesis
    (join_node, synthesis_node)
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
