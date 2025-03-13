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
import time
from .gemini_client import GeminiRegionClient
from .prompts import get_prompt_by_number
from .logger import app_logger, performance_logger
import json
from pathlib import Path
import altair as alt
import numpy as np

# Function to convert finish reason code to human-readable string
def get_finish_reason_text(finish_reason):
    """
    Convert finish reason to a human-readable string.
    This function is maintained for backward compatibility.
    New code should use GeminiRegionClient.get_finish_reason_description directly.
    """
    # Check if we already have a string description
    if isinstance(finish_reason, str) and len(finish_reason) > 10:
        # This is likely already a descriptive string from the new client
        return finish_reason
    
    # Otherwise, use the legacy mapping
    reason_map = {
        0: "FINISH_REASON_UNSPECIFIED - The finish reason is unspecified",
        1: "MAX_TOKENS - The model reached the token limit",
        2: "SAFETY - Content filtered for safety reasons",
        3: "RECITATION - Potential recitation detected",
        4: "OTHER - Other stopping reason",
        5: "BLOCKLIST - Content contains blocked terms",
        6: "PROHIBITED_CONTENT - Content contains prohibited material",
        7: "SPII - Sensitive Personal Identifiable Information detected",
        8: "MALFORMED_FUNCTION_CALL - Invalid function call format"
    }
    
    # Handle both string and numeric inputs
    try:
        # If it's a string but represents a number, convert to int
        if isinstance(finish_reason, str) and finish_reason.isdigit():
            finish_reason = int(finish_reason)
    except:
        pass
    
    # Return the mapped value or the original if not found
    if isinstance(finish_reason, int) and finish_reason in reason_map:
        return reason_map[finish_reason]
    return str(finish_reason)

