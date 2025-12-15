#!/bin/bash
# Cloud Doctor - Doctor Zone Deployment Script
# Deploys enhanced monitoring service to GCP Cloud Run

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cloud Doctor - Doctor Zone Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found. Please install Docker.${NC}"
    exit 1
fi

# Environment variables
GCP_PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
GCP_REGION=${GCP_REGION:-"asia-northeast3"}
SERVICE_NAME=${SERVICE_NAME:-"doctor-zone"}
IMAGE_NAME="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/cloud-doctor/${SERVICE_NAME}"

if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID not set. Set it with 'export GCP_PROJECT_ID=your-project-id'${NC}"
    exit 1
fi

echo -e "${GREEN}✓ GCP Project: ${GCP_PROJECT_ID}${NC}"
echo -e "${GREEN}✓ Region: ${GCP_REGION}${NC}"
echo -e "${GREEN}✓ Service: ${SERVICE_NAME}${NC}"

# Check required environment variables
echo -e "\n${YELLOW}Checking required environment variables...${NC}"

REQUIRED_VARS=("CLAUDE_API_KEY" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")
MISSING_VARS=()

for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        MISSING_VARS+=("$VAR")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    for VAR in "${MISSING_VARS[@]}"; do
        echo -e "${RED}  - $VAR${NC}"
    done
    echo -e "${YELLOW}Please set them before deploying.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All required variables set${NC}"

# Create Artifact Registry repository if it doesn't exist
echo -e "\n${YELLOW}Setting up Artifact Registry...${NC}"

if ! gcloud artifacts repositories describe cloud-doctor --location=${GCP_REGION} &>/dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create cloud-doctor \
        --repository-format=docker \
        --location=${GCP_REGION} \
        --description="Cloud Doctor container images"
    echo -e "${GREEN}✓ Repository created${NC}"
else
    echo -e "${GREEN}✓ Repository already exists${NC}"
fi

# Configure Docker authentication
echo -e "\n${YELLOW}Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev --quiet
echo -e "${GREEN}✓ Docker authenticated${NC}"

# Build Docker image
echo -e "\n${YELLOW}Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:latest .
echo -e "${GREEN}✓ Image built successfully${NC}"

# Push to Artifact Registry
echo -e "\n${YELLOW}Pushing image to Artifact Registry...${NC}"
docker push ${IMAGE_NAME}:latest
echo -e "${GREEN}✓ Image pushed successfully${NC}"

# Deploy to Cloud Run
echo -e "\n${YELLOW}Deploying to Cloud Run...${NC}"

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${GCP_REGION} \
    --allow-unauthenticated \
    --set-env-vars "GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
    --set-env-vars "GCP_LOCATION=us-central1" \
    --set-env-vars "CLAUDE_API_KEY=${CLAUDE_API_KEY}" \
    --set-env-vars "SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-}" \
    --set-env-vars "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" \
    --set-env-vars "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" \
    --set-env-vars "AWS_REGION=${AWS_REGION:-ap-northeast-2}" \
    --set-env-vars "LOG_GROUP_NAME=${LOG_GROUP_NAME:-/ecs/patient-zone}" \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 300s \
    --quiet

echo -e "${GREEN}✓ Deployment successful${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${GCP_REGION} \
    --format 'value(status.url)')

# Test deployment
echo -e "\n${YELLOW}Testing deployment...${NC}"
HEALTH_STATUS=$(curl -s ${SERVICE_URL}/health | grep -o '"status":"ok"' || echo "failed")

if [ "$HEALTH_STATUS" != "failed" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Service URL:${NC} ${SERVICE_URL}"
echo -e "\n${YELLOW}Test endpoints:${NC}"
echo -e "  Health Check:  ${SERVICE_URL}/health"
echo -e "  Analyze Logs:  ${SERVICE_URL}/analyze"
echo -e "  Test Slack:    ${SERVICE_URL}/slack/test"
echo -e "\n${YELLOW}Example usage:${NC}"
echo -e "  curl -X POST ${SERVICE_URL}/analyze \\"
echo -e "    -H 'Content-Type: application/json' \\"
echo -e "    -d '{\"time_range_minutes\":30,\"generate_terraform\":true}'"
echo -e "\n${GREEN}========================================${NC}"
