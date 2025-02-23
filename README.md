# VS Code Extension Downloader

A command-line tool to download VS Code extensions from the marketplace.

## Features

- Smart extension search with relevance scoring:
  - Name matching (40%)
  - Download count (30%)
  - Ratings (20%)
  - Last updated date (10%)
- Show top 5 most relevant extensions with detailed information:
  - Display name and publisher
  - Version number
  - Description
  - Installation count
  - Rating and number of ratings
  - Relevance score
- Interactive selection from multiple matches
- Progress bar for downloads
- Automatic retry on network errors

## Requirements

- Python 3.6 or higher
- Required packages (install via pip):
  ```bash
  pip install -r requirements.txt
  ```

## Usage

### Interactive Mode
Simply run without any arguments:
```bash
python vsix_downloader.py
```
The tool will:
1. Prompt for extension name
2. Show top 5 matching extensions with relevance scores
3. Let you choose from multiple matches (if found)
4. Display detailed extension information
5. Ask for download confirmation
6. Show download progress

### Command Line Mode
Directly specify the extension name:
```bash
python vsix_downloader.py gitlens
```

### Options

- `-o, --output-dir`: Specify output directory (default: current directory)
  ```bash
  python vsix_downloader.py gitlens -o downloads/
  ```

- `-v, --verbose`: Enable verbose output
  ```bash
  python vsix_downloader.py gitlens -v
  ```

The downloaded file will be named in the format:
`{publisher}.{extension_id}-{version}.vsix`

For example:
`eamodio.gitlens-2025.2.2304.vsix`

## Extension Scoring

Extensions are scored based on multiple factors to help you find the most relevant ones:

- **Name Matching (40 points)**
  - Exact match: 40 points
  - Contains as whole word: 30 points
  - Contains as part: 20 points

- **Download Count (30 points)**
  - Logarithmic scale based on number of downloads
  - More downloads = higher score (up to 30 points)

- **Ratings (20 points)**
  - Based on average rating and number of ratings
  - Higher ratings and more reviews = higher score

- **Update Frequency (10 points)**
  - Based on how recently the extension was updated
  - More recent updates = higher score

Only the top 5 scored extensions are displayed to avoid information overload.

## Error Handling

The tool includes robust error handling for:
- Network connection issues (with automatic retry)
- Invalid extension names
- Missing output directory (automatically created)
- API response errors
- User cancellation (during selection or download)

## Note

This tool uses the official VS Code Marketplace API to search for and download extensions.
