import os


class Settings:
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True")
    DATA_GOV_IN_API_KEY = os.getenv("DATA_GOV_IN_API_KEY")
    REGION = os.getenv("REGION", "TN_INDIA")


settings = Settings()
