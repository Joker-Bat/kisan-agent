import os
from dotenv import load_dotenv

from google.adk.apps import App
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import GraphState
from app.core.constants import ORCHESTRATOR_INSTRUCTION, SYNTHESIS_INSTRUCTION
from app.agents.weather_agent import run_weather_agent
from app.agents.market_agent import run_market_agent
from app.agents.crop_agent import run_crop_agent
from app.agents.scheme_agent import run_scheme_agent

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

class KisanAgentRunner:
    def __init__(self):
        self.orchestrator = Agent(
            name="orchestrator",
            model=Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
            instruction=ORCHESTRATOR_INSTRUCTION,
            output_type=GraphState
        )
        self.synthesizer = Agent(
            name="synthesis_agent",
            model=Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
            instruction=SYNTHESIS_INSTRUCTION,
        )

    def __call__(self, query: str) -> str:
        print(f"[Orchestrator] Analyzing query: '{query}'")
        
        # Step 1: Orchestrator analyzes intent and extracts parameters
        initial_prompt = f"User Query: {query}"
        
        try:
            state: GraphState = self.orchestrator(initial_prompt)
        except Exception as e:
            return f"Sorry, I encountered an error analyzing your request: {str(e)}"
            
        print(f"[Orchestrator] Extracted Profile: {state.profile}")
        print(f"[Orchestrator] Active Agents: {state.active_agents}")
        
        # Optional: Ask follow-up questions if critical parameters for the requested agent are missing
        if state.missing_info_questions:
            print("[Orchestrator] Missing information, asking user...")
            return " ".join(state.missing_info_questions)
            
        # Step 2: Dynamic Routing (Fan-Out)
        if not state.active_agents:
            return "I am the Kisan Agent. How can I assist you with your farming needs today?"
            
        if "weather_agent" in state.active_agents:
            print("[Running] Weather Agent...")
            state.weather_info = run_weather_agent(state.profile)
            
        if "market_agent" in state.active_agents:
            print("[Running] Market Agent...")
            state.market_info = run_market_agent(state.profile)
            
        if "crop_agent" in state.active_agents:
            print("[Running] Crop Agent...")
            state.crop_info = run_crop_agent(state.profile, state.weather_info)
            
        if "scheme_agent" in state.active_agents:
            print("[Running] Scheme Agent...")
            state.scheme_info = run_scheme_agent(state.profile)
            
        # Step 3: Synthesis (Fan-In)
        print("[Running] Synthesis Agent...")
        synthesis_prompt = f"User Query: {query}\nPopulated State: {state.model_dump_json()}"
        
        try:
            final_response = self.synthesizer(synthesis_prompt)
            return final_response
        except Exception as e:
            return f"Sorry, I gathered the data but encountered an error synthesizing the response: {str(e)}"

# Instantiate the runner and bind to the ADK App
root_agent = KisanAgentRunner()
app = App(
    root_agent=root_agent,
    name="kisan-app"
)
