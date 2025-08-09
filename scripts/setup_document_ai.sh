#!/bin/bash

# Google Cloud Document AI Setup Script
# This script helps you set up Google Cloud Document AI for the engineering design criteria extractor

set -e

echo "🔧 Google Cloud Document AI Setup Script"
echo "========================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Installing..."
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
    echo "✅ Google Cloud CLI installed. Please restart your terminal and run this script again."
    exit 1
fi

echo "✅ Google Cloud CLI found"

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "🔐 Please authenticate with Google Cloud..."
    gcloud auth login
fi

# Get project ID
echo "📋 Available projects:"
gcloud projects list --format="table(projectId,name)"

read -p "Enter your Google Cloud Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Project ID is required"
    exit 1
fi

# Set project
echo "🔧 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable APIs
echo "🚀 Enabling required APIs..."
gcloud services enable documentai.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable vision.googleapis.com

# Create service account
SERVICE_ACCOUNT_NAME="document-ai-extractor"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo "👤 Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Document AI Extractor" \
    --description="Service account for engineering design criteria extractor" \
    || echo "Service account already exists"

# Grant permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/documentai.apiUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer"

# Download service account key
KEY_FILE="$HOME/document-ai-key.json"
echo "📄 Downloading service account key to $KEY_FILE..."
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
# Google Cloud Document AI Configuration
GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE

# Document AI Processor Configuration
DOCUMENT_AI_PROCESSOR_ID=your-processor-id-here
DOCUMENT_AI_LOCATION=us

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=$(openssl rand -hex 32)

# File Upload Configuration
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=data/uploads
OUTPUT_FOLDER=data/output

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF

echo "✅ .env file created"

# List available processors
echo "📋 Available Document AI processors:"
gcloud ai document processors list --location=us --format="table(name,displayName,type,state)"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and set DOCUMENT_AI_PROCESSOR_ID to one of the processor IDs above"
echo "2. Run: python3 examples/test_document_ai_config.py"
echo "3. Start the webapp: python3 -m src.webapp.run"
echo ""
echo "For more information, see: config/google_cloud_setup.md" 