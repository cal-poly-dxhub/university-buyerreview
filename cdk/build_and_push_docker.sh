#!/bin/bash

# Docker Build and Push Script for Document Processing Pipeline
# This script builds your Docker image and pushes it to ECR

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="DocumentProcessingStack"
REGION=${AWS_REGION:-"us-east-1"}
IMAGE_TAG="latest"

echo -e "${BLUE}🐳 Docker Build and Push Script for Document Processing Pipeline${NC}"
echo "=================================================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Get ECR repository URI from CloudFormation outputs
echo -e "${YELLOW}🔍 Getting ECR repository URI from CloudFormation...${NC}"
ECR_REPO_URI=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
    --output text)

if [ -z "$ECR_REPO_URI" ] || [ "$ECR_REPO_URI" == "None" ]; then
    echo -e "${RED}❌ Could not find ECR repository URI. Make sure the CDK stack is deployed.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ ECR Repository URI: $ECR_REPO_URI${NC}"

# Get ECR login token
echo -e "${YELLOW}🔐 Getting ECR login token...${NC}"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO_URI

# Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
cd ..  # Go to project root where Dockerfile is located

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found in project root.${NC}"
    exit 1
fi

# Build the image
docker build -t document-processor .

# Tag the image for ECR
echo -e "${YELLOW}🏷️  Tagging Docker image...${NC}"
docker tag document-processor:latest $ECR_REPO_URI:$IMAGE_TAG

# Push to ECR
echo -e "${YELLOW}📤 Pushing Docker image to ECR...${NC}"
docker push $ECR_REPO_URI:$IMAGE_TAG

echo -e "${GREEN}✅ Docker image successfully built and pushed to ECR!${NC}"
echo ""
echo -e "${BLUE}Image Details:${NC}"
echo "- Repository: $ECR_REPO_URI"
echo "- Tag: $IMAGE_TAG"
echo "- Region: $REGION"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. The Lambda function will now use this container image"
echo "2. Test the API endpoint for file uploads"
echo "3. Monitor CloudWatch logs for the processing pipeline"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "- View ECR images: aws ecr describe-images --repository-name $(basename $ECR_REPO_URI)"
echo "- Delete old images: aws ecr batch-delete-image --repository-name $(basename $ECR_REPO_URI) --image-ids imageTag=old-tag"
echo "- View Lambda logs: aws logs tail /aws/lambda/$(basename $ECR_REPO_URI)-document-processor --follow" 