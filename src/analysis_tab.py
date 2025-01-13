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

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from .gemini_client import GeminiRegionClient
from .prompts import get_prompt_by_number
import json
from pathlib import Path

def render_analysis_tab():
    st.title("Analysis")
    
    if 'gemini_client' not in st.session_state:
        st.session_state.gemini_client = GeminiRegionClient()
    
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = {}
    
    # Create subtabs for each prompt
    subtabs = st.tabs(["General Sentiment", "Detailed Analysis", "Problems & Suggestions", 
                      "Sentiment Factors", "Spam Detection", "Gameplay Analysis"])
    
    for i, tab in enumerate(subtabs, 1):
        with tab:
            if st.session_state.results:
                for app_id, result in st.session_state.results.items():
                    st.subheader(f"Analysis for {app_id}")
                    
                    # Create unique key for this analysis
                    analysis_key = f"{app_id}_prompt_{i}"
                    
                    # Show analysis history in expanders
                    if analysis_key in st.session_state.analysis_history:
                        for timestamp, analysis in st.session_state.analysis_history[analysis_key].items():
                            with st.expander(f"Analysis from {timestamp}", expanded=False):
                                st.markdown(analysis)
                    
                    if i == 5:  # Spam Detection
                        if st.button(f"Analyze with Prompt {i}", key=f"analyze_btn_{i}_{app_id}"):
                            with st.spinner("Analyzing reviews for spam..."):
                                # Get both prompts
                                text_prompt = get_prompt_by_number(5)
                                json_prompt = get_prompt_by_number(8)
                                
                                # Convert DataFrame to CSV string
                                csv_data = result['dataframe'].to_csv(index=False)
                                
                                # Add language instruction to both prompts
                                language_instruction = f"\nPlease provide the analysis in {st.session_state.analysis_language}."
                                text_prompt = text_prompt + language_instruction
                                json_prompt = json_prompt + language_instruction
                                
                                text_full_prompt = f"{text_prompt}\n\nData:\n{csv_data}"
                                json_full_prompt = f"{json_prompt}\n\nData:\n{csv_data}"
                                
                                with st.spinner(f"Analyzing reviews for spam in {st.session_state.analysis_language}..."):
                                    text_response = st.session_state.gemini_client.generate_content(text_full_prompt)
                                    json_response = st.session_state.gemini_client.generate_content(json_full_prompt)
                                
                                # Save analysis to history
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                if analysis_key not in st.session_state.analysis_history:
                                    st.session_state.analysis_history[analysis_key] = {}
                                
                                # Store both responses
                                st.session_state.analysis_history[analysis_key][timestamp] = {
                                    'text': text_response,
                                    'json': json_response
                                }
                                
                                # Show the new analysis in three columns
                                with st.expander(f"Analysis from {timestamp}", expanded=True):
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.markdown("## Text Analysis")
                                        st.markdown(text_response)
                                    
                                    with col2:
                                        st.markdown("## Data Analysis")
                                        try:
                                            # Clean up the JSON response
                                            clean_response = json_response.strip()
                                            if '```json' in clean_response:
                                                clean_response = clean_response.split('```json')[1].split('```')[0]
                                            elif '```' in clean_response:
                                                clean_response = clean_response.split('```')[1].split('```')[0]
                                            
                                            data = json.loads(clean_response.strip())
                                            
                                            # Display key metrics
                                            st.markdown("### Key Metrics")
                                            metrics = data.get('overall_quality_metrics', {})
                                            mc1, mc2, mc3 = st.columns(3)
                                            with mc1:
                                                st.metric("Authenticity Score", f"{metrics.get('authenticity_score', 0)*100:.1f}%")
                                            with mc2:
                                                st.metric("Spam Percentage", f"{metrics.get('spam_percentage', 0):.1f}%")
                                            with mc3:
                                                st.metric("Quality Score", f"{metrics.get('average_quality_score', 0)*100:.1f}%")
                                            
                                            # Rating distribution chart
                                            st.markdown("### Rating Distribution")
                                            rating_dist = data.get('statistical_analysis', {}).get('rating_distribution', {})
                                            ratings_df = pd.DataFrame([
                                                {'Rating': f"{stars} Stars", 'Count': rating_dist.get(f'{stars}_star', {}).get('count', 0)}
                                                for stars in range(1, 6)
                                            ])
                                            st.bar_chart(ratings_df.set_index('Rating'))
                                            
                                            # Review length distribution
                                            st.markdown("### Review Length Distribution")
                                            length_dist = data.get('statistical_analysis', {}).get('review_length', {}).get('distribution', {})
                                            length_df = pd.DataFrame([
                                                {'Length': k, 'Count': v.get('count', 0)}
                                                for k, v in length_dist.items()
                                            ])
                                            st.bar_chart(length_df.set_index('Length'))
                                            
                                            # Top keywords
                                            st.markdown("### Most Common Keywords")
                                            keywords = data.get('statistical_analysis', {}).get('keyword_frequency', {}).get('top_keywords', [])
                                            if keywords:
                                                keywords_df = pd.DataFrame(keywords)
                                                st.bar_chart(keywords_df.set_index('word'))
                                            
                                        except Exception as e:
                                            st.error(f"Error processing JSON data: {str(e)}")
                                            st.text(json_response)
                                    
                                    with col3:
                                        st.markdown("## Raw JSON")
                                        try:
                                            st.json(data)
                                        except Exception as e:
                                            st.error(f"Error displaying raw JSON: {str(e)}")
                                            st.text(json_response)
                    else:
                        if st.button(f"Analyze with Prompt {i}", key=f"analyze_btn_{i}_{app_id}"):
                            try:
                                # Get the prompt text
                                prompt = get_prompt_by_number(i)
                                
                                # Add language instruction to prompt
                                language_instruction = f"\nPlease provide the analysis in {st.session_state.analysis_language}."
                                prompt = prompt + language_instruction
                                
                                # Convert DataFrame to CSV string
                                csv_data = result['dataframe'].to_csv(index=False)
                                
                                # Combine prompt with data
                                full_prompt = f"{prompt}\n\nData:\n{csv_data}"
                                
                                with st.spinner(f"Analyzing reviews in {st.session_state.analysis_language}..."):
                                    response = st.session_state.gemini_client.generate_content(full_prompt)
                                    
                                    # Save analysis to history with language info
                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    if analysis_key not in st.session_state.analysis_history:
                                        st.session_state.analysis_history[analysis_key] = {}
                                    st.session_state.analysis_history[analysis_key][timestamp] = {
                                        'response': response,
                                        'language': st.session_state.analysis_language
                                    }
                                    
                                    # Show the new analysis in an expander
                                    with st.expander(f"Analysis from {timestamp} ({st.session_state.analysis_language})", expanded=True):
                                        st.markdown(response)
                                    
                            except Exception as e:
                                st.error(f"Error during analysis: {str(e)}")
            else:
                st.info("No data available for analysis. Please scrape some reviews first.")
 