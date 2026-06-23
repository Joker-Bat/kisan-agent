from pydantic import BaseModel, Field
from typing import List, Optional, Any

class FarmerProfile(BaseModel):
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    state: Optional[str] = None
    soil_type: Optional[str] = None
    n_val: Optional[float] = None
    p_val: Optional[float] = None
    k_val: Optional[float] = None
    ph_val: Optional[float] = None
    rainfall_val: Optional[float] = None
    land_size_acres: Optional[float] = None
    income: Optional[float] = None
    tenancy_type: Optional[str] = None
    crop_intent: Optional[str] = None
    disaster_flag: bool = False
    damage_date: Optional[str] = None

class WeatherOutput(BaseModel):
    summary: str
    forecast_days: List[dict] = Field(default_factory=list)

class MarketOutput(BaseModel):
    crop: str
    state: str
    prices: List[dict] = Field(default_factory=list)

class CropOutput(BaseModel):
    recommended_crops: List[str] = Field(default_factory=list)
    rationale: str

class SchemeOutput(BaseModel):
    applicable_schemes: List[dict] = Field(default_factory=list)
    instructions: str

class GraphState(BaseModel):
    user_query: str = ""
    profile: FarmerProfile = Field(default_factory=FarmerProfile)
    weather_info: Optional[WeatherOutput] = None
    market_info: Optional[MarketOutput] = None
    crop_info: Optional[CropOutput] = None
    scheme_info: Optional[SchemeOutput] = None
    active_agents: List[str] = Field(default_factory=list)
    missing_info_questions: List[str] = Field(default_factory=list)
    final_advisory: Optional[str] = None
