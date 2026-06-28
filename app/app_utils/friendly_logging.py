import logging
from typing import Any, Optional
from google.genai import types
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

class FriendlyLoggingPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="friendly_logging")
        self.logger = logging.getLogger("friendly_logging")

    async def on_user_message_callback(
        self,
        *,
        invocation_context: InvocationContext,
        user_message: types.Content,
    ) -> Optional[types.Content]:
        query = ""
        if user_message.parts:
            query = user_message.parts[0].text or ""
        print("\n" + "-"*60)
        print(f"💬 [User Query] Received: \"{query}\"")
        print("-"*60 + "\n")
        return None

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        print("\n" + "-"*60)
        print(f"🤖 [Agent Start] Running: {agent.name}")
        print("-"*60 + "\n")
        return None

    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        print("\n" + "-"*60)
        print(f"🏁 [Agent End] Completed: {agent.name}")
        
        # Check for orchestrator completion to display routing decision and profile state
        if agent.name in ("orchestrator", "orchestrator_node"):
            active = callback_context.state.get("active_agents", [])
            missing = callback_context.state.get("missing_info_questions", [])
            profile = callback_context.state.get("profile", {})
            print(f"🧠 [Orchestrator Decision]")
            print(f"   👉 Active Agents: {active}")
            print(f"   ❓ Missing Info Questions: {missing}")
            print(f"   👤 Profile Status: {profile}")
        elif agent.name in ("synthesizer", "synthesis_agent", "synthesis_node"):
            print(f"✨ [Synthesis] Final advisory generated successfully.")
            
        print("-"*60 + "\n")
        return None

    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> Optional[dict]:
        print("\n" + "-"*60)
        print(f"🛠️ [Tool Calling] {tool.name}")
        print(f"   Parameters: {tool_args}")
        print("-"*60 + "\n")
        return None

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict,
    ) -> Optional[dict]:
        print("\n" + "-"*60)
        print(f"✅ [Tool Completed] {tool.name}")
        result_str = str(result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "... [truncated]"
        print(f"   Result: {result_str}")
        print("-"*60 + "\n")
        return None
