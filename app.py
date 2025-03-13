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
from src.analysis_tab import render_analysis_tab, get_finish_reason_text
import json
from src.prompts import get_prompt_by_number
from src.config import Config
from src.logger import app_logger, performance_logger
import time

# Initialize logging
logger = Config.setup_logging()

@performance_logger(app_logger, "scrape_reviews")
def scrape_reviews(app_id, reviews_count, language, country):
    """Scrape reviews from Google Play Store with performance tracking."""
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    if language == "All":
        language = ""
    if country == "All":
        country = ""

    # Log API call
    app_logger.log_api_call(
        api_name="google_play_scraper.reviews",
        params={
            "app_id": app_id,
            "lang": language,
            "country": country,
            "count": reviews_count
        }
    )

    try:
        start_time = time.time()
        result, _ = reviews(
            app_id,
            lang=language,
            country=country,
            sort=Sort.NEWEST,
            count=reviews_count,
        )
        duration_ms = (time.time() - start_time) * 1000

        # Log successful API call
        app_logger.log_api_call(
            api_name="google_play_scraper.reviews",
            params={"app_id": app_id},
            response_status="success",
            duration_ms=duration_ms
        )

        df = pd.DataFrame(result)
        if len(df) > 0:
            # Remove user names for confidentiality
            df = df.drop('userName', axis=1)
            df = df.drop('userImage', axis=1)
            
            # Save to CSV in data directory
            csv_path = data_dir / f"{app_id}_reviews.csv"
            df.to_csv(csv_path, index=False)
            
            # Log successful saving
            app_logger.log_user_action(
                f"Saved {len(df)} reviews for {app_id} to CSV",
                {"file_path": str(csv_path), "row_count": len(df)}
            )
            
        return df
    except Exception as e:
        # Log error
        app_logger.log_error(
            f"Error scraping reviews for {app_id}",
            exception=e,
            context={"app_id": app_id, "lang": language, "country": country}
        )
        raise

