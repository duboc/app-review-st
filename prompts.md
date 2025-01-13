## Example Prompts

## Prompt 1: General Sentiment Analysis (Expanded)

```
Analyze the sentiment of user reviews in the CSV file, which contains the columns content, score, and thumbs up of the review.

1. Classify each review as "Positive", "Negative" or "Neutral" based on the textual content, considering that the 'score' may not accurately reflect the expressed sentiment.
2. Provide a qualitative estimate of the percentage distribution of each sentiment category to get an overview of users' opinions about the application.
3. Identify the main themes and keywords associated with each sentiment category, such as praised or criticized features, reported problems, and suggestions for improvement.
4. Present a concise analysis summary, highlighting the most relevant points and general sentiment trends.
```

## Prompt 2: Detailed Analysis with Examples (Expanded)

```
Conduct an in-depth sentiment analysis of reviews in the CSV file, which contains the columns content, score, and at.

1. Classify each review as "Positive", "Negative" or "Neutral", considering that the 'score' may not be entirely accurate.
2. For each sentiment category:
    * Describe the main themes and keywords, grouping them by similarity and relevance.
    * Select 3 example reviews that clearly represent the category's sentiment, including the review date for context.
3. Present a general analysis of sentiment distribution, showing evolution over time (if sufficient data is available).
4. Include insights about possible causes of sentiment changes, such as app updates or external events.
```

## Prompt 3: Focus on Problems and Suggestions (Expanded)

```
Analyze the reviews in the CSV file, focusing on identifying problems and suggestions reported by users.

1. Extract the main complaints and problems mentioned in negative reviews, categorizing them by type (bugs, features, performance, etc.) and frequency.
2. Identify the most requested suggestions and features by users, grouping them by theme and prioritizing the most frequent or impactful ones.
3. Present a structured report with problems and suggestions, including examples of relevant reviews and highlighting the most critical points that require immediate attention from developers.
4. If possible, use the 'at' column to identify trends and verify if certain problems persist over time or if new suggestions have emerged recently.
```

## Prompt 4: Identification of Factors Influencing Sentiment

```
Explore the CSV file to identify factors that influence user sentiment.

1. Classify each review as "Positive", "Negative" or "Neutral".
2. Investigate whether the device type ('device') or user's country ('androidVersion') are related to differences in overall sentiment.
3. Analyze if certain features or problems are more frequently mentioned in reviews from specific devices or countries.
4. Present the results clearly, showing if there are significant trends and offering insights on how to adapt the application for different audiences.
```

## Prompt 5: Detection of Inconsistent Reviews or Spam

```
Use sentiment and language analysis techniques to identify possible fake reviews or spam in the CSV file containing the content column.

1. Analyze the sentiment of each review and check for discrepancies between expressed sentiment and assigned 'rating', which may indicate a fake review.
2. Identify suspicious language patterns, such as excessive keyword repetition, generic phrases, or unusual grammatical structures.
3. Check for very similar or identical reviews, which may suggest spam or rating manipulation.
4. Present a list of potentially fake reviews or spam, along with the criteria used to identify them.
```

## Prompt 6: Sentiment Comparison Between App Versions

### **Select the `Gemini-1.5-Pro-002` model and change the temperature to `0.3`.**

[System Instructions section remains in English as it's technical documentation]

## Prompt 7: Extracting Gameplay Insights from Reviews Based on Video

1. ### If you're a gaming company, preferably create a recording of your game for use in this exercise or download the game video in the **Artifacts** tab.

2. ### Download the CSV with reviews of your application corresponding to the video or use ID **org.supertuxkart.stk** to download the reviews corresponding to the video downloaded above.

```
Analyze the CSV file containing user reviews about a game, aiming to identify gameplay improvement points that can be observed in a game recording that is also being included in this request.

1. Extract from **negative and neutral** reviews the main problems, criticisms, and suggestions related to gameplay, such as:
    * Controls: difficulties, inaccuracies, lack of responsiveness.
    * Game mechanics: complexity, repetitiveness, lack of balance.
    * Level design: frustration, lack of challenge, bugs.
    * Artificial intelligence: predictable enemies, inconsistent behavior.
    * Progression: difficulty in advancing, lack of meaningful rewards.
    * Other gameplay aspects mentioned in the reviews.

2. Organize problems and suggestions into categories, prioritizing the most frequent or impactful ones.

3. For each identified problem or suggestion, provide a clear and objective description of how it might manifest in the game recording. Examples:

    * **Problem:** "Imprecise controls"
        * **How to observe in recording:** Character movements that don't correspond to player commands, difficulty in performing specific actions, camera that hinders visualization.
    * **Suggestion:** "More enemy variety"
        * **How to observe in recording:** Frequent repetition of the same enemy types, lack of challenge in combat, sense of monotony.

4. Include examples of specific review excerpts that illustrate each problem or suggestion, to facilitate contextualization during recording analysis.

5. Finally, present a summary of the main gameplay attention points, based on the reviews, to guide the recording analysis and identify improvement opportunities.
```

## Prompt 9: User Story Generation from Analysis

```
Based on the detailed sentiment analysis provided, create user stories following the format:

As a [type of user],
I want [goal/desire]
So that [benefit/value]

Guidelines for story creation:
1. Focus on the main pain points and feature requests identified in the analysis
2. Prioritize stories based on sentiment frequency and impact
3. Include acceptance criteria for each story
4. Add story points estimation (1,2,3,5,8,13)
5. Group stories by themes (e.g., UI/UX, Performance, Features)

Expected output format (JSON):
{
    "themes": [
        {
            "name": "string",
            "stories": [
                {
                    "as_a": "string",
                    "i_want": "string",
                    "so_that": "string",
                    "acceptance_criteria": ["string"],
                    "story_points": number,
                    "priority": "High|Medium|Low",
                    "supporting_reviews": ["string"]
                }
            ]
        }
    ],
    "summary": {
        "total_stories": number,
        "total_story_points": number,
        "theme_breakdown": {
            "theme_name": number
        }
    }
}
```

