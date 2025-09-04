# #!/usr/bin/env python3
# """
# CDK Stack for Document Processing Pipeline
# """

# import aws_cdk as cdk
# from aws_cdk import (
#     Stack,
#     aws_s3 as s3,
#     aws_s3_notifications as s3n,
#     aws_lambda as _lambda,
#     aws_apigatewayv2 as apigwv2,
#     aws_apigatewayv2_integrations as apigwv2_integrations,
#     aws_iam as iam,
#     aws_logs as logs,
#     aws_ecr as ecr,
#     aws_apigateway as apigw,
#     aws_ecr_assets as ecr_assets,
#     Duration,
#     RemovalPolicy,
#     CfnOutput
# )
# from constructs import Construct
# import cdk_ecr_deployment as ecrdeploy
# import uuid

# class DocumentProcessingStack(Stack):
#     def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
#         super().__init__(scope, construct_id, **kwargs)

#         # ============================================================================
#         # S3 Bucket for Document Storage
#         # ============================================================================
        
#         # Create S3 bucket for document uploads
#         self.documents_bucket = s3.Bucket(
#             self, "DocumentsBucket",
#             bucket_name=f"{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}-dxhub-ub-bkt",
#             versioned=True,
#             encryption=s3.BucketEncryption.S3_MANAGED,
#             block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
#             removal_policy=RemovalPolicy.RETAIN,  # Keep data when stack is deleted
#             lifecycle_rules=[
#                 # For CURRENT objects
#                 s3.LifecycleRule(
#                     id="CurrentObjectsPolicy",
#                     transitions=[
#                         s3.Transition(
#                             storage_class=s3.StorageClass.INFREQUENT_ACCESS,
#                             transition_after=Duration.days(30)
#                         ),
#                         s3.Transition(
#                             storage_class=s3.StorageClass.GLACIER,
#                             transition_after=Duration.days(90)
#                         ),
#                     ],
#                     expiration=Duration.days(365),
#                 ),

#                 # For NONCURRENT versions (after updates/deletes)
#                 s3.LifecycleRule(
#                     id="NoncurrentVersionsPolicy",
#                     noncurrent_version_transitions=[
#                         s3.NoncurrentVersionTransition(
#                             storage_class=s3.StorageClass.INFREQUENT_ACCESS,
#                             transition_after=Duration.days(30)   # ≥30 required by S3
#                         ),
#                     ],
#                     noncurrent_version_expiration=Duration.days(60),  # > 30 to satisfy constraint
#                 ),
#             ]
#         )

#         # ============================================================================
#         # IAM Roles and Policies
#         # ============================================================================
        
#         # Lambda execution role
#         lambda_execution_role = iam.Role(
#             self, "LambdaExecutionRole",
#             assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
#             managed_policies=[
#                 iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
#                 iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
#             ]
#         )

#         # Add custom policies for S3 access
#         lambda_execution_role.add_to_policy(
#             iam.PolicyStatement(
#                 effect=iam.Effect.ALLOW,
#                 actions=[
#                     "s3:GetObject",
#                     "s3:GetObjectVersion",
#                     "s3:PutObject",
#                     "s3:DeleteObject",
#                     "s3:ListBucket"
#                 ],
#                 resources=[
#                     self.documents_bucket.bucket_arn,
#                     f"{self.documents_bucket.bucket_arn}/*"
#                 ]
#             )
#         )

#         # Add Bedrock permissions
#         lambda_execution_role.add_to_policy(
#             iam.PolicyStatement(
#                 effect=iam.Effect.ALLOW,
#                 actions=[
#                     "bedrock:InvokeModel",
#                     "bedrock:InvokeModelWithResponseStream"
#                 ],
#                 resources=["*"]
#             )
#         )

#         # ============================================================================
#         # Results / Output S3 Bucket
#         # ============================================================================
#         self.results_bucket = s3.Bucket(
#             self, "ResultsBucket",
#             bucket_name=f"{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}-dxhub-results-bkt",
#             versioned=True,
#             encryption=s3.BucketEncryption.S3_MANAGED,
#             block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
#             removal_policy=RemovalPolicy.RETAIN,
#         )

#         # Give the container Lambda permission to PUT results there
#         lambda_execution_role.add_to_policy(
#             iam.PolicyStatement(
#                 effect=iam.Effect.ALLOW,
#                 actions=["s3:PutObject", "s3:AbortMultipartUpload", "s3:ListBucketMultipartUploads"],
#                 resources=[f"{self.results_bucket.bucket_arn}/*"]
#             )
#         )

