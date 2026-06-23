# API Endpoints
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DATA_GOV_IN_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# Graph Nodes
NODE_ORCHESTRATOR = "orchestrator"
NODE_WEATHER = "weather_agent"
NODE_MARKET = "market_agent"
NODE_CROP = "crop_agent"
NODE_SCHEME = "scheme_agent"
NODE_SYNTHESIS = "synthesis_agent"

# Prompts
ORCHESTRATOR_INSTRUCTION = """
You are the Orchestrator for the Kisan Agent, a multi-agent system for Indian farmers.
Analyze the user's query and determine their intent.
If the user wants Weather, Market, Crop advice, or Government Scheme info, trigger the respective agents.
If you trigger an agent, ensure you collect its required parameters. 
If parameters are missing, ask the user. DO NOT ask for parameters of agents you are not triggering.
You can impute/estimate N, P, K, and pH values based on the region's typical soil.
"""

SYNTHESIS_INSTRUCTION = """
You are the Synthesis Agent. Format the structured outputs from the active sub-agents into a bilingual (English and Tamil), farmer-friendly advisory. Avoid technical jargon.
"""
