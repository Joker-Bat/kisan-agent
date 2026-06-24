import asyncio
from google.adk.workflow import node
from google.adk.events.event import Event
from google.adk.agents.context import Context

from app.core.schemas import GraphState
from app.core.constants import ROUTE_SYNTHESIS, ROUTE_DIRECT_RESPONSE
from app.agents.weather_agent import weather_node
from app.agents.market_agent import market_node
from app.agents.crop_agent import crop_node
from app.agents.scheme_agent import scheme_node

@node(rerun_on_resume=True)
async def dynamic_router(ctx: Context, node_input: GraphState):
    return await dynamic_router_logic(ctx, node_input)

async def dynamic_router_logic(ctx: Context, node_input: GraphState):
    """Dynamically parallelizes and schedules sub-agents based on Orchestrator's routing."""
    
    # Short-circuit if missing info
    if node_input.missing_info_questions:
        return Event(output=" ".join(node_input.missing_info_questions), route=ROUTE_DIRECT_RESPONSE)
        
    if not node_input.active_agents:
        return Event(output="I am the Kisan Agent. How can I assist you with your farming needs today?", route=ROUTE_DIRECT_RESPONSE)

    tasks = []
    keys = []
    
    if "weather_agent" in node_input.active_agents:
        tasks.append(ctx.run_node(weather_node, node_input=node_input))
        keys.append("weather")
        
    if "market_agent" in node_input.active_agents:
        tasks.append(ctx.run_node(market_node, node_input=node_input))
        keys.append("market")
        
    if "crop_agent" in node_input.active_agents:
        tasks.append(ctx.run_node(crop_node, node_input=node_input))
        keys.append("crop")
        
    if "scheme_agent" in node_input.active_agents:
        tasks.append(ctx.run_node(scheme_node, node_input=node_input))
        keys.append("scheme")
        
    # Execute all dynamically scheduled agents concurrently
    outputs = await asyncio.gather(*tasks)
    results = {k: out for k, out in zip(keys, outputs)}
    
    # We pass the combined results to the synthesis route
    return Event(output=results, route=ROUTE_SYNTHESIS)
