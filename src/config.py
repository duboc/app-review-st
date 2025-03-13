# Copyright 2024 The Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Environment variables with defaults
class Config:
    GCP_PROJECT = os.getenv('GCP_PROJECT', 'conventodapenha')
    GCP_REGION = os.getenv('GCP_REGION', 'us-central1')
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8080'))
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    ENABLE_FILE_LOGGING = os.getenv('ENABLE_FILE_LOGGING', 'False').lower() == 'true'
    
    # User activity logging
    LOG_USER_ACTIONS = True
    LOG_API_CALLS = True
    LOG_PERFORMANCE = True

    @classmethod
    def validate(cls):
        """Validate required environment variables are set"""
        required_vars = ['GCP_PROJECT']
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @classmethod
    def setup_logging(cls):
        """Configure logging based on settings"""
        log_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=cls.LOG_FORMAT
        )
        
        # Add file handler if enabled
        if cls.ENABLE_FILE_LOGGING:
            file_handler = logging.FileHandler(cls.LOG_FILE)
            file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
            logging.getLogger().addHandler(file_handler)
        
        return logging.getLogger('app') 