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
    #st.set_page_config(page_title="Google Play Store Review Scraper & Analyzer", page_icon="📱", layout="wide")

    if 'results' not in st.session_state:
        st.session_state.results = {}
    if 'sentiment_results' not in st.session_state:
        st.session_state.sentiment_results = {}

    tabs = st.tabs(["Scraper", "Results", "Analysis", "Version Comparison", "Sample Prompts", "Artifacts", "Log"])

    with tabs[0]:
        st.title("Google Play Store Review Scraper")

        # User inputs
        app_id = st.text_input("Enter the app ID (e.g., com.example.app):","org.supertuxkart.stk")
        reviews_count = st.number_input("Number of reviews to scrape:", min_value=1, max_value=10000, value=1000)
        language = st.selectbox("Select language:", ["", "All", "en", "es", "fr", "de", "it", "pt"])
        country = st.selectbox("Select country:", ["", "All", "us", "gb", "ca", "au", "in", "es", "fr", "de", "it", "br"])

        if st.button("Scrape Reviews"):
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
        txt = Path('prompts.md').read_text()
        st.markdown(body=txt)

    with tabs[5]:
        st.title("Artifacts")
        st.link_button("Game Video Download", 
                       "https://storage.googleapis.com/damadei-public-bucket/supertux.mp4")

    with tabs[6]:
        st.title("Activity Log")
        if 'log' in st.session_state and st.session_state.log:
            for entry in reversed(st.session_state.log):
                st.text(entry)
        else:
            st.info("No activity logged yet.")

if __name__ == "__main__":
    main()