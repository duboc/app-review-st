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
from google_play_scraper import Sort, reviews, reviews_all, app
from datetime import datetime
from pathlib import Path
import json
from src.prompts import get_prompt_by_number
from src.bigquery_client import BigQueryStorageWriter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize BigQuery writer
bq_writer = BigQueryStorageWriter()

def scrape_reviews(app_id, reviews_count, language, country):
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    if language == "All":
        language = ""
    if country == "All":
        country = ""

    # Get app details to fetch the title
    app_details = app(app_id, lang=language, country=country)
    app_title = app_details['title']

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
        
        # Add app title and app id columns
        df['app_title'] = app_title
        df['app_id'] = app_id
        
        # Save to CSV in data directory
        csv_path = data_dir / f"{app_id}_reviews.csv"
        df.to_csv(csv_path, index=False)
        
        # Save to BigQuery using Storage Write API
        try:
            dataset_name = os.getenv('BIGQUERY_DATASET')
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            
            if dataset_name and project_id:
                result = bq_writer.append_rows(
                    project_id=project_id,
                    dataset_id=dataset_name,
                    table_id='scrapped',
                    df=df
                )
                log_action(result)
            else:
                st.warning("BigQuery dataset name or project ID not found in environment variables")
        except Exception as e:
            st.error(f"Error saving to BigQuery: {str(e)}")
        
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
        "�� Sample Prompts",
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

    with tabs[3]:
        st.title("Artifacts")
        st.link_button("Game Video Download", 
                       "https://storage.googleapis.com/damadei-public-bucket/supertux.mp4")

    with tabs[4]:
        st.title("Activity Log")
        if 'log' in st.session_state and st.session_state.log:
            for entry in reversed(st.session_state.log):
                st.text(entry)
        else:
            st.info("No activity logged yet.")

if __name__ == "__main__":
    main()