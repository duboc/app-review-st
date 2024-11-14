from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Environment variables with defaults
class Config:
    GCP_PROJECT = os.getenv('GCP_PROJECT', 'conventodapenha')
    GCP_REGION = os.getenv('GCP_REGION', 'us-central1')
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8080'))

    @classmethod
    def validate(cls):
        """Validate required environment variables are set"""
        required_vars = ['GCP_PROJECT']
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}") 