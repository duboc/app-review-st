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

import os
os.environ['GRPC_PYTHON_BUILD_SYSTEM_OPENSSL'] = '1'
os.environ['GRPC_PYTHON_BUILD_SYSTEM_ZLIB'] = '1'

import streamlit as st
import pandas as pd
from google_play_scraper import Sort, reviews, reviews_all
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from src.analysis_tab import render_analysis_tab
import json
from src.prompts import get_prompt_by_number

def scrape_reviews(app_id, reviews_count, language, country):
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    if language == "All":
        language = ""
    if country == "All":
        country = ""

    result, _ = reviews(
        app_id,
        lang=language,
        country=country,
        sort=Sort.NEWEST,
        count=reviews_count,
    )

    df = pd.DataFrame(result)
    if len(df) > 0:
        # Remove user names for confidentiality
        df = df.drop('userName', axis=1)
        df = df.drop('userImage', axis=1)
        
        # Save to CSV in data directory
        csv_path = data_dir / f"{app_id}_reviews.csv"
        df.to_csv(csv_path, index=False)
        
    return df

def log_action(action):
    if 'log' not in st.session_state:
        st.session_state.log = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.log.append(f"{timestamp}: {action}")



def main():
    st.set_page_config(
        page_title="Google Play Store Review Scraper & Analyzer",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Add sidebar with language selector first, then instructions
    with st.sidebar:
        st.subheader("🌐 Analysis Settings")
        selected_language = st.selectbox(
            "Output Language",
            options=["English", "Portuguese", "Spanish", "Japanese"],
            key="analysis_language"
        )
        
        # Map full names to language codes
        language_map = {
            "English": "en",
            "Portuguese": "pt",
            "Spanish": "es",
            "Japanese": "ja"
        }
        
        st.divider()  # Add divider after language selection
        
        st.markdown("""
        # 📱 How to Use
        
        Follow these steps to analyze app reviews:
        
        ### 1. Scrape Reviews 🔍
        - Enter the app ID from Play Store URL
        - Select number of reviews to fetch
        - Choose language and country filters
        - Click "Scrape Reviews"
        
        ### 2. View Results 📊
        - Check scraped reviews in Results tab
        - Download data as CSV if needed
        
        ### 3. Analyze Data 📈
        - Use Analysis tab for sentiment analysis
        - View detailed breakdowns and insights
        
        ### 4. Compare Versions 🔄
        - See sentiment across app versions
        - Identify trends and patterns
        
        ### 5. Additional Features
        - Check Sample Prompts for analysis examples
        - View activity log for history
        
        ### 📝 Note
        The app ID can be found in the Play Store URL:
        ```
        play.google.com/store/apps/details?id=com.example.app
                                            ↑
                                         App ID
        ```
        """)
        
        # Add a divider
        st.divider()
        
        # Add some metadata
        st.markdown("""
        ### About
        This tool helps analyze Google Play Store reviews using:
        - Automated scraping
        - Sentiment analysis
        - Version comparison
        - Spam detection
        
        
        """)

    # Add custom CSS with Material Design colors
    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
        }
        /* Title styling */
        .main-title {
            font-size: 2rem;
            font-weight: 600;
            color: #202124;
            padding: 1rem 0 2rem 0;
        }
        /* Tab styling */
        .stTabs {
            background-color: #ffffff;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: #f8f9fa;
            padding: 1rem 1rem 0 1rem;
            border-bottom: 1px solid #dadce0;
            margin-bottom: 1rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 0 24px;
            color: #5f6368;
            font-size: 1rem;
            font-weight: 500;
            background: white;
            border: none;
            border-radius: 4px 4px 0 0;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #1a73e8;
            background-color: rgba(26, 115, 232, 0.1);
        }
        .stTabs [aria-selected="true"] {
            color: #1a73e8 !important;
            background-color: #ffffff !important;
            border-radius: 4px 4px 0 0 !important;
            border-bottom: 3px solid #1a73e8 !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            display: none;
        }
        .stTabs [data-baseweb="tab-border"] {
            display: none;
        }
        /* Other Material styles */
        .stButton > button {
            background-color: #1a73e8;
            color: white;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        .stButton > button:hover {
            background-color: #1557b0;
        }
        .stSelectbox [data-baseweb="select"] {
            border-radius: 4px;
            border-color: #dadce0;
        }
        .stTextInput > div > div > input {
            border-radius: 4px;
            border-color: #dadce0;
        }
        .stNumberInput > div > div > input {
            border-radius: 4px;
            border-color: #dadce0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Add page title before tabs
    st.markdown('<h1 class="main-title">Google Play Store Review Analyzer</h1>', unsafe_allow_html=True)

    if 'results' not in st.session_state:
        st.session_state.results = {}
    if 'sentiment_results' not in st.session_state:
        st.session_state.sentiment_results = {}

    tabs = st.tabs([
        "🔍 Scraper",
        "📊 Results",
        "📈 Analysis",
        "🔄 Version Comparison",
        "📝 User Stories",
        "💡 Marketing",
        "💡 Sample Prompts",
        "📦 Artifacts",
        "📝 Log"
    ])

    with tabs[0]:
        st.markdown("""
            # 🔍 Google Play Store Review Scraper
            Extract and analyze user reviews from any app on the Google Play Store.
        """)
        
        # Single column layout with consistent spacing
        container = st.container()
        with container:
            app_id = st.text_input(
                "App ID:", 
                "org.supertuxkart.stk",
                help="Find this in the app's Play Store URL. Example: com.company.appname"
            )
            
            reviews_count = st.number_input(
                "Number of reviews:", 
                min_value=1, 
                max_value=10000, 
                value=1000,
                help="Maximum number of reviews to scrape"
            )
            
            language = st.selectbox(
                "Language:", 
                ["", "All", "en", "es", "fr", "de", "it", "pt"],
                help="Filter reviews by language"
            )
            
            country = st.selectbox(
                "Country:", 
                ["", "All", "us", "gb", "ca", "au", "in", "es", "fr", "de", "it", "br"],
                help="Filter reviews by country"
            )

            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            
            # Make the button more prominent
            if st.button("🚀 Scrape Reviews", type="primary", use_container_width=True):
                if app_id:
                    with st.spinner("Scraping reviews... This may take a while."):
                        df = scrape_reviews(app_id, reviews_count, language, country)

                    # Save results to session state
                    st.session_state.results[app_id] = {
                        'dataframe': df,
                        'language': language,
                        'country': country,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    if len(df) > 0:
                        st.success(f"Successfully scraped {len(df)} reviews!")

                        st.dataframe(df)

                        # Allow CSV download
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"{app_id}_reviews.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning(
                            "No reviews were scraped. Please check your inputs.")
                else:
                    st.error("Please enter an app ID.")
                    log_action("Attempted to scrape without entering an app ID")

    with tabs[1]:
        st.title("Scraping Results")
        if st.session_state.results:
            for app_id, result in st.session_state.results.items():
                st.subheader(f"App ID: {app_id}")
                st.write(f"Language: {result['language']}, Country: {result['country']}")
                st.write(f"Scraped on: {result['timestamp']}")
                st.dataframe(result['dataframe'])
                csv = result['dataframe'].to_csv(index=False)
                st.download_button(
                    label=f"Download CSV for {app_id}",
                    data=csv,
                    file_name=f"{app_id}_reviews.csv",
                    mime="text/csv",
                )
                st.divider()
        else:
            st.info("No results available. Use the Scraper tab to fetch reviews.")

    with tabs[2]:
        render_analysis_tab()

    with tabs[3]:
        st.title("Version Comparison")
        if st.session_state.results:
            for app_id, result in st.session_state.results.items():
                st.subheader(f"Analysis for {app_id}")
                
                # Create unique key for version comparison analysis
                analysis_key = f"{app_id}_prompt_6"
                
                if st.button("Analyze Versions", key=f"analyze_versions_{app_id}"):
                    try:
                        # Get the prompt text for version comparison
                        prompt = get_prompt_by_number(6)
                        csv_data = result['dataframe'].to_csv(index=False)
                        full_prompt = f"{prompt}\n\nData:\n{csv_data}"
                        
                        with st.spinner("Analyzing versions..."):
                            response = st.session_state.gemini_client.generate_content(full_prompt)
                            
                            # Save analysis to history
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if analysis_key not in st.session_state.analysis_history:
                                st.session_state.analysis_history[analysis_key] = {}
                            st.session_state.analysis_history[analysis_key][timestamp] = response
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                
                # Show analysis in subtabs if available
                if analysis_key in st.session_state.analysis_history:
                    latest_timestamp = max(st.session_state.analysis_history[analysis_key].keys())
                    analysis = st.session_state.analysis_history[analysis_key][latest_timestamp]
                    
                    try:
                        # Clean up the response
                        clean_response = analysis.strip()
                        if clean_response.startswith('```json'):
                            clean_response = clean_response.split('```json')[1]
                        if clean_response.endswith('```'):
                            clean_response = clean_response.rsplit('```', 1)[0]
                        
                        data = json.loads(clean_response)
                        
                        # Create subtabs
                        raw_tab, viz_tab = st.tabs(["Raw JSON", "Visualization"])
                        
                        # Raw JSON tab
                        with raw_tab:
                            st.json(data)
                        
                        # Visualization tab
                        with viz_tab:
                            # Create three columns for the main metrics
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                # Version History Table
                                st.subheader("Version History")
                                df = pd.DataFrame(data['historico_versoes'])
                                st.dataframe(
                                    df[['versao_aplicativo', 'sentimento', 'score_sentimento_positivo']]
                                    .rename(columns={
                                        'versao_aplicativo': 'Version',
                                        'sentimento': 'Sentiment',
                                        'score_sentimento_positivo': 'Score'
                                    })
                                )
                            
                            with col2:
                                # Best Version
                                st.success("Best Version")
                                st.write(f"Version: {data['melhor_sentimento']['versao_aplicativo']}")
                                st.write(data['melhor_sentimento']['resumo_sentimento'])
                            
                            with col3:
                                # Worst Version
                                st.error("Worst Version")
                                st.write(f"Version: {data['pior_sentimento']['versao_aplicativo']}")
                                st.write(data['pior_sentimento']['resumo_sentimento'])
                            
                            # Sentiment Score Chart
                            st.subheader("Sentiment Scores by Version")
                            chart_data = pd.DataFrame({
                                'Version': df['versao_aplicativo'],
                                'Score': df['score_sentimento_positivo']
                            }).set_index('Version')
                            st.bar_chart(chart_data)
                            
                            # Detailed Analysis Section
                            st.subheader("Detailed Version Analysis")
                            for version in data['historico_versoes']:
                                with st.container():
                                    col1, col2 = st.columns([1, 3])
                                    with col1:
                                        st.markdown(f"**Version {version['versao_aplicativo']}**")
                                        st.markdown(f"*{version['sentimento'].title()}*")
                                        st.markdown(f"**Score:** {version['score_sentimento_positivo']}")
                                    with col2:
                                        st.markdown(version['resumo_sentimento'])
                                st.divider()
                                
                    except json.JSONDecodeError as e:
                        st.warning(f"Could not parse JSON from response: {str(e)}")
                    except Exception as e:
                        st.error(f"Error processing visualization: {str(e)}")
        else:
            st.info("No data available for version comparison. Please scrape some reviews first.")

    with tabs[4]:
        st.title("User Stories")
        if st.session_state.results:
            for app_id, result in st.session_state.results.items():
                st.subheader(f"Generate User Stories for {app_id}")
                
                # Create unique keys for analysis
                detailed_analysis_key = f"{app_id}_prompt_2"
                user_story_key = f"{app_id}_prompt_9"
                
                if st.button("Generate User Stories", key=f"generate_stories_{app_id}"):
                    try:
                        # Step 1: Get detailed analysis first
                        detailed_prompt = get_prompt_by_number(2)
                        csv_data = result['dataframe'].to_csv(index=False)
                        detailed_analysis_prompt = f"{detailed_prompt}\n\nData:\n{csv_data}"
                        
                        with st.spinner("Performing detailed analysis..."):
                            detailed_response = st.session_state.gemini_client.generate_content(detailed_analysis_prompt)
                            detailed_text = str(detailed_response)
                        
                        # Step 2: Generate user stories based on the analysis
                        user_story_prompt = get_prompt_by_number(9)
                        story_prompt = f"{user_story_prompt}\n\nAnalysis:\n{detailed_text}"
                        
                        with st.spinner("Generating user stories..."):
                            story_response = st.session_state.gemini_client.generate_content(story_prompt)
                            story_text = str(story_response)
                            
                            # Clean up the response text to extract JSON
                            try:
                                # Remove markdown code blocks and clean the JSON string
                                if '```json' in story_text:
                                    json_content = story_text.split('```json')[1].split('```')[0]
                                elif '```' in story_text:
                                    json_content = story_text.split('```')[1].split('```')[0]
                                else:
                                    json_content = story_text
                                
                                # Clean up any remaining whitespace and validate JSON
                                json_content = json_content.strip()
                                
                                # Debug output
                                ##st.write("### Cleaned JSON content:")
                                ##st.code(json_content)
                                
                                stories_data = json.loads(json_content)
                                
                                # Display the results in tabs
                                overview_tab, details_tab, raw_tab = st.tabs(["Overview", "Stories by Theme", "Raw JSON"])
                                
                                with overview_tab:
                                    if 'summary' in stories_data:
                                        st.subheader("Summary")
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Total Stories", stories_data['summary'].get('total_stories', 0))
                                        with col2:
                                            st.metric("Total Story Points", stories_data['summary'].get('total_story_points', 0))
                                        with col3:
                                            st.json(stories_data['summary'].get('theme_breakdown', {}))
                                
                                with details_tab:
                                    if 'themes' in stories_data:
                                        for theme in stories_data['themes']:
                                            st.subheader(f"📌 {theme.get('name', 'Unnamed Theme')}")
                                            for story in theme.get('stories', []):
                                                with st.expander(f"{story.get('as_a', '')} - {story.get('i_want', '')[:50]}..."):
                                                    st.markdown(f"**As a** {story.get('as_a', '')}")
                                                    st.markdown(f"**I want** {story.get('i_want', '')}")
                                                    st.markdown(f"**So that** {story.get('so_that', '')}")
                                                    st.markdown("#### Acceptance Criteria")
                                                    for criteria in story.get('acceptance_criteria', []):
                                                        st.markdown(f"- {criteria}")
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        st.metric("Story Points", story.get('story_points', 0))
                                                    with col2:
                                                        st.metric("Priority", story.get('priority', 'Medium'))
                                
                                with raw_tab:
                                    st.json(stories_data)
                                
                            except json.JSONDecodeError as e:
                                st.error(f"Error parsing JSON response: {str(e)}")
                                st.write("### Raw response from model:")
                                st.code(story_text)
                                st.write("### Length of response:", len(story_text))
                                
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.write("Please try again or contact support if the error persists.")
        else:
            st.info("No data available for user story generation. Please scrape some reviews first.")

    with tabs[5]:
        st.title("Marketing Campaign Generation")
        if st.session_state.results:
            for app_id, result in st.session_state.results.items():
                st.subheader(f"Generate Marketing Campaign for {app_id}")
                
                # Create unique keys for analysis
                detailed_analysis_key = f"{app_id}_prompt_2"
                marketing_key = f"{app_id}_prompt_10"
                
                if st.button("Generate Marketing Campaign", key=f"generate_marketing_{app_id}"):
                    try:
                        # Step 1: Get detailed analysis first
                        detailed_prompt = get_prompt_by_number(2)
                        csv_data = result['dataframe'].to_csv(index=False)
                        detailed_analysis_prompt = f"{detailed_prompt}\n\nData:\n{csv_data}"
                        
                        with st.spinner("Performing detailed analysis..."):
                            detailed_response = st.session_state.gemini_client.generate_content(detailed_analysis_prompt)
                            detailed_text = str(detailed_response)
                        
                        # Step 2: Generate marketing campaign based on the analysis
                        marketing_prompt = get_prompt_by_number(10)
                        campaign_prompt = f"{marketing_prompt}\n\nAnalysis:\n{detailed_text}"
                        
                        with st.spinner("Generating marketing campaign..."):
                            campaign_response = st.session_state.gemini_client.generate_content(campaign_prompt)
                            campaign_text = str(campaign_response)
                            
                            try:
                                # Clean up the response text to extract JSON
                                if '```json' in campaign_text:
                                    json_content = campaign_text.split('```json')[1].split('```')[0]
                                elif '```' in campaign_text:
                                    json_content = campaign_text.split('```')[1].split('```')[0]
                                else:
                                    json_content = campaign_text
                                
                                # Clean up any remaining whitespace
                                json_content = json_content.strip()
                                
                                # Parse the JSON
                                campaign_data = json.loads(json_content)
                                
                                # Display results in tabs
                                overview_tab, strategies_tab, raw_tab = st.tabs(["Campaign Overview", "Strategies", "Raw JSON"])
                                
                                with overview_tab:
                                    st.header("Campaign Overview")
                                    st.subheader(campaign_data.get('campaign_name', 'Unnamed Campaign'))
                                    
                                    # Display key campaign information
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Duration", campaign_data.get('campaign_duration', 'N/A'))
                                    with col2:
                                        st.metric("Budget", campaign_data.get('campaign_budget', 'N/A'))
                                    with col3:
                                        st.metric("Target Audience", campaign_data.get('target_audience', 'N/A'))
                                    
                                    st.markdown("### Overall Message")
                                    st.info(campaign_data.get('overall_message', 'No message provided'))
                                
                                with strategies_tab:
                                    st.header("Campaign Strategies")
                                    for strategy in campaign_data.get('campaign_strategies', []):
                                        with st.expander(f"📌 {strategy.get('strategy_name', 'Unnamed Strategy')}"):
                                            st.markdown(f"**Description:** {strategy.get('description', 'No description')}")
                                            
                                            st.markdown("### Tactics")
                                            for tactic in strategy.get('tactics', []):
                                                st.markdown(f"""
                                                **{tactic.get('tactic_name', 'Unnamed Tactic')}**
                                                - Description: {tactic.get('description', 'No description')}
                                                - Platforms: {', '.join(tactic.get('platforms', []))}
                                                - Estimated Cost: {tactic.get('estimated_cost', 'N/A')}
                                                """)
                                            
                                            st.markdown("### Measurement Metrics")
                                            for metric in strategy.get('measurement_metrics', []):
                                                st.markdown(f"- {metric}")
                                
                                with raw_tab:
                                    st.json(campaign_data)
                                
                            except json.JSONDecodeError as e:
                                st.error(f"Error parsing JSON response: {str(e)}")
                                st.write("### Raw response from model:")
                                st.code(campaign_text)
                                st.write("### Length of response:", len(campaign_text))
                                
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.write("Please try again or contact support if the error persists.")
        else:
            st.info("No data available for marketing campaign generation. Please scrape some reviews first.")

    with tabs[6]:
        st.title("Sample Prompts")
        
        # Get all prompt files from the prompts directory
        prompts_dir = Path('prompts')
        prompt_files = sorted([f for f in prompts_dir.glob('[0-9][0-9]*.md')])
        
        for prompt_file in prompt_files:
            try:
                # Extract prompt number from filename (assuming format like "01_name.md")
                prompt_num = prompt_file.stem.split('_')[0]
                
                # Read prompt content
                prompt_content = prompt_file.read_text()
                
                # Create expandable section for each prompt
                with st.expander(f"Prompt {prompt_num}"):
                    st.markdown(prompt_content)
                    
            except Exception as e:
                st.error(f"Error loading prompt {prompt_file}: {str(e)}")

    with tabs[7]:
        st.title("Artifacts")
        st.link_button("Game Video Download", 
                       "https://storage.googleapis.com/damadei-public-bucket/supertux.mp4")

    with tabs[8]:
        st.title("Activity Log")
        if 'log' in st.session_state and st.session_state.log:
            for entry in reversed(st.session_state.log):
                st.text(entry)
        else:
            st.info("No activity logged yet.")

if __name__ == "__main__":
    main()