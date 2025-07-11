# Phase 2 Implementation - Google Drive Integration & Enhanced Error Handling

## Overview

Phase 2 adds cloud storage integration, enhanced error handling with exponential backoff, and structured logging to the job instruction downloader.

## New Features

### 1. Google Drive Integration (`cloud_manager.py`)

- **OAuth Authentication**: Secure authentication with Google Drive API
- **Folder Management**: Automatic creation of department-based folder structure
- **File Upload**: Upload documents with proper naming and duplicate checking
- **Error Handling**: Robust error handling for API operations

#### Setup
1. Create Google Cloud Project and enable Drive API
2. Download credentials.json from Google Cloud Console
3. Place credentials.json in `config/` directory
4. Run authentication flow on first use

### 2. Enhanced Error Handling (`error_handler.py`)

- **Exponential Backoff**: Configurable retry logic with exponential delays
- **Jitter**: Random delay variation to prevent thundering herd
- **Decorator Support**: Easy retry decoration for functions
- **Configurable**: Retry attempts, delays, and backoff settings

#### Configuration
```json
{
  "error_handling": {
    "retry_attempts": 3,
    "retry_delay": 5,
    "exponential_backoff": true,
    "refresh_page_on_error": true,
    "skip_on_repeated_failure": true
  }
}
```

### 3. Structured Logging (`structured_logger.py`)

- **JSON Format**: Machine-readable log entries
- **Operation Tracking**: Context-aware logging with operation metadata
- **Timed Operations**: Automatic duration tracking
- **File Rotation**: Configurable log file size and backup management

#### Features
- Department and document context in logs
- Operation duration tracking
- Structured error reporting
- Configurable log levels and output

### 4. Enhanced JobInstruction Model

New fields for cloud storage tracking:
- `local_path`: Local file path
- `cloud_status`: Upload status
- `cloud_file_id`: Google Drive file ID
- `download_timestamp`: Download completion time
- `upload_timestamp`: Upload completion time

## Usage Examples

### Cloud Upload
```python
downloader = DocumentDownloader(config)
downloader.setup_cloud_storage()

success = downloader.upload_to_cloud(
    file_path="/path/to/document.docx",
    department_name="Отдел кадров",
    document_title="Должностная инструкция менеджера"
)
```

### Error Handling with Retry
```python
error_handler = EnhancedErrorHandler(config)

result = error_handler.retry_with_backoff(
    risky_operation,
    arg1, arg2,
    keyword_arg="value"
)
```

### Structured Logging
```python
structured_logger = StructuredLogger(config)

with structured_logger.timed_operation(
    logger, "info", "Processing document",
    operation="document_processing",
    department="HR",
    document_title="Job Description"
):
    # Process document
    pass
```

## Configuration

### Cloud Storage Settings
```json
{
  "cloud_storage": {
    "default_provider": "google_drive",
    "create_folders_automatically": true,
    "check_duplicates": true,
    "credentials_path": "config/credentials.json",
    "root_folder_name": "Job Instructions",
    "cleanup_after_upload": false
  }
}
```

### Logging Settings
```json
{
  "logging": {
    "file_path": "logs/app.log",
    "max_file_size": "10MB",
    "backup_count": 5,
    "console_output": true,
    "structured_logging": true,
    "detailed_logs": {
      "cloud_operations": true
    }
  }
}
```

## Testing

Comprehensive test suite includes:
- Unit tests for all new components
- Integration tests for complete workflows
- Mock-based testing for external APIs
- Russian character handling tests

Run tests:
```bash
pytest job_instruction_downloader/tests/ -v
```

## Dependencies

New dependencies added:
- `google-api-python-client`: Google Drive API
- `google-auth-httplib2`: Authentication
- `google-auth-oauthlib`: OAuth flow

## Security

- OAuth tokens stored securely in `config/token.json`
- Credentials file excluded from version control
- Minimal required API scopes (`drive.file`)

## Performance

- Exponential backoff prevents API rate limiting
- Duplicate checking reduces unnecessary uploads
- Structured logging optimized for performance
- Optional local file cleanup after upload