#         # (Optional) allow GET if your workflow reads back its own outputs
#         lambda_execution_role.add_to_policy(
#             iam.PolicyStatement(
#                 effect=iam.Effect.ALLOW,
#                 actions=["s3:GetObject"],
#                 resources=[f"{self.results_bucket.bucket_arn}/*"]
#             )
#         )


#         # ============================================================================
#         # Lambda Function (Container Image)
#         # ============================================================================

#         # Create ECR repository for the container image
#         ecr_repository = ecr.Repository(
#             self, "POWorkflowRepository",
#             repository_name=f"po-workflow-repository",
#             removal_policy=RemovalPolicy.RETAIN,  # Delete ECR repo when stack is deleted
#             image_scan_on_push=True,
#             lifecycle_rules=[
#                 ecr.LifecycleRule(
#                     max_image_count=10,  # Keep last 10 images
#                     rule_priority=1
#                 )
#             ]
#         )

#         asset = ecr_assets.DockerImageAsset(
#             self,
#             "LocalDockerImage",
#             directory="../lambda/po-workflow",  # folder with your Dockerfile and code
#         )

#         push = ecrdeploy.ECRDeployment(
#             self,
#             "PushToRepo",
#             src=ecrdeploy.DockerImageName(asset.image_uri),
#             dest=ecrdeploy.DockerImageName(f"{ecr_repository.repository_uri}:latest"),
#         )

#         # Lambda function using container image
#         self.po_workflow_lambda = _lambda.DockerImageFunction(
#             self, "POWorkflowLambda",
#             function_name=f"po-workflow-lambda",
#             code=_lambda.DockerImageCode.from_ecr(
#                 repository=ecr_repository,
#                 tag_or_digest="latest"  # You can specify a specific tag here
#             ),
#             role=lambda_execution_role,
#             timeout=Duration.minutes(15),  # 15 minute timeout for document processing
#             memory_size=1024,  # 1GB memory
#             environment={
#                 "DOCUMENTS_BUCKET": self.documents_bucket.bucket_name,
#                 "LOG_LEVEL": "INFO",
#                 "MAX_DOCUMENTS_PER_BATCH": "10",
#                 "BATCH_DELAY_SECONDS": "1.0"
#             },
#             log_retention=logs.RetentionDays.ONE_MONTH,
#             #reserved_concurrent_executions=5,  # Limit concurrent executions to prevent throttling
#             vpc=None,  # Set to your VPC if needed
#             vpc_subnets=None  # Set to your subnet selection if using VPC
#         )

#         # Add RESULTS_BUCKET env to the container lambda
#         self.po_workflow_lambda.add_environment("RESULTS_BUCKET", self.results_bucket.bucket_name)

#         self.po_workflow_lambda.node.add_dependency(push)
#         ecr_repository.grant_pull(self.po_workflow_lambda.role)

#         # ============================================================================
#         # S3 Event Trigger
#         # ============================================================================
        
#         # Add S3 trigger for new document uploads
#         self.documents_bucket.add_event_notification(
#             s3.EventType.OBJECT_CREATED,
#             s3n.LambdaDestination(self.po_workflow_lambda),
#             s3.NotificationKeyFilter(suffix=".pdf")  # Trigger on PDF uploads
#         )

#         # Also trigger on other common document formats
#         self.documents_bucket.add_event_notification(
#             s3.EventType.OBJECT_CREATED,
#             s3n.LambdaDestination(self.po_workflow_lambda),
#             s3.NotificationKeyFilter(suffix=".docx")
#         )

#         self.documents_bucket.add_event_notification(
#             s3.EventType.OBJECT_CREATED,
#             s3n.LambdaDestination(self.po_workflow_lambda),
#             s3.NotificationKeyFilter(suffix=".txt")
#         )

#         # ============================================================================
#         # API Gateway for File Uploads
#         # ============================================================================

