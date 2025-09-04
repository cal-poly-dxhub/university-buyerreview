#!/usr/bin/env python3
"""
CDK App for Document Processing Pipeline
"""

import aws_cdk as cdk
from document_processing_stack import DocumentProcessingStack

app = cdk.App()

# Create the document processing stack
DocumentProcessingStack(app, "DocumentProcessingStack",
    env=cdk.Environment(
        account=app.node.try_get_context('account'),
        region=app.node.try_get_context('region')
    ),
    description="Document processing pipeline with S3 triggers and Lambda container"
)

app.synth() 