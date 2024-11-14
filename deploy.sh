#!/bin/bash

# Exit on error
set -e

# Function to read value from .env file
read_env() {
    local key=$1
    local default=$2
    if [ -f .env ]; then
        local value=$(grep "^${key}=" .env | cut -d '=' -f2)
        if [ ! -z "$value" ]; then
            echo "$value"
            return
        fi
    fi
    echo "$default"
}

# Read values from .env with defaults
PROJECT_ID=$(read_env "GCP_PROJECT")
REGION=$(read_env "GCP_REGION")
ARTIFACT_REGISTRY_REPO=$(read_env "ARTIFACT_REGISTRY_REPO")
SERVICE_NAME=$(read_env "SERVICE_NAME")

# Display configuration
echo "Using configuration:"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Artifact Registry Repo: $ARTIFACT_REGISTRY_REPO"
echo "Service Name: $SERVICE_NAME"

# Ensure gcloud is authenticated and configured
echo "Configuring gcloud..."
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com

# Create Artifact Registry repository if it doesn't exist
echo "Setting up Artifact Registry repository..."
gcloud artifacts repositories create $ARTIFACT_REGISTRY_REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="Play Store Reviews Demo" \
  || true

# Configure Docker to use Artifact Registry
echo "Configuring Docker authentication..."
gcloud auth configure-docker $REGION-docker.pkg.dev

# Submit the build
echo "Submitting build to Cloud Build..."
gcloud builds submit . --config=./cloudbuild.yaml \
  --substitutions=\
_ARTIFACT_REGISTRY_REPO=$ARTIFACT_REGISTRY_REPO,\
_REPO_LOCATION=$REGION,\
_SERVICE_NAME=$SERVICE_NAME,\
_SERVICE_REGION=$REGION

echo "Deployment completed successfully!" 