#         # ---- Lambda Layer: requests-toolbelt (for multipart/form-data parsing) ----
#         requests_toolbelt_layer = _lambda.LayerVersion(
#             self,
#             "RequestsToolbeltLayer",
#             code=_lambda.Code.from_asset(
#                 path="../layers/requests_toolbelt",
#                 # NOTE: Use cdk.BundlingOptions (NOT aws_lambda.BundlingOptions)
#                 bundling=cdk.BundlingOptions(
#                     # Good default Python 3.11 build image
#                     image=_lambda.Runtime.PYTHON_3_11.bundling_image,
#                     # Create the correct layer layout: /python site-packages at layer root
#                     command=[
#                         "bash", "-lc",
#                         "pip install --no-cache-dir requests-toolbelt -t /asset-output/python"
#                     ],
#                 ),
#             ),
#             compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
#             description="Layer with requests-toolbelt for multipart parsing",
#         )
#         # Create Lambda function for handling file uploads
#         upload_handler_lambda = _lambda.Function(
#             self, "UploadHandlerLambda",
#             function_name=f"{self.stack_name.lower()}-upload-handler",
#             runtime=_lambda.Runtime.PYTHON_3_11,
#             handler="upload_to_s3.lambda_handler",
#             code=_lambda.Code.from_asset("../lambda/upload_to_s3"),
#             role=lambda_execution_role,
#             timeout=Duration.minutes(5),
#             memory_size=512,
#             environment={
#                 "DOCUMENTS_BUCKET": self.documents_bucket.bucket_name,
#                 "MAX_FILE_SIZE_MB": "50"
#             },
#             layers=[requests_toolbelt_layer],  # <-- add this line
#         )

#         # Add S3 upload permissions to upload handler
#         upload_handler_lambda.add_to_role_policy(
#             iam.PolicyStatement(
#                 effect=iam.Effect.ALLOW,
#                 actions=[
#                     "s3:PutObject",
#                     "s3:PutObjectAcl"
#                 ],
#                 resources=[
#                     f"{self.documents_bucket.bucket_arn}/*"
#                 ]
#             )
#         )

#         # API Gateway REST API
#         api = apigw.RestApi(
#             self, "UploadFileRestApi",
#             rest_api_name="upload-file-rest",
#             deploy=True
#         )

#         # Resource: /upload
#         upload_resource = api.root.add_resource("upload")

#         # Method: POST → Lambda proxy
#         upload_resource.add_method(
#             "POST",
#             apigw.LambdaIntegration(
#                 upload_handler_lambda,
#                 proxy=True
#             )
#         )


#         # ============================================================================
#         # CloudWatch Alarms and Monitoring
#         # ============================================================================
        
#         # Create CloudWatch alarm for Lambda errors
#         error_alarm = cdk.aws_cloudwatch.Alarm(
#             self, "DocumentProcessorErrorAlarm",
#             metric=self.po_workflow_lambda.metric_errors(),
#             threshold=5,
#             evaluation_periods=2,
#             alarm_description="Alert when document processor Lambda has errors"
#         )

#         # Create CloudWatch alarm for Lambda duration
#         duration_alarm = cdk.aws_cloudwatch.Alarm(
#             self, "DocumentProcessorDurationAlarm",
#             metric=self.po_workflow_lambda.metric_duration(),
#             threshold=Duration.minutes(10).to_milliseconds(),
#             evaluation_periods=2,
#             alarm_description="Alert when document processor Lambda takes too long"
#         )

#         # ============================================================================
#         # Outputs
#         # ============================================================================
        
#         CfnOutput(
#             self, "DocumentsBucketName",
#             value=self.documents_bucket.bucket_name,
#             description="Name of the S3 bucket for document storage"
#         )

#         CfnOutput(
#             self, "ECRRepositoryUri",
#             value=ecr_repository.repository_uri,
#             description="URI of the ECR repository for the document processor container"
#         )

#         CfnOutput(
#             self, "APIEndpoint",
#             value=api.url,
#             description="API Gateway endpoint for file uploads"
#         )

#         CfnOutput(
#             self, "DocumentProcessorLambdaArn",
#             value=self.po_workflow_lambda.function_arn,
#             description="ARN of the document processor Lambda function"
#         )

#         CfnOutput(
#             self, "ResultsBucketName",
#             value=self.results_bucket.bucket_name,
#             description="Name of the S3 bucket for workflow results"
#         )


#         # ============================================================================
#         # Tags
#         # ============================================================================
        
#         cdk.Tags.of(self).add("Project", "DocumentProcessingPipeline")
#         cdk.Tags.of(self).add("Environment", "Production")
#         cdk.Tags.of(self).add("ManagedBy", "CDK") 