# Changelog

All notable changes to the VSIX Downloader project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-03-06

### Added
- Explicit timeouts for all network requests
- SSL verification for all requests
- Input validation for extension names
- Directory validation with permission checks
- File verification after download
- File cleanup for failed downloads
- Detailed error messages for different failure types
- Support for non-interactive environments
- Better handling of date formats in extension scoring
- Auto-selection in non-interactive mode

### Fixed
- Session resource leak in network requests
- Potential IndexError when accessing versions array
- Integer overflow risk in scoring functions
- Improved error handling for network timeouts
- Fixed crash when stdin is not available
- Better error recovery during downloads
- Protected against file system errors
- Improved date parsing logic for different formats
- Fixed incomplete error handling in API requests

### Changed
- Network timeout defaults (30s for API, 120s for downloads)
- Added bounds checking for extremely large install counts
- Enhanced file system interaction with proper error handling
- Improved scoring algorithm error handling
- Updated download progress reporting

## [1.0.0] - 2025-03-01

### Added
- Initial release
- Extension search and download functionality
- Smart extension search with relevance scoring
- Interactive extension selection
- Progress bar for downloads
- Retry mechanism for network errors