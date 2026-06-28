from typing import Any

from pydantic import BaseModel, Field


class SchemeEligibility(BaseModel):
    target_group: str | None = None
    land_requirement: str | None = None
    crops_covered: str | None = None
    income_criteria: str | None = None
    exclusions: list[str] | None = None
    additional_criteria: str | None = None


class SchemeModel(BaseModel):
    id: str
    name: str
    type: str
    benefit: str
    eligibility: SchemeEligibility
    application_process: str
    url: str | None = None


class FarmerProfile(BaseModel):
    preferred_language: str = Field(
        default="English",
        description="The preferred language of the user for all responses (e.g., 'English', 'Tamil', 'Tanglish').",
    )
    location_name: str | None = Field(
        default=None,
        description="The name of the village, city, or district provided by the farmer.",
    )
    latitude: float | None = Field(
        default=None, description="The geographical latitude of the farmer's location."
    )
    longitude: float | None = Field(
        default=None, description="The geographical longitude of the farmer's location."
    )
    state: str | None = Field(
        default=None,
        description="The Indian state where the farm is located (e.g., 'Tamil Nadu').",
    )
    district: str | None = Field(
        default=None,
        description="The district name resolved from the location or query, used for local market price filtering.",
    )
    market: str | None = Field(
        default=None,
        description="The specific market/mandi name resolved from the location or query.",
    )
    soil_type: str | None = Field(
        default=None,
        description="The type of soil present on the farm (e.g., 'Red soil', 'Black soil').",
    )
    n_val: float | None = Field(
        default=None,
        description="Nitrogen content in the soil. Can be imputed by the LLM if exact values are unknown.",
    )
    p_val: float | None = Field(
        default=None,
        description="Phosphorous content in the soil. Can be imputed by the LLM if unknown.",
    )
    k_val: float | None = Field(
        default=None,
        description="Potassium content in the soil. Can be imputed by the LLM if unknown.",
    )
    ph_val: float | None = Field(
        default=None,
        description="pH level of the soil. Can be imputed by the LLM if unknown.",
    )
    rainfall_val: float | None = Field(
        default=None,
        description="Expected average rainfall in mm. Can be imputed by the LLM based on location.",
    )
    land_size_acres: float | None = Field(
        default=None,
        description="The total land size owned or leased by the farmer, in acres.",
    )
    income: float | None = Field(
        default=None, description="The annual income of the farmer in INR."
    )
    tenancy_type: str | None = Field(
        default=None,
        description="The type of land tenancy (e.g., 'owner', 'tenant', 'sharecropper').",
    )
    crop_intent: list[str] = Field(
        default_factory=list,
        description="A list of individual crop names (e.g., ['Cotton', 'Sorghum'] instead of ['Cotton and Sorghum']) that the farmer is planning to grow or inquiring about.",
    )
    disaster_flag: bool = Field(
        default=False,
        description="True if the farmer is reporting a crop loss or disaster scenario (e.g., flood, drought).",
    )
    damage_date: str | None = Field(
        default=None, description="The date the crop damage occurred, if applicable."
    )
    weather_start_date: str | None = Field(
        default=None,
        description="The start date for weather queries in YYYY-MM-DD format.",
    )
    weather_end_date: str | None = Field(
        default=None,
        description="The end date for weather queries in YYYY-MM-DD format.",
    )


class WeatherOutput(BaseModel):
    summary: str = Field(
        description="A concise, plain-language summary of the weather forecast or history over the requested date range."
    )
    forecast_days: list[dict] = Field(
        default_factory=list,
        description="A structured list containing daily precipitation, max/min temperature, and soil temperature.",
    )


class MarketOutput(BaseModel):
    crop: str = Field(
        description="The name of the crop for which the market price was retrieved."
    )
    state: str = Field(description="The state where the mandi (market) is located.")
    prices: list[dict] = Field(
        default_factory=list,
        description="A list of recent wholesale prices across various nearby mandis.",
    )
    summary: str | None = Field(
        default=None,
        description="A summary of the market prices and recommendations on where the farmer should sell.",
    )


class CropOutput(BaseModel):
    recommended_crops: list[str] = Field(
        default_factory=list,
        description="A list of the top recommended crops suitable for the farmer's soil and weather.",
    )
    rationale: str = Field(
        description="The agricultural reasoning behind the crop recommendations."
    )


class SchemeOutput(BaseModel):
    applicable_schemes: list[dict] = Field(
        default_factory=list,
        description="A list of government schemes the farmer is eligible for.",
    )
    instructions: str = Field(
        description="Step-by-step instructions on how the farmer can apply or claim benefits for the listed schemes."
    )


class OrchestratorOutput(BaseModel):
    profile: FarmerProfile = Field(
        description="The updated profile of the farmer based on the user's latest query."
    )
    active_agents: list[str] = Field(
        default_factory=list,
        description="A list of agent node names to activate for this turn (e.g., 'weather_agent', 'market_agent', 'crop_agent', 'scheme_agent').",
    )
    missing_info_questions: list[str] = Field(
        default_factory=list,
        description="A list of follow-up questions to ask the user if required parameters are missing.",
    )
    final_advisory: str | None = Field(
        default=None,
        description="A direct response or greeting to the user if no specialists are activated.",
    )


class GraphState(BaseModel):
    model_config = {"extra": "allow"}

    user_query: str = Field(
        default="", description="The current natural language query from the user."
    )
    profile: FarmerProfile = Field(
        default_factory=FarmerProfile,
        description="The persistent profile of the farmer, updated as new info is collected.",
    )
    weather_info: WeatherOutput | None = Field(
        default=None, description="The output from the WeatherAgent, if invoked."
    )
    market_info: MarketOutput | None = Field(
        default=None, description="The output from the MarketAgent, if invoked."
    )
    crop_info: CropOutput | None = Field(
        default=None, description="The output from the CropAgent, if invoked."
    )
    scheme_info: SchemeOutput | None = Field(
        default=None, description="The output from the SchemeAgent, if invoked."
    )
    active_agents: list[str] = Field(
        default_factory=list,
        description="A list of agent node names that the Orchestrator has decided to trigger for the current turn.",
    )
    missing_info_questions: list[str] = Field(
        default_factory=list,
        description="A list of follow-up questions the Orchestrator must ask the user to collect required missing parameters for the active agents.",
    )
    final_advisory: str | None = Field(
        default=None,
        description="The final synthesized bilingual response generated by the SynthesisAgent.",
    )


# To prevent ADK's _validate_state_entry from throwing StateSchemaError during evaluation,
# we must expose its internal keys to Pydantic's model_fields. Pydantic forbids declaring
# fields with '__' prefixes inside the class body, so we inject them dynamically here.
from pydantic.fields import FieldInfo

GraphState.model_fields["__user_simulation_app__"] = FieldInfo(
    annotation=Any, default=None
)
GraphState.model_fields["__llm_request_key__"] = FieldInfo(annotation=Any, default=None)
