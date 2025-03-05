# VSIX Downloader Project To-Do List

## Core Functionality
- [x] Create Python script file
  - Create `vsix_downloader.py`
  - Add basic script structure
- [x] Implement argument parsing
  - Add extension name argument
  - Add optional output directory parameter
  - Add verbose mode flag
- [x] Implement marketplace search
  - Setup requests for marketplace search
  - Parse search results page
  - Find exact extension match
- [x] Implement value extraction
  - Parse extension details page
  - Extract publisher name (fieldA)
  - Extract extension name (fieldB)
  - Get latest version number
- [x] Implement URL construction
  - Build download URL template
  - Insert extracted values into URL
- [x] Implement file download
  - Setup requests for file download
  - Save file with appropriate name
  - Handle download progress

## Error Handling
- [x] Handle extension not found
- [x] Handle network errors
- [x] Handle parsing failures
- [x] Add meaningful error messages
- [x] Add troubleshooting suggestions

## Output & Logging
Guideline: use logging module from log_utils.py, usage example is:
```python
from log_utils import ConsoleLogger

def process_user_data(user_id: int):
    logger = ConsoleLogger()
    
    logger.debug(f"Processing user data for ID: {user_id}")
    
    # Simulate some processing steps
    logger.info("Fetching user profile")
    
    # Simulate a warning condition
    if user_id > 1000:
        logger.warning("High user ID detected")
    
    # Simulate an error condition
    if user_id <= 0:
        logger.error("Invalid user ID")
        return
    
    # Simulate a critical error
    try:
        if user_id == 999:
            raise Exception("Special error case")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
    
    logger.info("Processing completed successfully")

if __name__ == "__main__":
    # Test with different scenarios
    process_user_data(1)      # Normal case
    process_user_data(1001)   # Warning case
    process_user_data(0)      # Error case
    process_user_data(999)    # Critical case
```
- [x] Add progress messages
- [x] Add success message
- [x] Implement verbose mode
- [x] Add download statistics

## Dependencies
- [x] Add requirements.txt
  - Add requests
  - Add argparse

## Additional Features
- [x] Add version check
- [x] Add help documentation
- [x] Add unit tests
- [] Add CI/CD pipeline
