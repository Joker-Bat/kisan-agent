from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class SchemeEligibility(BaseModel):
    target_group: Optional[str] = None
    land_requirement: Optional[str] = None
    crops_covered: Optional[str] = None
    income_criteria: Optional[str] = None
    exclusions: Optional[List[str]] = None
    additional_criteria: Optional[str] = None

class SchemeModel(BaseModel):
    id: str
    name: str
    type: str
    benefit: str
    eligibility: SchemeEligibility
    application_process: str
    url: Optional[str] = None

class FarmerProfile(BaseModel):
    location_name: Optional[str] = Field(default=None, description="The name of the village, city, or district provided by the farmer.")
    latitude: Optional[float] = Field(default=None, description="The geographical latitude of the farmer's location.")
    longitude: Optional[float] = Field(default=None, description="The geographical longitude of the farmer's location.")
    state: Optional[str] = Field(default=None, description="The Indian state where the farm is located (e.g., 'Tamil Nadu').")
    soil_type: Optional[str] = Field(default=None, description="The type of soil present on the farm (e.g., 'Red soil', 'Black soil').")
    n_val: Optional[float] = Field(default=None, description="Nitrogen content in the soil. Can be imputed by the LLM if exact values are unknown.")
    p_val: Optional[float] = Field(default=None, description="Phosphorous content in the soil. Can be imputed by the LLM if unknown.")
    k_val: Optional[float] = Field(default=None, description="Potassium content in the soil. Can be imputed by the LLM if unknown.")
    ph_val: Optional[float] = Field(default=None, description="pH level of the soil. Can be imputed by the LLM if unknown.")
    rainfall_val: Optional[float] = Field(default=None, description="Expected average rainfall in mm. Can be imputed by the LLM based on location.")
    land_size_acres: Optional[float] = Field(default=None, description="The total land size owned or leased by the farmer, in acres.")
    income: Optional[float] = Field(default=None, description="The annual income of the farmer in INR.")
    tenancy_type: Optional[str] = Field(default=None, description="The type of land tenancy (e.g., 'owner', 'tenant', 'sharecropper').")
    crop_intent: Optional[str] = Field(default=None, description="The specific crop the farmer is planning to grow or is inquiring about.")
    disaster_flag: bool = Field(default=False, description="True if the farmer is reporting a crop loss or disaster scenario (e.g., flood, drought).")
    damage_date: Optional[str] = Field(default=None, description="The date the crop damage occurred, if applicable.")

class WeatherOutput(BaseModel):
    summary: str = Field(description="A concise, plain-language summary of the weather forecast over the next 14 days.")
    forecast_days: List[dict] = Field(default_factory=list, description="A structured list containing daily precipitation, max/min temperature, and soil temperature.")

class MarketOutput(BaseModel):
    crop: str = Field(description="The name of the crop for which the market price was retrieved.")
    state: str = Field(description="The state where the mandi (market) is located.")
    prices: List[dict] = Field(default_factory=list, description="A list of recent wholesale prices across various nearby mandis.")

class CropOutput(BaseModel):
    recommended_crops: List[str] = Field(default_factory=list, description="A list of the top recommended crops suitable for the farmer's soil and weather.")
    rationale: str = Field(description="The agricultural reasoning behind the crop recommendations.")

class SchemeOutput(BaseModel):
    applicable_schemes: List[dict] = Field(default_factory=list, description="A list of government schemes the farmer is eligible for.")
    instructions: str = Field(description="Step-by-step instructions on how the farmer can apply or claim benefits for the listed schemes.")

class GraphState(BaseModel):
    model_config = {"extra": "allow"}

    user_query: str = Field(default="", description="The current natural language query from the user.")
    profile: FarmerProfile = Field(default_factory=FarmerProfile, description="The persistent profile of the farmer, updated as new info is collected.")
    weather_info: Optional[WeatherOutput] = Field(default=None, description="The output from the WeatherAgent, if invoked.")
    market_info: Optional[MarketOutput] = Field(default=None, description="The output from the MarketAgent, if invoked.")
    crop_info: Optional[CropOutput] = Field(default=None, description="The output from the CropAgent, if invoked.")
    scheme_info: Optional[SchemeOutput] = Field(default=None, description="The output from the SchemeAgent, if invoked.")
    active_agents: List[str] = Field(default_factory=list, description="A list of agent node names that the Orchestrator has decided to trigger for the current turn.")
    missing_info_questions: List[str] = Field(default_factory=list, description="A list of follow-up questions the Orchestrator must ask the user to collect required missing parameters for the active agents.")
    final_advisory: Optional[str] = Field(default=None, description="The final synthesized bilingual response generated by the SynthesisAgent.")

# To prevent ADK's _validate_state_entry from throwing StateSchemaError during evaluation,
# we must expose its internal keys to Pydantic's model_fields. Pydantic forbids declaring
# fields with '__' prefixes inside the class body, so we inject them dynamically here.
from pydantic.fields import FieldInfo
GraphState.model_fields["__user_simulation_app__"] = FieldInfo(annotation=Any, default=None)
GraphState.model_fields["__llm_request_key__"] = FieldInfo(annotation=Any, default=None)
