import asyncio
from google.adk.workflow import node, Event
from google.adk.agents.context import Context

from app.core.schemas import GraphState
from app.core.constants import ROUTE_SYNTHESIS, ROUTE_DIRECT_RESPONSE
from app.agents.weather_agent import run_weather_agent
from app.agents.market_agent import run_market_agent
from app.agents.crop_agent import run_crop_agent
from app.agents.scheme_agent import run_scheme_agent

# Wrappers for standalone agents so they can be dynamically scheduled
async def weather_node(node_input: GraphState):
    return run_weather_agent(node_input.profile)

async def market_node(node_input: GraphState):
    return run_market_agent(node_input.profile)

async def crop_node(node_input: GraphState):
    return run_crop_agent(node_input.profile, None)

async def scheme_node(node_input: GraphState):
    return run_scheme_agent(node_input.profile)

@node(rerun_on_resume=True)
async def dynamic_router(ctx: Context, state: GraphState):
    """Dynamically parallelizes and schedules sub-agents based on Orchestrator's routing."""
    
    # Short-circuit if missing info
    if state.missing_info_questions:
        return Event(output=" ".join(state.missing_info_questions), route=ROUTE_DIRECT_RESPONSE)
        
    if not state.active_agents:
        return Event(output="I am the Kisan Agent. How can I assist you with your farming needs today?", route=ROUTE_DIRECT_RESPONSE)

    tasks = []
    keys = []
    
    if "weather_agent" in state.active_agents:
        tasks.append(ctx.run_node(weather_node, node_input=state))
        keys.append("weather")
        
    if "market_agent" in state.active_agents:
        tasks.append(ctx.run_node(market_node, node_input=state))
        keys.append("market")
        
    if "crop_agent" in state.active_agents:
        tasks.append(ctx.run_node(crop_node, node_input=state))
        keys.append("crop")
        
    if "scheme_agent" in state.active_agents:
        tasks.append(ctx.run_node(scheme_node, node_input=state))
        keys.append("scheme")
        
    # Execute all dynamically scheduled agents concurrently
    outputs = await asyncio.gather(*tasks)
    results = {k: out for k, out in zip(keys, outputs)}
    
    # We pass the combined results to the synthesis route
    return Event(output=results, route=ROUTE_SYNTHESIS)
