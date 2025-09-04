#!/bin/bash

# CDK Deployment Script for Document Processing Pipeline
# This script automates the deployment of your CDK stack

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
ACCOUNT=${AWS_ACCOUNT_ID:-""}

echo -e "${BLUE}🚀 CDK Deployment Script for Document Processing Pipeline${NC}"
echo "=================================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS account ID if not provided
if [ -z "$ACCOUNT" ]; then
    echo -e "${YELLOW}🔍 Getting AWS Account ID...${NC}"
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    echo -e "${GREEN}✅ AWS Account ID: $ACCOUNT${NC}"
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ CDK CLI is not installed. Please install it first:${NC}"
    echo "npm install -g aws-cdk"
    exit 1
fi

# Check if Python dependencies are installed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Bootstrap CDK if needed
echo -e "${YELLOW}🔧 Checking if CDK is bootstrapped...${NC}"
if ! cdk list &> /dev/null; then
    echo -e "${YELLOW}🚀 Bootstrapping CDK...${NC}"
    cdk bootstrap aws://$ACCOUNT/$REGION
    echo -e "${GREEN}✅ CDK bootstrapped successfully${NC}"
else
    echo -e "${GREEN}✅ CDK is already bootstrapped${NC}"
fi

# Build the Lambda functions
echo -e "${YELLOW}🔧 Building Lambda functions...${NC}"
cd lambda_functions/upload_handler
pip install -r requirements.txt -t .
cd ../health_check
pip install -r requirements.txt -t .
cd ../..

# Deploy the stack
echo -e "${YELLOW}🚀 Deploying CDK stack...${NC}"
cdk deploy --require-approval never

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"

# Get stack outputs
echo -e "${BLUE}📊 Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs' \
    --output table

echo -e "${GREEN}🎉 Your document processing pipeline is now deployed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Build and push your Docker image to the ECR repository"
echo "2. Test the API endpoint for file uploads"
echo "3. Monitor CloudWatch logs for the processing pipeline"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "- View stack: cdk list"
echo "- Destroy stack: cdk destroy"
echo "- View logs: cdk logs"
echo "- Update stack: cdk deploy" 