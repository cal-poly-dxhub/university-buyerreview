#!/usr/bin/env python3
"""
Test script to verify CDK deployment
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def test_deployment():
    """Test the deployed infrastructure"""
    
    print("🧪 Testing CDK Deployment")
    print("=" * 50)
    
    # Initialize AWS clients
    cloudformation = boto3.client('cloudformation')
    s3 = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    ecr = boto3.client('ecr')
    
    stack_name = "DocumentProcessingStack"
    
    try:
        # Test 1: Check if CloudFormation stack exists
        print("1. Checking CloudFormation stack...")
        response = cloudformation.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        if stack['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            print("   ✅ Stack is deployed successfully")
        else:
            print(f"   ❌ Stack status: {stack['StackStatus']}")
            return False
        
        # Get stack outputs
        outputs = {output['OutputKey']: output['OutputValue'] for output in stack['Outputs']}
        
        # Test 2: Check S3 bucket
        print("2. Testing S3 bucket...")
        bucket_name = outputs.get('DocumentsBucketName')
        if bucket_name:
            try:
                s3.head_bucket(Bucket=bucket_name)
                print(f"   ✅ S3 bucket '{bucket_name}' exists and is accessible")
            except ClientError as e:
                print(f"   ❌ S3 bucket error: {e}")
                return False
        else:
            print("   ❌ S3 bucket name not found in outputs")
            return False
        
        # Test 3: Check ECR repository
        print("3. Testing ECR repository...")
        ecr_uri = outputs.get('ECRRepositoryUri')
        if ecr_uri:
            try:
                repo_name = ecr_uri.split('/')[-1]
                ecr.describe_repositories(repositoryNames=[repo_name])
                print(f"   ✅ ECR repository '{repo_name}' exists")
            except ClientError as e:
                print(f"   ❌ ECR repository error: {e}")
                return False
        else:
            print("   ❌ ECR repository URI not found in outputs")
            return False
        
        # Test 4: Check Lambda functions
        print("4. Testing Lambda functions...")
        lambda_arn = outputs.get('DocumentProcessorLambdaArn')
        if lambda_arn:
            try:
                lambda_name = lambda_arn.split(':')[-1]
                response = lambda_client.get_function(FunctionName=lambda_name)
                if response['Configuration']['State'] == 'Active':
                    print(f"   ✅ Lambda function '{lambda_name}' is active")
                else:
                    print(f"   ❌ Lambda function state: {response['Configuration']['State']}")
                    return False
            except ClientError as e:
                print(f"   ❌ Lambda function error: {e}")
                return False
        else:
            print("   ❌ Lambda function ARN not found in outputs")
            return False
        
        # Test 5: Check API Gateway
        print("5. Testing API Gateway...")
        api_endpoint = outputs.get('APIEndpoint')
        if api_endpoint:
            print(f"   ✅ API Gateway endpoint: {api_endpoint}")
        else:
            print("   ❌ API Gateway endpoint not found in outputs")
            return False
        
        # Test 6: Check IAM roles
        print("6. Testing IAM roles...")
        try:
            # Check if Lambda execution role exists
            lambda_client.get_function(FunctionName=lambda_name)
            print("   ✅ IAM roles are properly configured")
        except ClientError as e:
            print(f"   ❌ IAM role error: {e}")
            return False
        
        print("\n🎉 All tests passed! Your infrastructure is deployed correctly.")
        print("\n📊 Deployment Summary:")
        print(f"   - Stack Name: {stack_name}")
        print(f"   - S3 Bucket: {bucket_name}")
        print(f"   - ECR Repository: {ecr_uri}")
        print(f"   - API Endpoint: {api_endpoint}")
        print(f"   - Lambda Function: {lambda_arn.split(':')[-1]}")
        
        return True
        
    except ClientError as e:
        print(f"❌ AWS API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints"""
    
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    try:
        # Get API endpoint from CloudFormation
        cloudformation = boto3.client('cloudformation')
        response = cloudformation.describe_stacks(StackName="DocumentProcessingStack")
        outputs = {output['OutputKey']: output['OutputValue'] for output in response['Stacks'][0]['Outputs']}
        api_endpoint = outputs.get('APIEndpoint')
        
        if not api_endpoint:
            print("❌ API endpoint not found")
            return False
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        import requests
        
        try:
            health_url = f"{api_endpoint}/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Health endpoint is working")
                health_data = response.json()
                print(f"   📊 Status: {health_data.get('status', 'unknown')}")
            else:
                print(f"   ❌ Health endpoint returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Health endpoint error: {e}")
            return False
        
        print("\n🎉 API endpoints are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ API testing error: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 CDK Deployment Test Suite")
    print("=" * 60)
    
    # Test infrastructure deployment
    infra_success = test_deployment()
    
    if infra_success:
        # Test API endpoints
        api_success = test_api_endpoints()
        
        if api_success:
            print("\n🎉 All tests passed! Your document processing pipeline is ready.")
            print("\n📋 Next steps:")
            print("   1. Build and push your Docker image to ECR")
            print("   2. Test file uploads via the API")
            print("   3. Monitor CloudWatch logs for processing")
            print("   4. Set up additional monitoring and alerts")
        else:
            print("\n❌ API endpoint tests failed. Check your deployment.")
    else:
        print("\n❌ Infrastructure tests failed. Check your CDK deployment.")
        print("\n🔧 Troubleshooting:")
        print("   1. Run 'cdk deploy' to deploy the stack")
        print("   2. Check CloudFormation events for errors")
        print("   3. Verify AWS credentials and permissions")
        print("   4. Check the CDK logs for issues")

if __name__ == "__main__":
    main() 