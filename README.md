# VS Code Extension Downloader

A command-line tool to download VS Code extensions from the marketplace.

## Features

- Search for extensions by name
- Show detailed extension information:
  - Display name and publisher
  - Version number
  - Description
  - Installation count
  - Rating and number of ratings
- Interactive mode for extension name input
- Download VSIX files directly from the VS Code Marketplace
- Progress tracking for downloads
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
The tool will prompt you to:
1. Enter the extension name
2. Review extension details
3. Confirm download (press Enter or 'y' to proceed, 'n' to cancel)

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

## Error Handling

The tool includes robust error handling for:
- Network connection issues (with automatic retry)
- Invalid extension names
- Missing output directory (automatically created)
- API response errors

## Note

This tool uses the official VS Code Marketplace API to search for and download extensions.
