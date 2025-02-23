# VS Code Extension Downloader

A command-line tool to download VS Code extensions from the marketplace.

## Features

- Search for extensions by name
- Download VSIX files directly from the VS Code Marketplace
- Show extension statistics (install count, ratings)
- Progress tracking for downloads
- Automatic retry on network errors

## Requirements

- Python 3.6 or higher
- Required packages (install via pip):
  ```bash
  pip install -r requirements.txt
  ```

## Usage

Basic usage:
```bash
python vsix_downloader.py <extension_name>
```

Example:
```bash
python vsix_downloader.py gitlens
```

### Options

- `-o, --output-dir`: Specify output directory (default: current directory)
- `-v, --verbose`: Enable verbose output

Example with options:
```bash
python vsix_downloader.py gitlens -o downloads/ -v
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
