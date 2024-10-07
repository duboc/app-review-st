import streamlit as st
import pandas as pd
from google_play_scraper import Sort, reviews_all
import io
from datetime import datetime
import os
import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmCategory,
    HarmBlockThreshold,
)
import matplotlib.pyplot as plt

# Initialize Vertex AI
PROJECT_ID = "conventodapenha"  # Replace with your Google Cloud Project ID
LOCATION = "us-central1"  # Replace with your preferred region

@st.cache_resource
def init_vertex_ai():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-1.5-pro-001")
    return model

model = init_vertex_ai()

def scrape_reviews(app_id, reviews_count, language, country):
    reviews = reviews_all(
        app_id,
        lang=language,
        country=country,
        sort=Sort.NEWEST,
        count=reviews_count
    )
    return pd.DataFrame(reviews)

def log_action(action):
    if 'log' not in st.session_state:
        st.session_state.log = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.log.append(f"{timestamp}: {action}")

def analyze_sentiment(text, language, country):
    prompt = f"""
    Analyze the sentiment of the following text and classify it as positive, negative, or neutral. 
    Also provide a brief explanation for the classification.
    Consider that this text is a review for an app in the {language} language from {country}.

    Text: "{text}"

    Provide the sentiment (positive/negative/neutral) followed by a brief explanation.
    """
    
    response = model.generate_content(
        prompt,
        generation_config={
            "max_output_tokens": 8192,
            "temperature": 0.4,
            "top_p": 1
        }
    )
    return response.text

def main():
    #st.set_page_config(page_title="Google Play Store Review Scraper & Analyzer", page_icon="📱", layout="wide")

    if 'results' not in st.session_state:
        st.session_state.results = {}
    if 'sentiment_results' not in st.session_state:
        st.session_state.sentiment_results = {}

    tabs = st.tabs(["Scraper", "Results", "Sentiment Analysis", "Log"])

    with tabs[0]:
        st.title("Google Play Store Review Scraper")

        # User inputs
        app_id = st.text_input("Enter the app ID (e.g., com.example.app):")
        reviews_count = st.number_input("Number of reviews to scrape:", min_value=1, max_value=10000, value=100)
        language = st.selectbox("Select language:", ["en", "es", "fr", "de", "it", "pt"])
        country = st.selectbox("Select country:", ["us", "gb", "ca", "au", "in", "es", "fr", "de", "it", "br"])

        if st.button("Scrape Reviews"):
            if app_id:
                with st.spinner("Scraping reviews... This may take a while."):
                    df = scrape_reviews(app_id, reviews_count, language, country)
                
                st.success(f"Successfully scraped {len(df)} reviews!")

                # Save results to session state
                st.session_state.results[app_id] = {
                    'dataframe': df,
                    'language': language,
                    'country': country,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Log the action
                log_action(f"Scraped {len(df)} reviews for app {app_id}")

                # Display the dataframe
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
        st.title("Sentiment Analysis")
        if st.session_state.results:
            app_id = st.selectbox("Select App ID for Sentiment Analysis", list(st.session_state.results.keys()))
            if app_id:
                result = st.session_state.results[app_id]
                df = result['dataframe']
                language = result['language']
                country = result['country']

                if st.button("Analyze Sentiment"):
                    if app_id not in st.session_state.sentiment_results:
                        st.session_state.sentiment_results[app_id] = {'analyzed': False}

                    if not st.session_state.sentiment_results[app_id]['analyzed']:
                        with st.spinner("Analyzing sentiment... This may take a while."):
                            sentiments = []
                            for index, row in df.iterrows():
                                sentiment_result = analyze_sentiment(row['content'], language, country)
                                sentiments.append(sentiment_result)

                            df['sentiment_analysis'] = sentiments
                            st.session_state.sentiment_results[app_id] = {
                                'analyzed': True,
                                'dataframe': df,
                                'language': language,
                                'country': country
                            }

                        log_action(f"Analyzed sentiment for {len(df)} reviews of app {app_id}")

                    analyzed_df = st.session_state.sentiment_results[app_id]['dataframe']
                    
                    st.success("Sentiment analysis completed!")
                    
                    # Display results in an expander
                    with st.expander("Sentiment Analysis Results", expanded=True):
                        for _, row in analyzed_df.iterrows():
                            st.write(f"Review: {row['content']}")
                            st.write(f"Sentiment Analysis: {row['sentiment_analysis']}")
                            st.divider()

                        # Allow CSV download of analyzed data
                        csv = analyzed_df.to_csv(index=False)
                        st.download_button(
                            label="Download Analyzed CSV",
                            data=csv,
                            file_name=f"{app_id}_analyzed_reviews.csv",
                            mime="text/csv",
                        )
        else:
            st.info("No results available for sentiment analysis. Use the Scraper tab to fetch reviews first.")

    with tabs[3]:
        st.title("Activity Log")
        if 'log' in st.session_state and st.session_state.log:
            for entry in reversed(st.session_state.log):
                st.text(entry)
        else:
            st.info("No activity logged yet.")

if __name__ == "__main__":
    main()