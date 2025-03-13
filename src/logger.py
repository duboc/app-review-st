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

import logging
import time
import uuid
import json
from datetime import datetime
import streamlit as st
from functools import wraps
from typing import Dict, Any, Optional, Callable, List, Union

class AppLogger:
    """Enhanced logger for the application with user action tracking and performance monitoring."""
    
    def __init__(self, name: str = 'app'):
        self.logger = logging.getLogger(name)
        self.session_id = str(uuid.uuid4())[:8]  # Generate a unique session ID
        
        # Initialize session state for logs if not exists
        if 'log' not in st.session_state:
            st.session_state.log = []
        
        if 'log_categories' not in st.session_state:
            st.session_state.log_categories = {
                'user_action': [],
                'api_call': [],
                'error': [],
                'performance': []
            }
    
    def _format_log_entry(self, message: str, category: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format a log entry as a structured dictionary."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            'timestamp': timestamp,
            'session_id': self.session_id,
            'category': category,
            'message': message
        }
        
        if details:
            entry['details'] = details
            
        return entry
    
    def log_user_action(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a user action with optional details."""
        entry = self._format_log_entry(action, 'user_action', details)
        
        # Add to session state logs
        st.session_state.log.append(f"{entry['timestamp']}: {action}")
        st.session_state.log_categories['user_action'].append(entry)
        
        # Log to system logger
        self.logger.info(f"USER ACTION: {action} - {json.dumps(details) if details else ''}")
    
    def log_api_call(self, api_name: str, params: Optional[Dict[str, Any]] = None, 
                    response_status: Optional[str] = None, duration_ms: Optional[float] = None) -> None:
        """Log an API call with details about the request and response."""
        details = {
            'api_name': api_name
        }
        
        if params:
            # Filter out sensitive information
            safe_params = {k: v for k, v in params.items() 
                          if not any(sensitive in k.lower() for sensitive in ['key', 'token', 'secret', 'password'])}
            details['params'] = safe_params
            
        if response_status:
            details['status'] = response_status
            
        if duration_ms:
            details['duration_ms'] = duration_ms
        
        entry = self._format_log_entry(f"API Call: {api_name}", 'api_call', details)
        
        # Add to session state logs
        st.session_state.log.append(f"{entry['timestamp']}: API Call to {api_name} ({response_status or 'unknown'}) - {duration_ms or 0}ms")
        st.session_state.log_categories['api_call'].append(entry)
        
        # Log to system logger
        self.logger.info(f"API CALL: {api_name} - Status: {response_status} - Duration: {duration_ms}ms")
    
    def log_error(self, error_message: str, exception: Optional[Exception] = None, 
                 context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with details about the exception and context."""
        details = {}
        
        if exception:
            details['exception_type'] = type(exception).__name__
            details['exception_message'] = str(exception)
            
        if context:
            details['context'] = context
        
        entry = self._format_log_entry(error_message, 'error', details)
        
        # Add to session state logs
        st.session_state.log.append(f"{entry['timestamp']}: ERROR - {error_message}")
        st.session_state.log_categories['error'].append(entry)
        
        # Log to system logger
        if exception:
            self.logger.exception(f"ERROR: {error_message}")
        else:
            self.logger.error(f"ERROR: {error_message} - {json.dumps(details) if details else ''}")
    
    def log_performance(self, operation: str, duration_ms: float, details: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics for an operation."""
        perf_details = {'duration_ms': duration_ms}
        
        if details:
            perf_details.update(details)
            
        entry = self._format_log_entry(f"Performance: {operation}", 'performance', perf_details)
        
        # Add to session state logs
        st.session_state.log.append(f"{entry['timestamp']}: PERF - {operation} took {duration_ms:.2f}ms")
        st.session_state.log_categories['performance'].append(entry)
        
        # Log to system logger
        self.logger.info(f"PERFORMANCE: {operation} - {duration_ms:.2f}ms - {json.dumps(details) if details else ''}")
    
    def get_logs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get logs filtered by category."""
        if category in st.session_state.log_categories:
            return st.session_state.log_categories[category]
        return []
    
    def get_all_logs(self) -> List[str]:
        """Get all logs as formatted strings."""
        return st.session_state.log
    
    def clear_logs(self) -> None:
        """Clear all logs from session state."""
        st.session_state.log = []
        st.session_state.log_categories = {
            'user_action': [],
            'api_call': [],
            'error': [],
            'performance': []
        }

# Performance monitoring decorator
def performance_logger(logger: AppLogger, operation_name: Optional[str] = None):
    """Decorator to log performance metrics for a function."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Use function name if operation_name not provided
                op_name = operation_name or func.__name__
                
                # Log performance
                logger.log_performance(op_name, duration_ms)
                
                return result
            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Use function name if operation_name not provided
                op_name = operation_name or func.__name__
                
                # Log performance and error
                logger.log_performance(op_name, duration_ms, {'error': True})
                logger.log_error(f"Error in {op_name}", e)
                
                # Re-raise the exception
                raise
        return wrapper
    return decorator

# Create a singleton instance
app_logger = AppLogger() 