def visualize_problems_suggestions(data):
    """
    Create visualizations for the problems and suggestions analysis.
    
    Args:
        data (dict): The parsed JSON data from the analysis
    
    Returns:
        None: Renders visualizations directly to Streamlit
    """
    try:
        # Create sections for different parts of the analysis
        st.subheader("Executive Summary")
        st.info(data.get("executive_summary", "No executive summary available"))
        
        # Problem Analysis Section
        if "problem_analysis" in data and "table" in data["problem_analysis"]:
            st.subheader("Problem Analysis")
            
            problem_data = data["problem_analysis"]["table"]
            
            # Convert to DataFrame for easier manipulation
            problem_df = pd.DataFrame(problem_data)
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_problems = problem_df["frequency"].sum() if "frequency" in problem_df else 0
                st.metric("Total Problems", total_problems)
            with col2:
                top_category = problem_df.iloc[0]["category"] if len(problem_df) > 0 and "category" in problem_df else "N/A"
                st.metric("Top Problem Category", top_category)
            with col3:
                # Count trends
                if "trend" in problem_df:
                    increasing = sum(1 for trend in problem_df["trend"] if trend == "Increasing")
                    st.metric("Increasing Trends", increasing)
            with col4:
                # Show critical problems count
                critical_count = data["problem_analysis"].get("critical_problems_count", 0)
                st.metric("Critical Problems", critical_count, delta=None, delta_color="inverse")
            
            # Problem frequency chart
            if "frequency" in problem_df and "category" in problem_df:
                st.subheader("Problem Categories by Frequency")
                
                # Sort by frequency descending
                sorted_df = problem_df.sort_values("frequency", ascending=False)
                
                # Create color scale based on severity if available
                if "severity" in problem_df:
                    # Create bar chart with Altair
                    chart = alt.Chart(sorted_df).mark_bar().encode(
                        x=alt.X('frequency:Q', title='Frequency'),
                        y=alt.Y('category:N', title='Category', sort='-x'),
                        color=alt.Color('severity:N', 
                                      scale=alt.Scale(
                                          domain=['Critical', 'Major', 'Minor'],
                                          range=['#ff4c4c', '#ffa64c', '#6aaa64']
                                      )),
                        tooltip=['category', 'frequency', 'severity', 'trend']
                    ).properties(
                        height=min(300, len(sorted_df) * 40)
                    )
                else:
                    # Fallback to trend-based coloring
                    chart = alt.Chart(sorted_df).mark_bar().encode(
                        x=alt.X('frequency:Q', title='Frequency'),
                        y=alt.Y('category:N', title='Category', sort='-x'),
                        color=alt.condition(
                            alt.datum.trend == 'Increasing',
                            alt.value('#ff4c4c'),
                            alt.condition(
                                alt.datum.trend == 'Decreasing',
                                alt.value('#6aaa64'),
                                alt.value('#9aa0a6')
                            )
                        ),
                        tooltip=['category', 'frequency', 'trend']
                    ).properties(
                        height=min(300, len(sorted_df) * 40)
                    )
                
                st.altair_chart(chart, use_container_width=True)
            
            # Show most affected user segments if available
            if "most_affected_segments" in data["problem_analysis"]:
                affected_segments = data["problem_analysis"]["most_affected_segments"]
                if affected_segments:
                    st.subheader("Most Affected User Segments")
                    segments_text = ", ".join(affected_segments)
                    st.markdown(f"""
                    <div style="padding: 0.7rem; border-radius: 4px; background-color: #fef7e0; margin-bottom: 0.8rem; border-left: 4px solid #fbbc04;">
                        <p><strong>Users most affected by problems:</strong> {segments_text}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Trend summary
            st.subheader("Trend Summary")
            if "trend_summary" in data["problem_analysis"]:
                st.write(data["problem_analysis"]["trend_summary"])
            
            # Problem details
            st.subheader("Problem Details")
            problem_tabs = st.tabs(["Problem Information", "Example Reviews"])
            
            with problem_tabs[0]:
                for problem in problem_data:
                    severity_color = "#ff4c4c" if problem.get("severity") == "Critical" else (
                        "#ffa64c" if problem.get("severity") == "Major" else "#6aaa64"
                    )
                    
                    st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 4px; border-left: 4px solid {severity_color}; background-color: #f8f9fa; margin-bottom: 1rem;">
                        <h3>{problem.get('category', 'Unnamed Category')}</h3>
                        <p><strong>Frequency:</strong> {problem.get('frequency', 'N/A')}</p>
                        <p><strong>Severity:</strong> <span style="color: {severity_color};">{problem.get('severity', 'N/A')}</span></p>
                        <p><strong>Trend:</strong> {problem.get('trend', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if "affected_user_segments" in problem:
                        st.markdown("#### Affected User Segments:")
                        segments = ", ".join(problem.get("affected_user_segments", []))
                        st.markdown(f"- {segments}")
            
            with problem_tabs[1]:
                for problem in problem_data:
                    if "example_reviews" in problem:
                        st.markdown(f"### {problem.get('category', 'Unnamed Category')} Examples:")
                        for review in problem["example_reviews"]:
                            st.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 4px; background-color: #f8f9fa; margin-bottom: 0.5rem;">
                                <p>"{review.get('content', 'No content')}"</p>
                                <p><small>Date: {review.get('at', 'Unknown date')}</small></p>
                            </div>
                            """, unsafe_allow_html=True)
        
        # Suggestion Analysis Section
        if "suggestion_analysis" in data and "table" in data["suggestion_analysis"]:
            st.subheader("Suggestion Analysis")
            
            suggestion_data = data["suggestion_analysis"]["table"]
            
            # Convert to DataFrame for easier manipulation
            suggestion_df = pd.DataFrame(suggestion_data)
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_suggestions = suggestion_df["frequency"].sum() if "frequency" in suggestion_df else 0
                st.metric("Total Suggestions", total_suggestions)
            with col2:
                top_suggestion = suggestion_df.iloc[0]["suggestion_group"] if len(suggestion_df) > 0 and "suggestion_group" in suggestion_df else "N/A"
                st.metric("Top Suggestion", top_suggestion)
            with col3:
                high_impact = sum(1 for impact in suggestion_df["estimated_impact"] if impact == "High") if "estimated_impact" in suggestion_df else 0
                st.metric("High Impact", high_impact)
            with col4:
                # Get high impact count from the enhanced schema if available
                high_impact_count = data["suggestion_analysis"].get("high_impact_count", high_impact)
                st.metric("High Impact Count", high_impact_count)
            
            # Quick wins section if available
            if "quick_wins" in data["suggestion_analysis"] and data["suggestion_analysis"]["quick_wins"]:
                st.subheader("Quick Wins")
                quick_wins = data["suggestion_analysis"]["quick_wins"]
                for i, win in enumerate(quick_wins):
                    st.markdown(f"""
                    <div style="padding: 0.7rem; border-radius: 4px; background-color: #e6f4ea; margin-bottom: 0.8rem; border-left: 4px solid #34a853;">
                        <p><strong>Quick Win {i+1}:</strong> {win}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Suggestion frequency chart
            if "frequency" in suggestion_df and "suggestion_group" in suggestion_df:
                st.subheader("Suggestions by Frequency")
                
                # Sort by frequency descending
                sorted_df = suggestion_df.sort_values("frequency", ascending=False)
                
                # Create chart with combined impact and difficulty
                if "estimated_impact" in sorted_df and "implementation_difficulty" in sorted_df:
                    # Create a combined field for visualization
                    sorted_df["impact_difficulty"] = sorted_df.apply(
                        lambda x: f"{x['estimated_impact']} Impact / {x['implementation_difficulty']} Difficulty", 
                        axis=1
                    )
                    
                    # Create a size scale based on the implementation difficulty
                    sorted_df["size"] = sorted_df["implementation_difficulty"].map({
                        "Easy": 100, 
                        "Medium": 70, 
                        "Hard": 40
                    })
                    
                    # Create bubble chart with Altair
                    bubble_chart = alt.Chart(sorted_df).mark_circle().encode(
                        x=alt.X('frequency:Q', title='Frequency'),
                        y=alt.Y('suggestion_group:N', title='Suggestion', sort='-x'),
                        size=alt.Size('size:Q', legend=None),
                        color=alt.Color('estimated_impact:N',
                                      scale=alt.Scale(
                                          domain=['High', 'Medium', 'Low'],
                                          range=['#ff4c4c', '#ffa64c', '#4c8bff']
                                      )),
                        tooltip=['suggestion_group', 'frequency', 'estimated_impact', 'implementation_difficulty']
                    ).properties(
                        height=min(400, len(sorted_df) * 40)
                    )
                    
                    st.altair_chart(bubble_chart, use_container_width=True)
                    
                    # Add a legend for difficulty
                    st.markdown("""
                    <div style="text-align: center; margin-top: -20px;">
                        <small>Circle size represents implementation difficulty: Larger = Easier</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Fallback to simple bar chart
                    chart = alt.Chart(sorted_df).mark_bar().encode(
                        x=alt.X('frequency:Q', title='Frequency'),
                        y=alt.Y('suggestion_group:N', title='Suggestion', sort='-x'),
                        color=alt.Color('estimated_impact:N', 
                                       scale=alt.Scale(
                                           domain=['High', 'Medium', 'Low'],
                                           range=['#ff4c4c', '#ffa64c', '#4c8bff']
                                       )),
                        tooltip=['suggestion_group', 'frequency', 'estimated_impact']
                    ).properties(
                        height=min(300, len(sorted_df) * 40)
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
            
            # Emerging suggestions
            st.subheader("Emerging Suggestions")
            if "emerging_suggestions" in data["suggestion_analysis"]:
                st.write(data["suggestion_analysis"]["emerging_suggestions"])
            
            # Suggestion details
            st.subheader("Suggestion Details")
            suggestion_tabs = st.tabs(["Suggestion Information", "Example Reviews"])
            
            with suggestion_tabs[0]:
                for suggestion in suggestion_data:
                    impact_color = "#ff4c4c" if suggestion.get("estimated_impact") == "High" else (
                        "#ffa64c" if suggestion.get("estimated_impact") == "Medium" else "#4c8bff"
                    )
                    
                    # Determine difficulty badge color
                    if "implementation_difficulty" in suggestion:
                        diff = suggestion["implementation_difficulty"]
                        diff_color = "#34a853" if diff == "Easy" else (
                            "#fbbc04" if diff == "Medium" else "#ea4335"
                        )
                        diff_badge = f'<span style="background-color: {diff_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8rem;">{diff}</span>'
                    else:
                        diff_badge = ""
                    
                    st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 4px; border-left: 4px solid {impact_color}; background-color: #f8f9fa; margin-bottom: 1rem;">
                        <h3>{suggestion.get('suggestion_group', 'Unnamed Suggestion')}</h3>
                        <p><strong>Frequency:</strong> {suggestion.get('frequency', 'N/A')}</p>
                        <p><strong>Estimated Impact:</strong> <span style="color: {impact_color};">{suggestion.get('estimated_impact', 'N/A')}</span></p>
                        <p><strong>Implementation Difficulty:</strong> {diff_badge}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with suggestion_tabs[1]:
                for suggestion in suggestion_data:
                    if "example_reviews" in suggestion:
                        st.markdown(f"### {suggestion.get('suggestion_group', 'Unnamed Suggestion')} Examples:")
                        for review in suggestion["example_reviews"]:
                            st.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 4px; background-color: #e6f4ea; margin-bottom: 0.5rem;">
                                <p>"{review.get('content', 'No content')}"</p>
                            </div>
                            """, unsafe_allow_html=True)
        
        # Sentiment Trend Analysis
        if "sentiment_trend_analysis" in data:
            st.subheader("Sentiment Trend Analysis")
            
            sentiment_data = data["sentiment_trend_analysis"]
            
            # Display summary
            if "summary" in sentiment_data:
                st.write(sentiment_data["summary"])
            
            # Display period trends if available
            if "period_trends" in sentiment_data and sentiment_data["period_trends"]:
                st.subheader("Sentiment Trends Over Time")
                
                # Convert to DataFrame
                trends_df = pd.DataFrame(sentiment_data["period_trends"])
                
                # Create stacked bar chart for sentiment percentages
                if "positive_percentage" in trends_df and "negative_percentage" in trends_df:
                    # Melt the DataFrame for easier charting
                    melted_df = pd.melt(
                        trends_df, 
                        id_vars=['period'], 
                        value_vars=['positive_percentage', 'neutral_percentage', 'negative_percentage'],
                        var_name='sentiment', 
                        value_name='percentage'
                    )
                    
                    # Replace sentiment names for better display
                    melted_df['sentiment'] = melted_df['sentiment'].replace({
                        'positive_percentage': 'Positive',
                        'neutral_percentage': 'Neutral',
                        'negative_percentage': 'Negative'
                    })
                    
                    # Create stacked bar chart
                    chart = alt.Chart(melted_df).mark_bar().encode(
                        x=alt.X('period:N', title='Time Period'),
                        y=alt.Y('percentage:Q', title='Percentage'),
                        color=alt.Color('sentiment:N', 
                                       scale=alt.Scale(
                                           domain=['Positive', 'Neutral', 'Negative'],
                                           range=['#34a853', '#9aa0a6', '#ea4335']
                                       )),
                        tooltip=['period', 'sentiment', 'percentage']
                    ).properties(
                        height=300
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
            
            # Display significant events
            st.subheader("Significant Events")
            if "significant_events" in sentiment_data and sentiment_data["significant_events"]:
                events = sentiment_data["significant_events"]
                for event in events:
                    impact_color = "#34a853" if event.get("sentiment_impact") == "Positive" else (
                        "#9aa0a6" if event.get("sentiment_impact") == "Neutral" else "#ea4335"
                    )
                    
                    st.markdown(f"""
                    <div style="padding: 0.7rem; border-radius: 4px; border-left: 4px solid {impact_color}; background-color: #f8f9fa; margin-bottom: 0.8rem;">
                        <p><strong>{event.get('date', '')}</strong>: {event.get('event', 'Unnamed event')}</p>
                        <p><small>Sentiment Impact: <span style="color: {impact_color};">{event.get('sentiment_impact', 'Unknown')}</span></small></p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # User Segments
        if "user_segments" in data:
            user_segments = data["user_segments"]
            
            # Only show if there are identified segments
            if "identified_segments" in user_segments and user_segments["identified_segments"]:
                st.subheader("User Segments Analysis")
                
                # Show identified segments
                segments = user_segments["identified_segments"]
                st.write("Identified user segments:", ", ".join(segments))
                
                # Show segment-specific issues if available
                if "segment_specific_issues" in user_segments and user_segments["segment_specific_issues"]:
                    segment_issues = user_segments["segment_specific_issues"]
                    
                    # Create tabs for each segment instead of expandable sections
                    segment_tabs = st.tabs([f"{segment_data.get('segment', 'Unknown')}" for segment_data in segment_issues])
                    
                    for i, segment_data in enumerate(segment_issues):
                        segment_name = segment_data.get("segment", "Unknown Segment")
                        issues = segment_data.get("top_issues", [])
                        
                        with segment_tabs[i]:
                            if issues:
                                st.markdown("#### Top Issues:")
                                for issue in issues:
                                    st.markdown(f"- {issue}")
                            else:
                                st.write("No specific issues identified for this segment.")
        
        # Actionable Insights
        if "actionable_insights" in data:
            st.subheader("Actionable Insights")
            
            insights = data["actionable_insights"]
            for i, insight in enumerate(insights):
                st.markdown(f"""
                <div style="padding: 0.7rem; border-radius: 4px; border-left: 4px solid #1a73e8; background-color: #e8f0fe; margin-bottom: 0.8rem;">
                    <p><strong>Insight {i+1}:</strong> {insight}</p>
                </div>
                """, unsafe_allow_html=True)
    
    except Exception as e:
        app_logger.log_error(
            "Error creating problem & suggestion visualizations",
            exception=e
        )
        st.error(f"Error creating visualizations: {str(e)}")
        st.json(data)  # Fallback to displaying raw JSON

@performance_logger(app_logger, "render_analysis_tab")
def render_analysis_tab():
    st.title("Analysis")
    
    # Initialize Gemini client if not exists
    if 'gemini_client' not in st.session_state:
        st.session_state.gemini_client = GeminiRegionClient()
        app_logger.log_user_action("Initialized Gemini client in analysis tab")
    
    # Initialize analysis history if not exists
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = {}
    
    # Create subtabs for each prompt with improved labeling
    subtabs = st.tabs([
        "🔍 General Sentiment", 
        "📊 Detailed Analysis", 
        "⚠️ Problems & Suggestions", 
        "💡 Sentiment Factors", 
        "🔎 Spam Detection", 
        "🎮 Gameplay Analysis"
    ])
    
    for i, tab in enumerate(subtabs, 1):
        with tab:
            if st.session_state.results:
                for app_id, result in st.session_state.results.items():
                    st.subheader(f"Analysis for {app_id}")
                    
                    # Create unique key for this analysis
                    analysis_key = f"{app_id}_prompt_{i}"
                    
                    # Show refresh button for previous analyses
                    if analysis_key in st.session_state.analysis_history:
                        history_container = st.container()
                        
                        # Add controls for history
                        hist_col1, hist_col2 = st.columns([3, 1])
                        with hist_col1:
                            st.write("📜 Previous analyses")
                        with hist_col2:
                            if st.button("🔄 Refresh", key=f"refresh_hist_{i}_{app_id}"):
                                # Clear this specific analysis history
                                st.session_state.analysis_history[analysis_key] = {}
                                app_logger.log_user_action(f"Refreshed analysis history for {app_id}, prompt {i}")
                                st.success("History cleared!")
                        
                        # Show analysis history in expanders
                        with history_container:
                            for timestamp, analysis in st.session_state.analysis_history[analysis_key].items():
                                with st.expander(f"Analysis from {timestamp} ({analysis.get('language', 'unknown')})", expanded=False):
                                    if 'response' in analysis:
                                        # Create tabs for response and metadata
                                        if 'metadata' in analysis:
                                            content_tab, metadata_tab = st.tabs(["Response", "Metadata"])
                                            with content_tab:
                                                st.markdown(analysis['response'])
                                            
                                            with metadata_tab:
                                                st.json(analysis['metadata'])
                                                
                                                # Highlight any truncation or early stopping
                                                if analysis['metadata'] is not None:
                                                    # Check if we have direct finish_reason in analysis
                                                    if 'finish_reason' in analysis:
                                                        finish_reason = analysis['finish_reason']
                                                        if finish_reason and 'completed normally' not in finish_reason.lower():
                                                            st.warning(f"⚠️ Generation stopped early: {finish_reason}")
                                                    # Fall back to old format in candidates
                                                    elif 'candidates' in analysis['metadata'] and analysis['metadata']['candidates']:
                                                        candidate = analysis['metadata']['candidates'][0]
                                                        reason = candidate.get('finish_reason')
                                                        if reason and reason != 'STOP':
                                                            st.warning(f"⚠️ Generation stopped early: {get_finish_reason_text(reason)} - {candidate.get('finish_message', '')}")
                                        else:
                                            # Just show the response if no metadata is available
                                            st.markdown(analysis['response'])
                                    else:
                                        # Handle older format
                                        st.markdown(analysis)
                    
                    if i == 3:  # Problems & Suggestions tab
                        # Add demo option for Problems & Suggestions
                        demo_col1, demo_col2 = st.columns([3, 1])
                        with demo_col2:
                            if st.button("🧪 View Demo", key=f"demo_btn_{i}_{app_id}", help="See a demo of the enhanced visualization"):
                                app_logger.log_user_action(f"Viewed demo visualization for Problems & Suggestions")
                                test_problems_suggestions_visualization(app_id)
                    
                    if i == 5:  # Spam Detection
                        if st.button(f"Analyze for Spam", key=f"analyze_btn_{i}_{app_id}", use_container_width=True):
                            try:
                                # Log start of analysis
                                app_logger.log_user_action(
                                    f"Started spam detection analysis for {app_id}",
                                    {"language": st.session_state.analysis_language}
                                )
                                
                                # Get the prompt text for spam detection json
                                json_prompt = get_prompt_by_number(8)
                                
                                # Add language instruction to prompt
                                language_instruction = f"\nPlease provide the analysis in {st.session_state.analysis_language}."
                                json_prompt = json_prompt + language_instruction
                                
                                # Get data for analysis
                                csv_data = ""
                                if app_id in st.session_state.results:
                                    csv_data = st.session_state.results[app_id]['dataframe'].to_csv(index=False)
                                
                                # Construct the JSON schema version of prompt (prompt 8)
                                json_full_prompt = f"{json_prompt}\n\nData:\n{csv_data}"
                                
                                # Create the analysis key for storing results
                                analysis_key = f"{app_id}_prompt_{i}"
                                
                                # Generate the JSON analysis
                                with st.spinner(f"Analyzing spam patterns in {st.session_state.analysis_language}..."):
                                    # Log API call
                                    app_logger.log_api_call(
                                        api_name="gemini_client.generate_content",
                                        params={"prompt_type": "spam_detection_json"}
                                    )
                                    
                                    # Time JSON analysis
                                    start_time = time.time()
                                    json_response = st.session_state.gemini_client.generate_content(json_full_prompt)
                                    json_duration_ms = (time.time() - start_time) * 1000
                                    
                                    # Log successful API call
                                    app_logger.log_api_call(
                                        api_name="gemini_client.generate_content",
                                        params={"prompt_type": "spam_detection_json"},
                                        response_status="success",
                                        duration_ms=json_duration_ms
                                    )
                                
                                # Save analysis to history
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                if analysis_key not in st.session_state.analysis_history:
                                    st.session_state.analysis_history[analysis_key] = {}
                                
                                # Store response
                                st.session_state.analysis_history[analysis_key][timestamp] = {
                                    'json': json_response,
                                    'language': st.session_state.analysis_language
                                }
                                
                                # Log completion
                                app_logger.log_user_action(
                                    f"Completed spam detection analysis for {app_id}",
                                    {
                                        "language": st.session_state.analysis_language, 
                                        "json_duration_ms": json_duration_ms
                                    }
                                )
                                
                                # Show the analysis result
                                st.markdown(f"## Spam Detection Analysis ({timestamp})")
                                
                                try:
                                    # Clean up the JSON response
                                    clean_response = json_response.strip()
                                    if '```json' in clean_response:
                                        clean_response = clean_response.split('```json')[1].split('```')[0]
                                    elif '```' in clean_response:
                                        clean_response = clean_response.split('```')[1].split('```')[0]
                                    
                                    # Parse the JSON data
                                    data = json.loads(clean_response.strip())
                                    
                                    # Simply display the JSON
                                    st.json(data)
                                    
                                except json.JSONDecodeError as e:
                                    # Log error
                                    app_logger.log_error(
                                        "Could not parse JSON from response",
                                        exception=e,
                                        context={"app_id": app_id}
                                    )
                                    
                                    # Display the error and raw response
                                    st.error(f"Could not parse JSON from response: {str(e)}")
                                    st.text(json_response)
                                            
                                except Exception as e:
                                    # Log error
                                    app_logger.log_error(
                                        "Error processing JSON",
                                        exception=e,
                                        context={"app_id": app_id}
                                    )
                                    st.error(f"Error processing JSON: {str(e)}")
                                    st.text(json_response)
                            
                            except Exception as e:
                                # Log error during analysis
                                app_logger.log_error(
                                    f"Error during spam detection analysis for {app_id}",
                                    exception=e,
                                    context={"app_id": app_id, "language": st.session_state.analysis_language}
                                )
                                st.error(f"Error during spam detection analysis: {str(e)}")
                    else:
                        # Choose a button label based on the analysis type
                        button_labels = {
                            1: "Analyze Sentiment",
                            2: "Analyze in Detail",
                            3: "Find Problems & Suggestions",
                            4: "Identify Sentiment Factors",
                            6: "Analyze Gameplay"
                        }
                        button_label = button_labels.get(i, f"Analyze with Prompt {i}")
                        
                        # Special configuration for Problems & Suggestions (index 3)
                        is_problematic_tab = (i == 3)
                        
                        # For problematic tab, add a toggle for retry options
                        if is_problematic_tab:
                            retry_col1, retry_col2 = st.columns([1, 1])
                            with retry_col1:
                                return_metadata = st.toggle("Show Generation Metadata", value=True, key=f"metadata_toggle_{app_id}")
                            with retry_col2:
                                retry_count = st.number_input("Max Retry Attempts", min_value=1, max_value=5, value=3, key=f"retry_count_{app_id}")
                        else:
                            return_metadata = False
                            retry_count = 3  # Default
                        
                        if st.button(button_label, key=f"analyze_btn_{i}_{app_id}", use_container_width=True):
                            try:
                                # Log start of analysis
                                app_logger.log_user_action(
                                    f"Started {button_label.lower()} for {app_id}",
                                    {"prompt_number": i, "language": st.session_state.analysis_language}
                                )
                                
                                # Get the prompt text
                                prompt = get_prompt_by_number(i)
                                
                                # Add language instruction to prompt
                                language_instruction = f"\nPlease provide the analysis in {st.session_state.analysis_language}."
                                prompt = prompt + language_instruction
                                
                                # Convert DataFrame to CSV string
                                csv_data = result['dataframe'].to_csv(index=False)
                                
                                # Combine prompt with data
                                full_prompt = f"{prompt}\n\nData:\n{csv_data}"
                                
                                # Log API call
                                app_logger.log_api_call(
                                    api_name="gemini_client.generate_content",
                                    params={"prompt_type": button_label.lower().replace(" ", "_")}
                                )
                                
                                with st.spinner(f"Analyzing reviews in {st.session_state.analysis_language}..."):
                                    start_time = time.time()
                                    
                                    # Use the enhanced generate_content method with metadata for problematic tabs
                                    response = st.session_state.gemini_client.generate_content(
                                        full_prompt, 
                                        return_full_response=return_metadata or is_problematic_tab
                                    )
                                    
                                    # Extract response, finish reason and metadata
                                    if isinstance(response, dict):
                                        response_text = response.get("text", "")
                                        finish_reason = response.get("finish_reason", "")
                                        response_metadata = response.get("metadata", {})
                                    else:
                                        response_text = response
                                        finish_reason = ""
                                        response_metadata = {}
                                    
                                    duration_ms = (time.time() - start_time) * 1000
                                    
                                    # Check for incomplete generation
                                    is_truncated = False
                                    if finish_reason:
                                        is_truncated = "completed normally" not in finish_reason.lower()
                                    elif response_metadata and "candidates" in response_metadata and response_metadata["candidates"]:
                                        # Fallback for older format
                                        candidate = response_metadata["candidates"][0]
                                        raw_reason = candidate.get("finish_reason", "UNKNOWN")
                                        is_truncated = raw_reason != "STOP"
                                    
                                    # Log successful API call with metadata
                                    app_logger.log_api_call(
                                        api_name="gemini_client.generate_content",
                                        params={
                                            "prompt_type": button_label.lower().replace(" ", "_"),
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
                                        'language': st.session_state.analysis_language,
                                        'finish_reason': finish_reason,
                                        'metadata': response_metadata if response_metadata else None
                                    }
                                    
                                    # Log completion
                                    app_logger.log_user_action(
                                        f"Completed {button_label.lower()} for {app_id}",
                                        {
                                            "duration_ms": duration_ms, 
                                            "language": st.session_state.analysis_language,
                                            "finish_reason": finish_reason,
                                            "is_truncated": is_truncated
                                        }
                                    )
                                    
                                    # Show the new analysis in an expander
                                    with st.expander(f"Analysis from {timestamp} ({st.session_state.analysis_language})", expanded=True):
                                        # First display warning if truncated
                                        if is_truncated:
                                            st.warning(f"⚠️ Response was not fully generated. Reason: {finish_reason}")
                                        
                                        # Check if response might contain JSON
                                        if "```json" in str(response_text) or "{" in str(response_text):
                                            try:
                                                # Try to extract and parse JSON
                                                response_str = str(response_text)
                                                if "```json" in response_str:
                                                    json_str = response_str.split("```json")[1].split("```")[0]
                                                elif "{" in response_str and "}" in response_str:
                                                    # Simple extraction - not robust for all cases
                                                    start = response_str.find("{")
                                                    end = response_str.rfind("}") + 1
                                                    json_str = response_str[start:end]
                                                else:
                                                    json_str = None
                                                
                                                if json_str:
                                                    # Parse JSON and display in a more interactive way
                                                    data = json.loads(json_str)
                                                    
                                                    # Use special visualization for Problems & Suggestions analysis
                                                    if is_problematic_tab:
                                                        # Create tabs for different views
                                                        viz_tab, raw_tab, meta_tab = st.tabs(["Visualization", "Raw", "Metadata"])
                                                        
                                                        with raw_tab:
                                                            st.markdown(response_text)
                                                        
                                                        with viz_tab:
                                                            # Use specialized visualization for Problems & Suggestions
                                                            visualize_problems_suggestions(data)
                                                        
                                                        with meta_tab:
                                                            st.subheader("Generation Metadata")
                                                            
                                                            # Display finish reason prominently
                                                            if finish_reason:
                                                                st.info(f"**Finish Reason:** {finish_reason}")
                                                                
                                                            if response_metadata:
                                                                # Token usage
                                                                if "token_count" in response_metadata:
                                                                    token_count = response_metadata["token_count"]
                                                                    tc1, tc2, tc3 = st.columns(3)
                                                                    with tc1:
                                                                        st.metric("Prompt Tokens", token_count.get("prompt", 0))
                                                                    with tc2:
                                                                        st.metric("Response Tokens", token_count.get("candidates", 0))
                                                                    with tc3:
                                                                        st.metric("Total Tokens", token_count.get("total", 0))
                                                                
                                                                # Full raw metadata - use subheader instead of expander
                                                                st.subheader("Raw Metadata")
                                                                st.json(response_metadata)
                                                            else:
                                                                st.info("No metadata available for this generation")
                                                    else:
                                                        # Create tabs for different views
                                                        viz_tab, raw_tab, meta_tab = st.tabs(["Visualization", "Raw", "Metadata"])
                                                        
                                                        with raw_tab:
                                                            st.markdown(response_text)
                                                        
                                                        with viz_tab:
                                                            # Try to create visualizations based on data structure
                                                            # This is a simple example - could be expanded based on specific analysis types
                                                            st.json(data)
                                                        
                                                        with meta_tab:
                                                            st.subheader("Generation Metadata")
                                                            
                                                            # Display finish reason prominently
                                                            if finish_reason:
                                                                st.info(f"**Finish Reason:** {finish_reason}")
                                                                
                                                            if response_metadata:
                                                                # Token usage
                                                                if "token_count" in response_metadata:
                                                                    token_count = response_metadata["token_count"]
                                                                    tc1, tc2, tc3 = st.columns(3)
                                                                    with tc1:
                                                                        st.metric("Prompt Tokens", token_count.get("prompt", 0))
                                                                    with tc2:
                                                                        st.metric("Response Tokens", token_count.get("candidates", 0))
                                                                    with tc3:
                                                                        st.metric("Total Tokens", token_count.get("total", 0))
                                                                
                                                                # Full raw metadata - use subheader instead of expander
                                                                st.subheader("Raw Metadata")
                                                                st.json(response_metadata)
                                                            else:
                                                                st.info("No metadata available for this generation")
                                            except json.JSONDecodeError as e:
                                                # Log error and display raw response
                                                app_logger.log_error(
                                                    "Could not parse JSON from response",
                                                    exception=e,
                                                    context={"app_id": app_id}
                                                )
                                                
                                                st.warning(f"Could not parse JSON from response: {str(e)}")
                                                st.markdown(response_text)
                                                
                                                # Show metadata in expandable section if available
                                                if response_metadata:
                                                    # Use tabs instead of expanders to avoid nesting
                                                    meta_tab = st.tab("Response Metadata")
                                                    with meta_tab:
                                                        # Display finish reason prominently 
                                                        if finish_reason:
                                                            st.info(f"**Finish Reason:** {finish_reason}")
                                                        st.json(response_metadata)
                                            except Exception as e:
                                                # Log general error
                                                app_logger.log_error(
                                                    "Error processing visualization",
                                                    exception=e,
                                                    context={"app_id": app_id}
                                                )
                                                st.error(f"Error processing visualization: {str(e)}")
                                                st.markdown(response_text)
                                        else:
                                            # Regular text response
                                            tabs = st.tabs(["Content", "Metadata"] if response_metadata else ["Content"])
                                            with tabs[0]:
                                                st.markdown(response_text)
                                            
                                            if response_metadata and len(tabs) > 1:
                                                with tabs[1]:
                                                    st.subheader("Generation Metadata")
                                                    
                                                    # Display finish reason prominently
                                                    if finish_reason:
                                                        st.info(f"**Finish Reason:** {finish_reason}")
                                                    
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
                                                    
                                                    # Full raw metadata - use subheader instead of expander
                                                    st.subheader("Raw Metadata")
                                                    st.json(response_metadata)
                                
                            except Exception as e:
                                app_logger.log_error(
                                    f"Error during {button_label.lower()}",
                                    exception=e,
                                    context={"app_id": app_id, "prompt_number": i}
                                )
                                st.error(f"Error during analysis: {str(e)}")
            else:
                st.info("No data available for analysis. Please scrape some reviews first.")
                
                # Add a quick demo button
                if st.button("🎮 Try with Demo Data", key=f"demo_btn_{i}"):
                    app_logger.log_user_action("Requested demo data for analysis")
                    
                    # Use our demo visualization for Problems & Suggestions
                    if i == 3:  # Problems & Suggestions tab
                        app_logger.log_user_action("Viewed demo visualization for Problems & Suggestions without app data")
                        test_problems_suggestions_visualization("demo_app")
                    else:
                        st.info("Demo feature coming soon! Please scrape real data for now.")

def test_problems_suggestions_visualization(app_id):
    """
    Load the example response and visualize it with the enhanced visualization.
    
    Args:
        app_id (str): The app ID to display in the title
    """
    try:
        # Load the example data from the file
        example_path = Path('prompts/03_example_response.json')
        if not example_path.exists():
            st.error("Example data file not found. Please make sure prompts/03_example_response.json exists.")
            return
        
        # Load the example JSON data
        with open(example_path, 'r') as f:
            example_data = json.load(f)
        
        # Create a container with a title
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 8px; background-color: #e8f0fe; margin-bottom: 1rem; border: 1px solid #4285f4;">
            <h2>Demo: Enhanced Problems & Suggestions Visualization for {app_id}</h2>
            <p>This is a demonstration of the enhanced visualization capabilities using example data.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for visualization and raw data
        viz_tab, raw_tab = st.tabs(["Visualization", "Raw JSON"])
        
        with viz_tab:
            # Use our visualization function
            visualize_problems_suggestions(example_data)
        
        with raw_tab:
            # Show the raw JSON for reference
            st.json(example_data)
        
        # Add explanatory notes
        st.markdown("""
        ### About This Demo
        
        This demo showcases the enhanced visualization for the Problems & Suggestions analysis. The visualization:
        
        - Highlights critical problems with appropriate color coding
        - Shows user segments affected by each problem
        - Visualizes trends in problem reports
        - Displays implementation difficulty alongside impact for suggestions
        - Provides sentiment trend analysis over time
        - Identifies quick wins for development teams
        
        To use this with real data, run the Problems & Suggestions analysis on your app reviews.
        """)
        
    except Exception as e:
        app_logger.log_error(
            "Error loading example visualization",
            exception=e
        )
        st.error(f"Error loading example visualization: {str(e)}")
 