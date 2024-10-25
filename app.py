import streamlit as st
import pandas as pd
from google_play_scraper import Sort, reviews, reviews_all
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

def scrape_reviews(app_id, reviews_count, language, country):
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
    #remove user names for confidentiality
    df = df.drop('userName', axis=1)
    df = df.drop('userImage', axis=1)
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

    tabs = st.tabs(["Scraper", "Results", "Sample Prompts", "Log"])

    with tabs[0]:
        st.title("Google Play Store Review Scraper")

        # User inputs
        app_id = st.text_input("Enter the app ID (e.g., com.example.app):")
        reviews_count = st.number_input("Number of reviews to scrape:", min_value=1, max_value=10000, value=1000)
        language = st.selectbox("Select language:", ["", "All", "en", "es", "fr", "de", "it", "pt"])
        country = st.selectbox("Select country:", ["", "All", "us", "gb", "ca", "au", "in", "es", "fr", "de", "it", "br"])

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
        txt = Path('prompts.md').read_text()
        st.markdown(body=txt)

    with tabs[3]:
        st.title("Activity Log")
        if 'log' in st.session_state and st.session_state.log:
            for entry in reversed(st.session_state.log):
                st.text(entry)
        else:
            st.info("No activity logged yet.")

if __name__ == "__main__":
    main()