# Kisan Agent Project Guidelines

## Tech Stack
- **Framework:** Google ADK (Agent Development Kit) 2.0 with graph-based workflows (`Workflow`, `LlmAgent`, `FunctionNode`).
- **Language:** Python 3.12+
- **Model:** Gemini (`gemini-2.5-flash`) via `google-genai` SDK.
- **Provider Adapters:** Open-Meteo (Weather), Data.gov.in (Mandi Prices), Local JSON (`TN_INDIA.json` for Schemes).
- **Validation:** Pydantic for state and I/O schemas.
- **Testing:** Pytest with `anyio`/`pytest-asyncio` for unit, integration, and E2E testing.

## Operational Rules & Patterns
1. **Adapter Pattern:** ALL external data sources (APIs, databases, web scraping) MUST be implemented using the Adapter pattern with strongly typed Pydantic models. We define a generic `Protocol` for the data provider and specific implementations (e.g., `OpenMeteoProvider`, `GovInMandiProvider`).
2. **Graceful Degradation:** Agents MUST never get "stuck" or crash the workflow on API failures or LLM generation errors. Every API call and LLM execution must be wrapped in `try-except` blocks that yield user-friendly fallback messages instead of raw exceptions.
3. **Structured Outputs:** Always define an `output_schema` for `LlmAgent` nodes within workflows, ensuring they return predictable Pydantic models instead of raw strings.
4. **Testing Policy:** Do NOT run the full test suite (`uv run pytest`) after every minor change, as it consumes API quota by making real calls to the LLM. Only run tests after major architectural changes, new feature additions, or before deployments. Use `agents-cli dev` (the ADK playground) for interactive, manual verification of small tweaks.
5. **Workflow Routing:** ADK 2.0 uses `Event(branch="target_route")` for conditional edge traversal. Ensure node outputs properly emit events with valid branches that match defined edges in `app/agent.py`.
