import os

from dotenv import load_dotenv
from google.adk.apps import App
from google.adk.workflow import JoinNode, Workflow

from app.agents.crop_agent import crop_node
from app.agents.direct_response_node import direct_response_node
from app.agents.market_agent import market_node
from app.agents.orchestrator_agent import orchestrator_node
from app.agents.router_node import dynamic_router
from app.agents.scheme_agent import scheme_node
from app.agents.synthesis_agent import synthesis_node
from app.agents.weather_agent import weather_node
from app.app_utils.log_config import setup_logging
from app.core.schemas import GraphState

setup_logging()
load_dotenv()

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True")

from app.core.constants import ROUTE_SPECIALISTS

join_node = JoinNode(name="merge_specialists")

# In ADK 2.0, the graph topology is static, and the JoinNode expects an Event output
# from every single predecessor branch. If any branch is skipped entirely at the route level,
# the JoinNode will block/deadlock waiting for it.
# To prevent this, we declare the specialists once and route to all of them concurrently:
# Non-active specialists immediately return "SKIPPED" (~0ms) to satisfy the JoinNode fan-in.
specialists = (weather_node, market_node, crop_node, scheme_node)

# Define the Graph Edges
edges = [
    ("START", orchestrator_node),
    (orchestrator_node, dynamic_router),
    # Conditional route: Either route directly or fan-out to all specialists
    (
        dynamic_router,
        {
            ROUTE_SPECIALISTS: specialists,
            "__default__": direct_response_node,
        },
    ),
    # Fan-In: JoinNode merges all outputs from the fanned-out specialist branches
    (specialists, join_node),
    # Pass the merged output to synthesis
    (join_node, synthesis_node),
]

root_agent = Workflow(
    name="kisan_workflow",
    edges=edges,
    description="A multi-agent graph workflow for Indian farmers.",
    state_schema=GraphState,
)

app = App(root_agent=root_agent, name="app")
