# Google Play Store Review Analyzer 📱

A powerful Streamlit application for scraping, analyzing, and gaining insights from Google Play Store reviews. This tool combines review scraping capabilities with advanced analysis features powered by AI to help understand user sentiment and feedback.

## Features 🌟

- **Review Scraping**: Fetch reviews from any Google Play Store app
- **Sentiment Analysis**: Analyze review sentiments and identify key factors
- **Version Comparison**: Track sentiment changes across app versions
- **Spam Detection**: Filter out potentially spam reviews
- **User Story Generation**: Convert reviews into actionable user stories
- **Multi-language Support**: Support for multiple languages and countries
- **Data Export**: Download scraped data in CSV format

## Installation 🛠️

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd partner-summit
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with your API keys:
```env
GCP_PROJECT=your-project-id
```

### Google Cloud Setup

1. Install the Google Cloud CLI:
```bash
# Install gcloud CLI following instructions for your OS
# https://cloud.google.com/sdk/docs/install
```

2. Initialize and set your project:
```bash
gcloud init
gcloud config set project your-project-id
```

3. Enable required APIs:
```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Vertex AI API for Gemini
gcloud services enable aiplatform.googleapis.com

# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com
```

4. Create an Artifact Registry repository:
```bash
gcloud artifacts repositories create app-images --repository-format=docker --location=your-region
```

### Cloud Run Deployment

1. Build and push the Docker image:
```bash
# Configure Docker to use Artifact Registry
gcloud auth configure-docker your-region-docker.pkg.dev

# Build and push the image
IMAGE_NAME="your-region-docker.pkg.dev/your-project-id/app-images/review-analyzer:latest"
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy review-analyzer \
  --image $IMAGE_NAME \
  --platform managed \
  --region your-region \
  --port 8080 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT=your-project-id"
```

## Usage 🚀

### Local Development
1. Start the application:
```bash
streamlit run app.py
```

2. Access the web interface at `http://localhost:8501`

### Cloud Run
After deployment, access the application at the URL provided by Cloud Run.

3. Enter an app ID from the Google Play Store URL:
   - Example: `org.supertuxkart.stk`
   - The app ID can be found in the Play Store URL: `play.google.com/store/apps/details?id=<app_id>`

## Project Structure 📁

```
.
├── app.py              # Main Streamlit application
├── src/
│   ├── analysis_tab.py # Analysis functionality
│   ├── gemini_client.py# AI client integration
│   ├── prompts.py      # Analysis prompts
│   └── config.py       # Configuration settings
├── prompts/            # Analysis prompt templates
├── Dockerfile          # Container configuration
└── requirements.txt    # Project dependencies
```

## Features in Detail 🔍

### Review Scraping
- Configurable number of reviews to fetch
- Language and country filtering
- Automatic data storage

### Analysis Features
- Sentiment analysis of reviews
- Key factor identification
- Version-based analysis
- Spam detection
- User story generation
- Interactive visualizations

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details. 