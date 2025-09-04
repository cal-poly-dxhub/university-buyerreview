# 🚀 CDK Infrastructure for Document Processing Pipeline

This CDK project deploys the complete infrastructure for your document processing pipeline, including S3 storage, Lambda functions, API Gateway, and ECR repository.

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway  │───▶│  Upload Handler  │───▶│   S3 Bucket     │
│   (HTTP API)   │    │    Lambda        │    │  (Documents)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  CloudWatch    │◀───│ Document Processor│◀───│  S3 Event      │
│   Logs &       │    │    Lambda        │    │  Trigger       │
│   Alarms       │    │  (Container)     │    │                │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 **What Gets Deployed**

### **Core Infrastructure**

- **S3 Bucket** - Secure document storage with lifecycle policies
- **ECR Repository** - Container image storage for your Lambda
- **IAM Roles & Policies** - Secure permissions for all services
- **CloudWatch Logs** - Centralized logging and monitoring

### **Lambda Functions**

- **Document Processor** - Your main container-based Lambda function
- **Upload Handler** - Handles file uploads via API Gateway
- **Health Check** - API health monitoring endpoint

### **API & Triggers**

- **HTTP API Gateway** - RESTful API for file uploads
- **S3 Event Triggers** - Automatically starts processing on file upload
- **CORS Support** - Cross-origin request handling

### **Monitoring & Security**

- **CloudWatch Alarms** - Error and performance monitoring
- **S3 Encryption** - Server-side encryption for all documents
- **IAM Security** - Least-privilege access policies

## 🚀 **Quick Start**

### **Prerequisites**

- AWS CLI configured with appropriate permissions
- Node.js and npm installed
- CDK CLI installed globally
- Python 3.8+ installed
- Docker installed and running

### **1. Install Dependencies**

```bash
# Install CDK CLI globally
npm install -g aws-cdk

# Install Python dependencies
pip install -r requirements.txt
```

### **2. Configure AWS**

```bash
# Configure your AWS credentials
aws configure

# Set your preferred region
export AWS_REGION=us-east-1
```

### **3. Deploy Infrastructure**

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### **4. Build and Push Docker Image**

```bash
# Make Docker script executable
chmod +x build_and_push_docker.sh

# Build and push your container
./build_and_push_docker.sh
```

## 🔧 **Configuration**

### **Environment Variables**

The CDK stack automatically sets these environment variables for your Lambda functions:

```python
environment={
    "DOCUMENTS_BUCKET": "your-bucket-name",
    "LOG_LEVEL": "INFO",
    "MAX_DOCUMENTS_PER_BATCH": "5",
    "BATCH_DELAY_SECONDS": "1.0"
}
```

### **Customizing the Stack**

Edit `document_processing_stack.py` to modify:

- **Lambda Configuration** - Memory, timeout, concurrent executions
- **S3 Settings** - Bucket policies, lifecycle rules, encryption
- **API Gateway** - CORS settings, rate limiting, authentication
- **Monitoring** - CloudWatch alarms, log retention

## 📁 **Project Structure**

```
cdk/
├── app.py                          # Main CDK app entry point
├── document_processing_stack.py    # Main infrastructure stack
├── requirements.txt                # Python dependencies
├── cdk.json                       # CDK configuration
├── deploy.sh                      # Deployment automation script
├── build_and_push_docker.sh       # Docker build/push script
├── README.md                      # This file
└── lambda_functions/              # Lambda function code
    ├── upload_handler/            # File upload handler
    │   ├── upload_handler.py
    │   └── requirements.txt
    └── health_check/              # Health check endpoint
        ├── health_check.py
        └── requirements.txt
```

## 🔄 **Deployment Workflow**

### **1. Infrastructure Deployment**

```bash
# Deploy the CDK stack
cdk deploy

# Or use the automated script
./deploy.sh
```

### **2. Container Image Deployment**

```bash
# Build and push your Docker image
./build_and_push_docker.sh
```

### **3. Testing**

```bash
# Test the health endpoint
curl https://your-api-id.execute-api.region.amazonaws.com/health

# Test file upload
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/upload \
  -F "file=@document.pdf"
```

