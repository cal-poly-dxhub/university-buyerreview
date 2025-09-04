# """
# Configuration file for document processing limits and throttling protection.
# Adjust these values based on your Bedrock service limits and requirements.
# """

# # Document Processing Limits
# MAX_DOCUMENTS_PER_BATCH = 4  # Maximum documents to process simultaneously
# BATCH_DELAY_SECONDS = 1.0    # Delay between batches to avoid throttling

# # Bedrock API Limits (adjust based on your service tier)
# MAX_CONCURRENT_REQUESTS = 4   # Maximum concurrent Bedrock API calls
# REQUEST_TIMEOUT_SECONDS = 30  # Timeout for individual Bedrock requests

# # File Size Limits
# MAX_FILE_SIZE_MB = 4.5       # Maximum file size in MB before compression
# MAX_TOTAL_BATCH_SIZE_MB = 20 # Maximum total size of documents in a batch

# # Retry Configuration
# MAX_RETRIES = 3              # Maximum retry attempts for failed requests
# RETRY_DELAY_SECONDS = 2.0    # Delay between retry attempts

# # Performance Monitoring
# ENABLE_PROGRESS_LOGGING = True  # Enable detailed progress logging
# ENABLE_PERFORMANCE_METRICS = True  # Enable performance timing metrics

# # Throttling Protection
# ENABLE_THROTTLING_PROTECTION = True  # Enable automatic throttling protection
# THROTTLING_BACKOFF_MULTIPLIER = 1.5  # Multiplier for exponential backoff
# MAX_BACKOFF_SECONDS = 10.0   # Maximum backoff delay

# def get_processing_config():
#     """
#     Get the current processing configuration as a dictionary.
#     """
#     return {
#         "max_documents_per_batch": MAX_DOCUMENTS_PER_BATCH,
#         "batch_delay_seconds": BATCH_DELAY_SECONDS,
#         "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
#         "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
#         "max_file_size_mb": MAX_FILE_SIZE_MB,
#         "max_total_batch_size_mb": MAX_TOTAL_BATCH_SIZE_MB,
#         "max_retries": MAX_RETRIES,
#         "retry_delay_seconds": RETRY_DELAY_SECONDS,
#         "enable_progress_logging": ENABLE_PROGRESS_LOGGING,
#         "enable_performance_metrics": ENABLE_PERFORMANCE_METRICS,
#         "enable_throttling_protection": ENABLE_THROTTLING_PROTECTION,
#         "throttling_backoff_multiplier": THROTTLING_BACKOFF_MULTIPLIER,
#         "max_backoff_seconds": MAX_BACKOFF_SECONDS
#     }

# def validate_config():
#     """
#     Validate the configuration values and return any warnings.
#     """
#     warnings = []
    
#     if MAX_DOCUMENTS_PER_BATCH > 10:
#         warnings.append("MAX_DOCUMENTS_PER_BATCH > 10 may cause throttling issues")
    
#     if BATCH_DELAY_SECONDS < 0.5:
#         warnings.append("BATCH_DELAY_SECONDS < 0.5 may not provide sufficient throttling protection")
    
#     if MAX_CONCURRENT_REQUESTS > MAX_DOCUMENTS_PER_BATCH:
#         warnings.append("MAX_CONCURRENT_REQUESTS should not exceed MAX_DOCUMENTS_PER_BATCH")
    
#     return warnings 