def main():
    # Configure Streamlit page
    st.set_page_config(
        page_title="Google Play Store Review Scraper & Analyzer",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state for logging
    if 'log' not in st.session_state:
        st.session_state.log = []
    
    if 'log_categories' not in st.session_state:
        st.session_state.log_categories = {
            'user_action': [],
            'api_call': [],
            'error': [],
            'performance': []
        }
    
    # Log application start
    app_logger.log_user_action("Application started", {"session_id": app_logger.session_id})

    # Add sidebar with language selector first, then instructions
    with st.sidebar:
        st.subheader("🌐 Analysis Settings")
        
        # Add session info and user controls
        with st.expander("📊 Session Info", expanded=False):
            st.info(f"Session ID: {app_logger.session_id}")
            
            if st.button("Clear Session Data", key="clear_session"):
                # Clear session data
                for key in list(st.session_state.keys()):
                    if key not in ['log', 'log_categories']:
                        del st.session_state[key]
                app_logger.log_user_action("Cleared session data")
                st.success("Session data cleared!")
            
            # Add theme selector
            theme = st.selectbox(
                "UI Theme",
                options=["Light", "Dark", "Auto"],
                key="ui_theme",
                help="Select the UI theme for the application"
            )
            
            # Log theme change if it happens
            if 'prev_theme' not in st.session_state:
                st.session_state.prev_theme = theme
                app_logger.log_user_action(f"Set UI theme to {theme}")
            elif st.session_state.prev_theme != theme:
                app_logger.log_user_action(f"Changed UI theme from {st.session_state.prev_theme} to {theme}")
                st.session_state.prev_theme = theme
        
        selected_language = st.selectbox(
            "Output Language",
            options=["English", "Portuguese", "Spanish", "Japanese"],
            key="analysis_language"
        )
        
        # Log language change if it happens
        if 'prev_language' not in st.session_state:
            st.session_state.prev_language = selected_language
            app_logger.log_user_action(f"Set output language to {selected_language}")
        elif st.session_state.prev_language != selected_language:
            app_logger.log_user_action(f"Changed output language from {st.session_state.prev_language} to {selected_language}")
            st.session_state.prev_language = selected_language
        
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

    # Add custom CSS with Material Design colors and improved UI feedback
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
            transition: all 0.3s ease-in-out;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #1a73e8;
            background-color: rgba(26, 115, 232, 0.1);
            transform: translateY(-2px);
        }
        .stTabs [aria-selected="true"] {
            color: #1a73e8 !important;
            background-color: #ffffff !important;
            border-radius: 4px 4px 0 0 !important;
            border-bottom: 3px solid #1a73e8 !important;
            transform: translateY(-3px) !important;
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
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #1557b0;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stButton > button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stSelectbox [data-baseweb="select"] {
            border-radius: 4px;
            border-color: #dadce0;
            transition: all 0.2s ease-in-out;
        }
        .stSelectbox [data-baseweb="select"]:focus-within {
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
        }
        .stTextInput > div > div > input {
            border-radius: 4px;
            border-color: #dadce0;
            transition: all 0.2s ease-in-out;
        }
        .stTextInput > div > div > input:focus {
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
        }
        .stNumberInput > div > div > input {
            border-radius: 4px;
            border-color: #dadce0;
            transition: all 0.2s ease-in-out;
        }
        .stNumberInput > div > div > input:focus {
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
        }
        /* Metric styling */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a73e8;
        }
        /* Success message styling */
        .success-message {
            background-color: #e6f4ea;
            color: #137333;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            border-left: 4px solid #137333;
        }
        /* Error message styling */
        .error-message {
            background-color: #fce8e6;
            color: #c5221f;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            border-left: 4px solid #c5221f;
        }
        /* Loading animation */
        .loading-animation {
            display: inline-block;
            position: relative;
            width: 80px;
            height: 80px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Add page title before tabs
    st.markdown('<h1 class="main-title">Google Play Store Review Analyzer</h1>', unsafe_allow_html=True)

    if 'results' not in st.session_state:
        st.session_state.results = {}
    if 'sentiment_results' not in st.session_state:
        st.session_state.sentiment_results = {}
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = {}
    if 'gemini_client' not in st.session_state:
        from src.gemini_client import GeminiRegionClient
        st.session_state.gemini_client = GeminiRegionClient()
        app_logger.log_user_action("Initialized Gemini client")

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
                ["", "All", "en", "es", "fr", "de", "it", "pt", "id", "th", "ms", "zh-CN", "tl"],
                index=1,
                help="Filter reviews by language. Available languages include English (en), Spanish (es), French (fr), "
                     "German (de), Italian (it), Portuguese (pt), Indonesian (id), Thai (th), Malay (ms), "
                     "Simplified Chinese (zh-CN), and Tagalog (tl)"
            )
            
            # Country mapping dictionary
            country_options = {
                "": "",
                "All": "All",
                "United States": "us",
                "United Kingdom": "gb",
                "Canada": "ca",
                "Australia": "au",
                "India": "in",
                "Spain": "es",
                "France": "fr",
                "Germany": "de",
                "Italy": "it",
                "Brazil": "br",
                "Indonesia": "id",
                "Thailand": "th",
                "Malaysia": "my",
                "Singapore": "sg",
                "Philippines": "ph"
            }
            
            selected_country_name = st.selectbox(
                "Country:", 
                list(country_options.keys()),
                help="Filter reviews by country. Includes major markets across North America, Europe, "
                     "and Asia-Pacific regions."
            )
            
            # Convert selected country name to code for the API
            country = country_options[selected_country_name]

            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            
            # Make the button more prominent
            scraper_col1, scraper_col2 = st.columns([3, 1])
            with scraper_col1:
                if st.button("🚀 Scrape Reviews", type="primary", use_container_width=True):
                    if app_id:
                        # Log user action
                        app_logger.log_user_action(
                            f"Started scraping reviews for {app_id}",
                            {
                                "app_id": app_id,
                                "reviews_count": reviews_count,
                                "language": language,
                                "country": country
                            }
                        )
                        
                        with st.spinner("Scraping reviews... This may take a while."):
                            try:
                                df = scrape_reviews(app_id, reviews_count, language, country)

                                # Save results to session state
                                st.session_state.results[app_id] = {
                                    'dataframe': df,
                                    'language': language,
                                    'country': country,
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }

                                if len(df) > 0:
                                    # Log success
                                    app_logger.log_user_action(
                                        f"Successfully scraped {len(df)} reviews for {app_id}",
                                        {"row_count": len(df)}
                                    )
                                    
                                    st.success(f"✅ Successfully scraped {len(df)} reviews!")

                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        st.dataframe(df, height=400)
                                    
                                    with col2:
                                        st.metric("Total Reviews", len(df))
                                        
                                        # Get rating distribution
                                        if 'score' in df.columns:
                                            avg_rating = df['score'].mean()
                                            st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
                                            
                                            # Count reviews by stars
                                            rating_counts = df['score'].value_counts().sort_index()
                                            
                                            # Display in expandable section
                                            with st.expander("Rating Distribution"):
                                                for stars, count in rating_counts.items():
                                                    st.write(f"{int(stars)} ⭐: {count} reviews")

                                    # Allow CSV download
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        label="Download CSV",
                                        data=csv,
                                        file_name=f"{app_id}_reviews.csv",
                                        mime="text/csv",
                                    )
                                else:
                                    # Log warning
                                    app_logger.log_user_action(
                                        f"No reviews found for {app_id}",
                                        {"language": language, "country": country}
                                    )
                                    
                                    st.warning(
                                        "No reviews were scraped. Please check your inputs.")
                            except Exception as e:
                                # Error is already logged in the scrape_reviews function
                                st.error(f"Error scraping reviews: {str(e)}")
                    else:
                        # Log error
                        app_logger.log_user_action("Attempted to scrape without entering an app ID")
                        st.error("Please enter an app ID.")
            
            with scraper_col2:
                # Add a sample app button
                if st.button("📱 Use Example", help="Use a sample app ID", use_container_width=True):
                    # This is handled by Streamlit's state management - we just log it
                    app_logger.log_user_action("Used example app ID", {"app_id": "org.supertuxkart.stk"})
                    st.info("Using example app: SuperTuxKart")

    with tabs[1]:
        st.title("Scraping Results")
        if st.session_state.results:
            for app_id, result in st.session_state.results.items():
                st.subheader(f"App ID: {app_id}")
                
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                with metrics_col1:
                    st.metric("Language", result['language'] if result['language'] else "All")
                with metrics_col2:
                    st.metric("Country", result['country'] if result['country'] else "All")
                with metrics_col3:
                    st.metric("Scraped on", result['timestamp'])
                
                # Create view toggle
                view_type = st.radio(
                    "View Type",
                    ["Table View", "Card View"],
                    horizontal=True,
                    key=f"view_type_{app_id}"
                )
                
                # Log user choice
                if f"prev_view_{app_id}" not in st.session_state:
                    st.session_state[f"prev_view_{app_id}"] = view_type
                    app_logger.log_user_action(f"Set view type to {view_type} for {app_id}")
                elif st.session_state[f"prev_view_{app_id}"] != view_type:
                    app_logger.log_user_action(f"Changed view type from {st.session_state[f'prev_view_{app_id}']} to {view_type} for {app_id}")
                    st.session_state[f"prev_view_{app_id}"] = view_type
                
                if view_type == "Table View":
                    st.dataframe(result['dataframe'], height=400)
                else:  # Card View
                    # Create a card for each review (limited to 10 for performance)
                    df = result['dataframe'].head(10)
                    for _, row in df.iterrows():
                        with st.container():
                            st.markdown(f"""
                            <div style="padding: 1rem; border-radius: 8px; border: 1px solid #dadce0; margin-bottom: 1rem;">
                                <h3>{"⭐" * int(row['score'])}</h3>
                                <p><strong>Review:</strong> {row['content']}</p>
                                <p><strong>App Version:</strong> {row['reviewCreatedVersion']}</p>
                                <p><small>Posted on: {row['at']}</small></p>
                            </div>
                            """, unsafe_allow_html=True)
                
                csv = result['dataframe'].to_csv(index=False)
                st.download_button(
                    label=f"Download CSV for {app_id}",
                    data=csv,
                    file_name=f"{app_id}_reviews.csv",
                    mime="text/csv",
                    key=f"download_{app_id}"
                )
                
                # Log download action (in a real scenario, the button's on_click would be used)
                if st.button(f"🗑️ Remove Dataset", key=f"remove_{app_id}"):
                    app_logger.log_user_action(f"Removed dataset for {app_id}")
                    del st.session_state.results[app_id]
                    st.rerun()
                
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
                
                # Add metadata toggle
                show_metadata = st.toggle("Show Generation Metadata", value=True, key=f"version_metadata_{app_id}")
                
                if st.button("Analyze Versions", key=f"analyze_versions_{app_id}"):
                    try:
                        # Log user action
                        app_logger.log_user_action(f"Started version analysis for {app_id}")
                        
                        # Get the prompt text for version comparison
                        prompt = get_prompt_by_number(6)
                        
                        # Add language instruction to prompt
                        language_instruction = f"\nPlease provide the analysis in {st.session_state.analysis_language}."
                        prompt = prompt + language_instruction
                        
                        csv_data = result['dataframe'].to_csv(index=False)
                        full_prompt = f"{prompt}\n\nData:\n{csv_data}"
                        
                        # Log API call
                        app_logger.log_api_call(
                            api_name="gemini_client.generate_content",
                            params={"prompt_type": "version_comparison"}
                        )
                        
                        with st.spinner(f"Analyzing versions in {st.session_state.analysis_language}..."):
                            start_time = time.time()
                            response = st.session_state.gemini_client.generate_content(
                                full_prompt,
                                return_full_response=show_metadata
                            )
                            
                            # Extract response and metadata
                            if isinstance(response, dict):
                                response_text = response.get("text", "")
                                finish_reason = response.get("finish_reason", "")
                                response_metadata = response.get("metadata", {})
                            else:
                                response_text = response
                                finish_reason = ""
                                response_metadata = {}
                                
                            duration_ms = (time.time() - start_time) * 1000

                            # Check for incomplete generation - using direct finish reason first if available
                            is_truncated = False
                            if finish_reason:
                                is_truncated = "completed normally" not in finish_reason.lower()
                            elif response_metadata and "candidates" in response_metadata and response_metadata["candidates"]:
                                # Fallback to older format if direct finish reason not available
                                candidate = response_metadata["candidates"][0]
                                finish_reason = get_finish_reason_text(candidate.get("finish_reason", "UNKNOWN"))
                                is_truncated = candidate.get("finish_reason") != "STOP"

                            # Log successful API call with metadata
                            app_logger.log_api_call(
                                api_name="gemini_client.generate_content",
                                params={
                                    "prompt_type": "version_comparison",
                                    "finish_reason": finish_reason,
                                    "is_truncated": is_truncated
                                },
                                response_status="success",
                                duration_ms=duration_ms
                            )
                            
                            # Save analysis to history with language info, finish reason, and metadata
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if analysis_key not in st.session_state.analysis_history:
                                st.session_state.analysis_history[analysis_key] = {}
                                
                            st.session_state.analysis_history[analysis_key][timestamp] = {
                                'response': response_text,
                                'finish_reason': finish_reason,
                                'metadata': response_metadata if response_metadata else None,
                                'language': st.session_state.analysis_language
                            }
                            
                            # Log successful analysis with metadata
                            app_logger.log_user_action(
                                f"Completed version analysis for {app_id}",
                                {
                                    "language": st.session_state.analysis_language, 
                                    "duration_ms": duration_ms,
                                    "finish_reason": finish_reason,
                                    "is_truncated": is_truncated
                                }
                            )
                            
                            # Show a warning if generation was truncated
                            if is_truncated:
                                st.warning(f"⚠️ Response was not fully generated. Reason: {finish_reason}")
                            
                            try:
                                # Clean up the response
                                clean_response = str(response_text).strip()
                                if clean_response.startswith('```json'):
                                    clean_response = clean_response.split('```json')[1]
                                if clean_response.endswith('```'):
                                    clean_response = clean_response.rsplit('```', 1)[0]
                                
                                data = json.loads(clean_response)
                                
                                # Create subtabs - fix duplication
                                tabs_list = ["Visualization", "Raw JSON"]
                                if show_metadata and response_metadata:
                                    tabs_list.append("Metadata")
                                subtabs = st.tabs(tabs_list)
                                
                                # Raw JSON tab
                                with subtabs[1]:
                                    st.json(data)
                                
                                # Visualization tab
                                with subtabs[0]:
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
                                
                                # Metadata tab if available
                                if show_metadata and response_metadata and len(subtabs) > 2:
                                    with subtabs[2]:
                                        st.subheader("Generation Metadata")
                                        
                                        # Display token usage statistics
                                        if "token_count" in response_metadata:
                                            token_count = response_metadata["token_count"]
                                            tc1, tc2, tc3 = st.columns(3)
                                            with tc1:
                                                st.metric("Prompt Tokens", token_count.get("prompt", 0))
                                            with tc2:
                                                st.metric("Response Tokens", token_count.get("candidates", 0)) 
                                            with tc3:
                                                st.metric("Total Tokens", token_count.get("total", 0))
                                        
                                        # Display finish reason - check for new format first, then fall back to older format
                                        if finish_reason:
                                            st.info(f"**Finish Reason:** {finish_reason}")
                                        elif "candidates" in response_metadata and response_metadata["candidates"]:
                                            # Fallback for older format
                                            candidate = response_metadata["candidates"][0]
                                            st.write(f"**Finish Reason:** {get_finish_reason_text(candidate.get('finish_reason', 'UNKNOWN'))}")
                                            if candidate.get('finish_message'):
                                                st.write(f"**Finish Message:** {candidate.get('finish_message')}")
                                        
                                        # Full raw metadata
                                        with st.expander("Raw Metadata", expanded=False):
                                            st.json(response_metadata)
                                
                            except json.JSONDecodeError as e:
                                # Log error
                                app_logger.log_error(
                                    "Could not parse JSON from response",
                                    exception=e,
                                    context={"app_id": app_id}
                                )
                                
                                # Display the error and raw response
                                st.error(f"Could not parse JSON from response: {str(e)}")
                                
                                # Create tabs for different views - fix the duplication
                                tabs_list = ["Raw Response"]
                                if show_metadata and response_metadata:
                                    tabs_list.append("Metadata")
                                error_tabs = st.tabs(tabs_list)
                                
                                # Show raw response in first tab
                                with error_tabs[0]:
                                    st.text(str(response_text))
                                
                                # Show metadata in second tab if available
                                if show_metadata and response_metadata and len(error_tabs) > 1:
                                    with error_tabs[1]:
                                        st.subheader("Generation Metadata")
                                        
                                        # Display token usage statistics
                                        if "token_count" in response_metadata:
                                            token_count = response_metadata["token_count"]
                                            tc1, tc2, tc3 = st.columns(3)
                                            with tc1:
                                                st.metric("Prompt Tokens", token_count.get("prompt", 0))
                                            with tc2:
                                                st.metric("Response Tokens", token_count.get("candidates", 0)) 
                                            with tc3:
                                                st.metric("Total Tokens", token_count.get("total", 0))
                                        
                                        # Display finish reason - check for new format first, then fall back to older format
                                        if finish_reason:
                                            st.info(f"**Finish Reason:** {finish_reason}")
                                        elif "candidates" in response_metadata and response_metadata["candidates"]:
                                            # Fallback for older format
                                            candidate = response_metadata["candidates"][0]
                                            st.write(f"**Finish Reason:** {get_finish_reason_text(candidate.get('finish_reason', 'UNKNOWN'))}")
                                            if candidate.get('finish_message'):
                                                st.write(f"**Finish Message:** {candidate.get('finish_message')}")
                                        
                                        # Full raw metadata
                                        with st.expander("Raw Metadata", expanded=False):
                                            st.json(response_metadata)
                                            
                            except Exception as e:
                                # Log error
                                app_logger.log_error(
                                    "Error processing visualization",
                                    exception=e,
                                    context={"app_id": app_id}
                                )
                                st.error(f"Error processing visualization: {str(e)}")
                                st.text(str(response_text))
                    except Exception as e:
                        # Log error
                        app_logger.log_error(
                            "Error during analysis",
                            exception=e,
                            context={"app_id": app_id, "analysis_type": "version_comparison"}
                        )
                        st.error(f"Error during analysis: {str(e)}")
                        st.write("Please try again or contact support if the error persists.")
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
                        # Add language instruction
                        detailed_prompt += f"\nPlease provide the analysis in {st.session_state.analysis_language}."
                        csv_data = result['dataframe'].to_csv(index=False)
                        detailed_analysis_prompt = f"{detailed_prompt}\n\nData:\n{csv_data}"
                        
                        with st.spinner(f"Performing detailed analysis in {st.session_state.analysis_language}..."):
                            detailed_response = st.session_state.gemini_client.generate_content(
                                detailed_analysis_prompt,
                                return_full_response=True
                            )
                            
                            # Extract text from response
                            if isinstance(detailed_response, dict):
                                detailed_text = detailed_response.get("text", "")
                                detailed_finish_reason = detailed_response.get("finish_reason", "")
                                if detailed_finish_reason and "completed normally" not in detailed_finish_reason.lower():
                                    st.warning(f"⚠️ Detailed analysis was not fully completed. Reason: {detailed_finish_reason}")
                            else:
                                detailed_text = str(detailed_response)
                        
                        # Step 2: Generate user stories based on the analysis
                        user_story_prompt = get_prompt_by_number(9)
                        # Add language instruction
                        user_story_prompt += f"\nPlease provide the user stories in {st.session_state.analysis_language}."
                        story_prompt = f"{user_story_prompt}\n\nAnalysis:\n{detailed_text}"
                        
                        with st.spinner(f"Generating user stories in {st.session_state.analysis_language}..."):
                            # Request full response with metadata
                            story_response = st.session_state.gemini_client.generate_content(
                                story_prompt,
                                return_full_response=True
                            )
                            
                            # Extract response text and metadata
                            if isinstance(story_response, dict):
                                response_text = story_response.get("text", "")
                                finish_reason = story_response.get("finish_reason", "")
                                response_metadata = story_response.get("metadata", {})
                            else:
                                # Fallback for older versions
                                response_text = story_response
                                finish_reason = ""
                                response_metadata = {}
                                
                            # Show warning if the generation was truncated
                            is_truncated = False
                            if finish_reason and "completed normally" not in finish_reason.lower():
                                is_truncated = True
                                st.warning(f"⚠️ User stories generation was not fully completed. Reason: {finish_reason}")
                            
                            # Save to history with language info
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if user_story_key not in st.session_state.analysis_history:
                                st.session_state.analysis_history[user_story_key] = {}
                            st.session_state.analysis_history[user_story_key][timestamp] = {
                                'response': response_text,
                                'finish_reason': finish_reason,
                                'metadata': response_metadata if response_metadata else None,
                                'language': st.session_state.analysis_language
                            }
                            
                            try:
                                # Clean up the response text to extract JSON
                                if '```json' in response_text:
                                    json_content = response_text.split('```json')[1].split('```')[0]
                                elif '```' in response_text:
                                    json_content = response_text.split('```')[1].split('```')[0]
                                else:
                                    json_content = response_text
                                
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
                                st.code(response_text)
                                st.write("### Length of response:", len(response_text))
                                
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
                        # Add language instruction
                        detailed_prompt += f"\nPlease provide the analysis in {st.session_state.analysis_language}."
                        csv_data = result['dataframe'].to_csv(index=False)
                        detailed_analysis_prompt = f"{detailed_prompt}\n\nData:\n{csv_data}"
                        
                        with st.spinner(f"Performing detailed analysis in {st.session_state.analysis_language}..."):
                            detailed_response = st.session_state.gemini_client.generate_content(
                                detailed_analysis_prompt,
                                return_full_response=True
                            )
                            
                            # Extract text from response
                            if isinstance(detailed_response, dict):
                                detailed_text = detailed_response.get("text", "")
                                detailed_finish_reason = detailed_response.get("finish_reason", "")
                                if detailed_finish_reason and "completed normally" not in detailed_finish_reason.lower():
                                    st.warning(f"⚠️ Detailed analysis was not fully completed. Reason: {detailed_finish_reason}")
                            else:
                                detailed_text = str(detailed_response)
                        
                        # Step 2: Generate marketing campaign based on the analysis
                        marketing_prompt = get_prompt_by_number(10)
                        # Add language instruction
                        marketing_prompt += f"\nPlease provide the marketing campaign in {st.session_state.analysis_language}."
                        campaign_prompt = f"{marketing_prompt}\n\nAnalysis:\n{detailed_text}"
                        
                        with st.spinner(f"Generating marketing campaign in {st.session_state.analysis_language}..."):
                            # Request full response with metadata
                            campaign_response = st.session_state.gemini_client.generate_content(
                                campaign_prompt,
                                return_full_response=True
                            )
                            
                            # Extract response text and metadata
                            if isinstance(campaign_response, dict):
                                response_text = campaign_response.get("text", "")
                                finish_reason = campaign_response.get("finish_reason", "")
                                response_metadata = campaign_response.get("metadata", {})
                            else:
                                # Fallback for older versions
                                response_text = campaign_response
                                finish_reason = ""
                                response_metadata = {}
                                
                            # Show warning if the generation was truncated
                            is_truncated = False
                            if finish_reason and "completed normally" not in finish_reason.lower():
                                is_truncated = True
                                st.warning(f"⚠️ Marketing campaign generation was not fully completed. Reason: {finish_reason}")
                            
                            # Save to history with language info
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if marketing_key not in st.session_state.analysis_history:
                                st.session_state.analysis_history[marketing_key] = {}
                            st.session_state.analysis_history[marketing_key][timestamp] = {
                                'response': response_text,
                                'finish_reason': finish_reason,
                                'metadata': response_metadata if response_metadata else None,
                                'language': st.session_state.analysis_language
                            }
                            
                            try:
                                # Clean up the response text to extract JSON
                                if '```json' in response_text:
                                    json_content = response_text.split('```json')[1].split('```')[0]
                                elif '```' in response_text:
                                    json_content = response_text.split('```')[1].split('```')[0]
                                else:
                                    json_content = response_text
                                
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
                                st.code(campaign_response)
                                st.write("### Length of response:", len(campaign_response))
                                
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
        
        log_container = st.container()
        
        # Add filter controls
        log_filter_col1, log_filter_col2, log_filter_col3 = st.columns(3)
        
        with log_filter_col1:
            category_filter = st.multiselect(
                "Filter by Category",
                ["user_action", "api_call", "error", "performance"],
                default=["user_action", "error"],
                key="log_category_filter"
            )
        
        with log_filter_col2:
            search_filter = st.text_input(
                "Search Logs",
                "",
                placeholder="Enter search term...",
                key="log_search_filter"
            )
        
        with log_filter_col3:
            clear_logs = st.button("Clear Logs", key="clear_logs_btn")
            if clear_logs:
                app_logger.clear_logs()
                app_logger.log_user_action("Cleared activity logs")
                st.success("Logs cleared!")
        
        # Display logs based on filters
        with log_container:
            if 'log_categories' in st.session_state:
                # Filter logs by category
                filtered_logs = []
                for category in category_filter:
                    filtered_logs.extend(st.session_state.log_categories.get(category, []))
                
                # Filter by search term if provided
                if search_filter:
                    filtered_logs = [log for log in filtered_logs if search_filter.lower() in log.get('message', '').lower()]
                
                # Sort logs by timestamp (latest first)
                filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                if filtered_logs:
                    # Display the logs
                    for log in filtered_logs:
                        timestamp = log.get('timestamp', '')
                        category = log.get('category', '')
                        message = log.get('message', '')
                        
                        # Style based on category
                        if category == 'error':
                            st.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 4px; background-color: #fce8e6; margin-bottom: 0.5rem;">
                                <strong>{timestamp}</strong> - ❌ {message}
                            </div>
                            """, unsafe_allow_html=True)
                        elif category == 'user_action':
                            st.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 4px; background-color: #e8f0fe; margin-bottom: 0.5rem;">
                                <strong>{timestamp}</strong> - 👤 {message}
                            </div>
                            """, unsafe_allow_html=True)
                        elif category == 'api_call':
                            st.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 4px; background-color: #e6f4ea; margin-bottom: 0.5rem;">
                                <strong>{timestamp}</strong> - 🔄 {message}
                            </div>
                            """, unsafe_allow_html=True)
                        elif category == 'performance':
                            st.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 4px; background-color: #fff8e1; margin-bottom: 0.5rem;">
                                <strong>{timestamp}</strong> - ⏱️ {message}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 4px; background-color: #f8f9fa; margin-bottom: 0.5rem;">
                                <strong>{timestamp}</strong> - {message}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Show details if available, in an expander
                        if 'details' in log:
                            with st.expander("Details", expanded=False):
                                st.json(log['details'])
                else:
                    if search_filter:
                        st.info(f"No logs found matching '{search_filter}'")
                    else:
                        st.info("No logs matching the selected categories")
            else:
                st.info("No activity logged yet.")
        
        # Add log statistics
        if 'log_categories' in st.session_state:
            st.divider()
            st.subheader("Log Statistics")
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                user_action_count = len(st.session_state.log_categories.get('user_action', []))
                st.metric("User Actions", user_action_count)
            
            with stats_col2:
                api_call_count = len(st.session_state.log_categories.get('api_call', []))
                st.metric("API Calls", api_call_count)
            
            with stats_col3:
                error_count = len(st.session_state.log_categories.get('error', []))
                st.metric("Errors", error_count)
            
            with stats_col4:
                performance_count = len(st.session_state.log_categories.get('performance', []))
                st.metric("Performance Logs", performance_count)
            
            # Add a download button for logs
            if st.button("📥 Download Logs as JSON"):
                log_data = json.dumps({
                    'session_id': app_logger.session_id,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'categories': st.session_state.log_categories
                }, indent=2)
                
                st.download_button(
                    label="Download JSON",
                    data=log_data,
                    file_name=f"app_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()