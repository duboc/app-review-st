# Copyright 2024
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

import os
import logging
import time
from typing import Union, List, Any, Dict, Optional, Tuple
from google.api_core.exceptions import ResourceExhausted

import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmCategory,
    Part,
    FinishReason
)
import vertexai.generative_models as generative_models

from tenacity import retry, stop_after_attempt, wait_exponential

class GeminiRegionClient:
    def __init__(self, project_id: str = None, logger: logging.Logger = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT")
        if not self.project_id:
            raise ValueError("Project ID must be provided or set in GCP_PROJECT environment variable")
            
        self.logger = logger or logging.getLogger(__name__)
        
        # Try to import app_logger if available
        try:
            from .logger import app_logger
            self.app_logger = app_logger
        except ImportError:
            self.app_logger = None
        
        self.regions = [
            "us-east5",
            "northamerica-northeast1", 
            "europe-west2",
            "europe-west3",
            "asia-northeast1",
            "asia-south1",
            "southamerica-east1",
            "australia-southeast1"
        ]
        
        self.safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.default_generation_config = GenerationConfig(
            max_output_tokens=8192,
            temperature=0.3,
            top_p=0.95,
        )
        
        # Log initialization
        if self.app_logger:
            self.app_logger.log_user_action("Initialized Gemini client", {"project_id": self.project_id})

    def _initialize_region(self, region: str) -> None:
        vertexai.init(project=self.project_id, location=region)
        
    def _get_model(self) -> GenerativeModel:
        return GenerativeModel("gemini-2.0-flash-001")

    def extract_response_metadata(self, response) -> Dict[str, Any]:
        """Extract and structure metadata from a Gemini response."""
        metadata = {
            "token_count": {
                "prompt": getattr(response.usage_metadata, "prompt_token_count", 0),
                "candidates": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total": getattr(response.usage_metadata, "total_token_count", 0)
            },
            "candidates": []
        }
        
        for i, candidate in enumerate(response.candidates):
            candidate_data = {
                "index": candidate.index,
                "finish_reason": candidate.finish_reason,
                "finish_message": candidate.finish_message
            }
            
            # Extract safety ratings if available
            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                candidate_data["safety_ratings"] = [
                    {
                        "category": str(rating.category),
                        "probability": str(rating.probability),
                        "blocked": rating.blocked
                    } 
                    for rating in candidate.safety_ratings
                ]
            
            metadata["candidates"].append(candidate_data)
            
        return metadata

    def get_finish_reason_description(self, finish_reason) -> str:
        """
        Convert a FinishReason enum to a human-readable description.
        
        Args:
            finish_reason: The finish reason from the API response
            
        Returns:
            A human-readable description of the finish reason
        """
        reason_map = {
            FinishReason.FINISH_REASON_UNSPECIFIED: "The finish reason is unspecified",
            FinishReason.STOP: "The model completed normally",
            FinishReason.MAX_TOKENS: "The model reached the token limit",
            FinishReason.SAFETY: "Content filtered for safety reasons",
            FinishReason.RECITATION: "Potential recitation detected",
            FinishReason.OTHER: "Other stopping reason",
            # Numeric fallbacks for older API versions
            "0": "The finish reason is unspecified",
            "1": "The model reached the token limit",
            "2": "Content filtered for safety reasons",
            "3": "Potential recitation detected",
            "4": "Other stopping reason",
            "5": "Content contains blocked terms",
            "6": "Content contains prohibited material",
            "7": "Sensitive Personal Identifiable Information detected",
            "8": "Invalid function call format"
        }
        
        # Handle string representations
        if isinstance(finish_reason, str):
            if finish_reason in reason_map:
                return reason_map[finish_reason]
            if finish_reason.isdigit() and finish_reason in reason_map:
                return reason_map[finish_reason]
            return finish_reason
                    
        # Try to get the enum name
        return reason_map.get(finish_reason, str(finish_reason))

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    def generate_content(self, prompt: Union[str, List[Union[str, Part]]], response_mime_type: str = None, return_full_response: bool = False, **kwargs) -> Union[str, Dict[str, Any], Tuple[str, str, Dict]]:
        """
        Generate content using Gemini API with support for multiple regions and simplified finish reason handling.
        
        Args:
            prompt: The text prompt or list of prompts to send to the model
            response_mime_type: Optional MIME type for the response
            return_full_response: Whether to return the full response object with metadata (True) or just the text (False)
            **kwargs: Additional keyword arguments to pass to the model
            
        Returns:
            By default: Just the generated text (str)
            If return_full_response=True: A dict with 'text', 'finish_reason', and 'metadata' keys
        """
        last_error = None
        start_time = time.time()
        prompt_length = len(str(prompt)) if isinstance(prompt, str) else "multipart"
        
        # Log API call start
        if self.app_logger:
            self.app_logger.log_api_call(
                api_name="gemini.generate_content",
                params={"prompt_length": prompt_length}
            )
        
        # Make a copy of kwargs to avoid modifying the original
        model_kwargs = kwargs.copy()
        
        for region in self.regions:
            try:
                self._initialize_region(region)
                model = self._get_model()
                
                gen_config = model_kwargs.pop('generation_config', self.default_generation_config)
                if response_mime_type:
                    gen_config = GenerationConfig(
                        **gen_config.to_dict(),
                        response_mime_type=response_mime_type
                    )
                
                if isinstance(prompt, list) and len(prompt) == 2:
                    image_content, text_prompt = prompt
                    if not isinstance(image_content, Part):
                        image_content = Part.from_data(image_content, mime_type="image/jpeg")
                    prompt = [image_content, text_prompt]
                
                # Track region-specific time
                region_start_time = time.time()
                
                # Call the model's generate_content WITHOUT passing our return_full_response flag
                response = model.generate_content(
                    prompt,
                    generation_config=gen_config,
                    safety_settings=self.safety_settings,
                    **model_kwargs
                )
                
                # Calculate timings
                region_duration_ms = (time.time() - region_start_time) * 1000
                total_duration_ms = (time.time() - start_time) * 1000
                
                # Always extract response metadata and finish reason
                response_metadata = self.extract_response_metadata(response)
                
                # Get the finish reason from the first candidate
                finish_reason_raw = None
                finish_message = ""
                if response_metadata["candidates"]:
                    finish_reason_raw = response_metadata["candidates"][0]["finish_reason"]
                    finish_message = response_metadata["candidates"][0]["finish_message"]
                
                # Get a human-readable description of the finish reason
                finish_reason_desc = self.get_finish_reason_description(finish_reason_raw)
                
                # Log successful API call
                if self.app_logger:
                    response_length = len(response.text) if hasattr(response, 'text') else 0
                    self.app_logger.log_api_call(
                        api_name="gemini.generate_content",
                        params={
                            "prompt_length": prompt_length, 
                            "region": region,
                            "finish_reason": finish_reason_raw,
                            "finish_message": finish_message
                        },
                        response_status="success",
                        duration_ms=total_duration_ms
                    )
                    self.app_logger.log_performance(
                        "gemini_api_call",
                        total_duration_ms,
                        {
                            "region": region,
                            "region_duration_ms": region_duration_ms,
                            "response_length": response_length,
                            "token_count": response_metadata["token_count"]
                        }
                    )
                
                # Return based on the return_full_response flag
                if return_full_response:
                    return {
                        "text": response.text,
                        "finish_reason": finish_reason_desc,
                        "finish_reason_raw": finish_reason_raw,
                        "metadata": response_metadata
                    }
                
                return response.text
                
            except ResourceExhausted as e:
                self.logger.warning(f"Region {region} exhausted. Trying next region...")
                if self.app_logger:
                    self.app_logger.log_api_call(
                        api_name="gemini.generate_content",
                        params={"prompt_length": prompt_length, "region": region},
                        response_status="exhausted",
                        duration_ms=(time.time() - start_time) * 1000
                    )
                last_error = e
            except Exception as e:
                self.logger.warning(f"Unexpected error with region {region}: {str(e)}")
                if self.app_logger:
                    self.app_logger.log_error(
                        f"Gemini API error with region {region}",
                        exception=e,
                        context={"prompt_length": prompt_length}
                    )
                last_error = e
        
        # All regions failed
        if self.app_logger:
            self.app_logger.log_error(
                "All Gemini API regions failed",
                exception=last_error,
                context={"prompt_length": prompt_length}
            )
        
        raise Exception(f"All regions failed. Last error: {str(last_error)}") from last_error 