## 📊 **Monitoring & Logs**

### **CloudWatch Logs**

- **Document Processor**: `/aws/lambda/documentprocessingstack-document-processor`
- **Upload Handler**: `/aws/lambda/documentprocessingstack-upload-handler`
- **Health Check**: `/aws/lambda/documentprocessingstack-health-check`

### **CloudWatch Alarms**

- **Error Rate** - Alerts when Lambda functions have errors
- **Duration** - Alerts when processing takes too long
- **Throttling** - Monitors for API throttling issues

### **S3 Metrics**

- **Bucket size** and **object count**
- **Upload/download rates**
- **Error rates** and **latency**

## 🔒 **Security Features**

### **IAM Policies**

- **Least privilege access** - Only necessary permissions
- **Resource-level permissions** - Specific S3 bucket access
- **Service principals** - Secure Lambda execution

### **S3 Security**

- **Server-side encryption** - AES-256 encryption
- **Block public access** - No public read/write
- **Versioning enabled** - File history preservation
- **Lifecycle policies** - Automatic cleanup and archiving

### **API Security**

- **HTTPS only** - All API calls encrypted
- **CORS configuration** - Controlled cross-origin access
- **Request validation** - Input sanitization and validation

## 🚨 **Troubleshooting**

### **Common Issues**

#### **CDK Bootstrap Required**

```bash
# If you get bootstrap errors
cdk bootstrap aws://ACCOUNT/REGION
```

#### **Permission Denied**

```bash
# Check your AWS credentials
aws sts get-caller-identity

# Verify IAM permissions for CDK
```

#### **Docker Build Fails**

```bash
# Check Docker is running
docker info

# Verify Dockerfile exists
ls -la Dockerfile
```

#### **Lambda Timeout**

```bash
# Increase timeout in the stack
timeout=Duration.minutes(30)  # Increase from 15 to 30 minutes
```

### **Useful Commands**

```bash
# List deployed stacks
cdk list

# View stack details
cdk diff

# Destroy stack
cdk destroy

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name DocumentProcessingStack

# Check Lambda function status
aws lambda get-function --function-name documentprocessingstack-document-processor
```

## 📈 **Scaling & Performance**

### **Lambda Configuration**

- **Memory**: 1GB (configurable)
- **Timeout**: 15 minutes (configurable)
- **Concurrent Executions**: 5 (configurable)
- **Reserved Concurrency**: Prevents throttling

### **S3 Performance**

- **Lifecycle Policies**: Automatic tiering to IA/Glacier
- **Versioning**: File history preservation
- **Encryption**: Minimal performance impact

### **API Gateway**

- **HTTP API v2**: Better performance than REST API
- **CORS Support**: Optimized for web applications
- **Auto-scaling**: Handles traffic spikes automatically

## 🔄 **Updates & Maintenance**

### **Updating the Stack**

```bash
# Make changes to your code
# Then redeploy
cdk deploy
```

### **Updating Container Image**

```bash
# Build and push new image
./build_and_push_docker.sh

# Lambda will automatically use the new image
```

### **Rolling Back**

```bash
# Revert to previous version
cdk rollback

# Or manually update Lambda function version
```

## 📞 **Support & Resources**

### **AWS Documentation**

- [CDK Developer Guide](https://docs.aws.amazon.com/cdk/)
- [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)

### **CDK Constructs**

- [aws-cdk-lib](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib-readme.html)
- [Constructs Library](https://docs.aws.amazon.com/cdk/api/v2/docs/constructs-readme.html)

### **Best Practices**

- [CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)

## 🎯 **Next Steps**

After deployment:

1. **Test the API endpoints** with sample documents
2. **Monitor CloudWatch logs** for any issues
3. **Set up additional alarms** for production monitoring
4. **Configure custom domain** for your API (optional)
5. **Add authentication** if needed (Cognito, API Keys)
6. **Set up CI/CD pipeline** for automated deployments

---

**Happy Deploying! 🚀**

This CDK project provides a production-ready foundation for your document processing pipeline with built-in security, monitoring, and scalability features.
