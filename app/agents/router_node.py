from google.adk.events.event import Event, EventActions
from google.adk.workflow import node

from app.core.constants import ROUTE_DIRECT_RESPONSE, ROUTE_SPECIALISTS
from app.core.schemas import GraphState


@node
def dynamic_router(node_input: GraphState):
    """
    Reads the active_agents requested by the orchestrator and triggers native ADK multi-route fan-out.
    If no agents are active, or if there is missing information, routes directly to END/direct_response.
    """
    # Short-circuit if missing info
    if node_input.missing_info_questions:
        return Event(
            output=" ".join(node_input.missing_info_questions),
            actions=EventActions(route=ROUTE_DIRECT_RESPONSE),
        )

    if not node_input.active_agents:
        output = (
            node_input.final_advisory
            or "I am the Kisan Agent. How can I assist you with your farming needs today?"
        )
        return Event(output=output, actions=EventActions(route=ROUTE_DIRECT_RESPONSE))

    # Return the exact same GraphState as output so child nodes get it
    # Route to the specialists branch which triggers the unconditional parallel fan-out
    return Event(output=node_input, actions=EventActions(route=ROUTE_SPECIALISTS))
