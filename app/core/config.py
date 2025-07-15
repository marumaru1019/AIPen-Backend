# app/core/config.py
import os
from dotenv import load_dotenv

# プロジェクトルートの .env ファイルを読み込む
load_dotenv()

class Settings:
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "default_key")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "https://eastus.api.cognitive.microsoft.com/")
    OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2023-07-01-preview")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    DALL_E_URL: str = os.getenv("DALL_E_URL", "https://poc-apim-aipen-jrw.azure-api.net/create-image/deployments/dall-e-3/images/generations?api-version=2024-10-21")
    DALL_E_API_KEY: str = os.getenv("DALL_E_API_KEY", "default_dalle_key")
    GENERATE_HTML_URL: str = os.getenv("GENERATE_HTML_URL", "https://appservice-aipen-jrw.azurewebsites.net/generate_html")

settings = Settings()
