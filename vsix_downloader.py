#!/usr/bin/env python3
"""
VSIX Downloader - A tool to download VS Code extensions from the marketplace.

This script automates the process of downloading VSIX files from the Visual Studio Code
marketplace by using the marketplace API to search for and download extensions.
"""

import argparse
import os
import sys
from typing import Optional, Tuple, List
import requests
from requests.adapters import HTTPAdapter, Retry
from log_utils import ConsoleLogger

class VSIXDownloader:
    """Main class for handling VSIX file downloads from VS Code marketplace."""
    
    # API flags for different types of information
    FLAG_INCLUDE_VERSIONS = 0x1
    FLAG_INCLUDE_FILES = 0x2
    FLAG_INCLUDE_CATEGORIES = 0x4
    FLAG_INCLUDE_SHARED_ACCOUNTS = 0x8
    FLAG_INCLUDE_VERSION_PROPERTIES = 0x10
    FLAG_INCLUDE_INSTALLATION_TARGETS = 0x40
    FLAG_INCLUDE_ASSET_URI = 0x80
    FLAG_INCLUDE_STATISTICS = 0x100
    FLAG_INCLUDE_LATEST_VERSION = 0x200
    FLAG_INCLUDE_NAME_CONFLICT = 0x8000
    
    # Predefined flag combinations for different operations
    FLAGS_SEARCH = FLAG_INCLUDE_LATEST_VERSION | FLAG_INCLUDE_STATISTICS
    FLAGS_DOWNLOAD = FLAG_INCLUDE_LATEST_VERSION | FLAG_INCLUDE_FILES | FLAG_INCLUDE_ASSET_URI
    FLAGS_DETAILED = (FLAG_INCLUDE_VERSIONS | FLAG_INCLUDE_FILES | FLAG_INCLUDE_CATEGORIES |
                     FLAG_INCLUDE_VERSION_PROPERTIES | FLAG_INCLUDE_INSTALLATION_TARGETS |
                     FLAG_INCLUDE_STATISTICS | FLAG_INCLUDE_ASSET_URI)
    
    def __init__(self, logger: Optional[ConsoleLogger] = None):
        """
        Initialize the VSIX downloader.
        
        Args:
            logger: Optional ConsoleLogger instance. If not provided, a new one will be created.
        """
        self.logger = logger or ConsoleLogger()
        
        # Setup session with retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set a user agent to avoid potential blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def _get_api_flags(self, operation: str = 'search', additional_flags: List[int] = None) -> int:
        """
        Get the appropriate combination of API flags for the requested operation.
        
        Args:
            operation: The type of operation ('search', 'download', or 'detailed')
            additional_flags: Optional list of additional flags to include
            
        Returns:
            Combined flags value
            
        Raises:
            ValueError: If operation is not recognized
        """
        base_flags = {
            'search': self.FLAGS_SEARCH,
            'download': self.FLAGS_DOWNLOAD,
            'detailed': self.FLAGS_DETAILED
        }.get(operation.lower())
        
        if base_flags is None:
            raise ValueError(f"Unknown operation: {operation}")
        
        if additional_flags:
            for flag in additional_flags:
                base_flags |= flag
        
        return base_flags
    
    def extract_extension_info(self, extension_name: str) -> Tuple[str, str, str]:
        """
        Search for and extract extension information from the marketplace.
        
        Args:
            extension_name: Name of the extension to search for
            
        Returns:
            Tuple containing (publisher_name, extension_id, version)
            
        Raises:
            ValueError: If extension cannot be found or information cannot be extracted
            requests.RequestException: If network request fails
        """
        self.logger.info(f"Searching for extension: {extension_name}")
        return self._extract_from_search(extension_name)
    
    def _extract_from_search(self, extension_name: str) -> Tuple[str, str, str]:
        """
        Search for extension and extract information from search results.
        
        Args:
            extension_name: Name of the extension to search for
            
        Returns:
            Tuple containing (publisher_name, extension_id, version)
            
        Raises:
            ValueError: If extension cannot be found
            requests.RequestException: If network request fails
        """
        search_url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
        
        # Get flags for search operation
        flags = self._get_api_flags('search')
        
        # API request payload
        payload = {
            "filters": [{
                "criteria": [{
                    "filterType": 8,
                    "value": "Microsoft.VisualStudio.Code"
                }, {
                    "filterType": 10,
                    "value": extension_name
                }],
                "pageNumber": 1,
                "pageSize": 1,
                "sortBy": 0,
                "sortOrder": 0
            }],
            "assetTypes": [],
            "flags": flags
        }
        
        headers = {
            'Accept': 'application/json; charset=utf-8; api-version=7.2-preview.1',
            'Content-Type': 'application/json'
        }
        
        self.logger.debug(f"Searching marketplace API for: {extension_name}")
        response = self.session.post(search_url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        if not results or not results[0].get('extensions'):
            raise ValueError(f"No extensions found matching '{extension_name}'")
            
        # Get the first extension result
        extension = results[0]['extensions'][0]
        
        # Extract required information
        publisher_name = extension.get('publisher', {}).get('publisherName')
        extension_id = extension.get('extensionName')
        versions = extension.get('versions', [])
        
        if not publisher_name or not extension_id or not versions:
            raise ValueError("Could not extract extension information from search results")
            
        version = versions[0].get('version')
        if not version:
            raise ValueError("Could not find version information")
        
        # Log statistics if available
        statistics = extension.get('statistics', [])
        for stat in statistics:
            if stat['statisticName'] == 'install':
                self.logger.info(f"Extension install count: {stat['value']:,}")
            elif stat['statisticName'] == 'averagerating':
                self.logger.info(f"Extension rating: {stat['value']:.2f}")
            elif stat['statisticName'] == 'ratingcount':
                self.logger.info(f"Number of ratings: {stat['value']:,}")
        
        self.logger.debug(f"Found extension: {publisher_name}.{extension_id} version {version}")
        return publisher_name, extension_id, version
    
    def construct_download_url(self, publisher: str, extension_id: str, version: str) -> str:
        """
        Construct the download URL for the VSIX file.
        
        Args:
            publisher: Publisher name (fieldA)
            extension_id: Extension ID (fieldB)
            version: Version number
            
        Returns:
            Complete download URL for the VSIX file
        """
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{extension_id}/{version}/vspackage"
    
    def download_extension(self, extension_name: str, output_dir: str = '.') -> str:
        """
        Download a VS Code extension by name.
        
        Args:
            extension_name: Name of the extension to download
            output_dir: Directory to save the downloaded file (default: current directory)
            
        Returns:
            Path to the downloaded file
            
        Raises:
            ValueError: If extension cannot be found
            requests.RequestException: If download fails
            OSError: If output directory cannot be created/accessed
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get extension info
        publisher, extension_id, version = self.extract_extension_info(extension_name)
        
        # Construct download URL
        download_url = self.construct_download_url(publisher, extension_id, version)
        
        # Construct output filename
        output_file = os.path.join(output_dir, f"{publisher}.{extension_id}-{version}.vsix")
        
        # Download the file
        self.logger.info(f"Downloading extension from: {download_url}")
        self.logger.info(f"Saving to: {output_file}")
        
        response = self.session.get(download_url, stream=True)
        response.raise_for_status()
        
        # Get total file size for progress tracking
        total_size = int(response.headers.get('content-length', 0))
        
        # Download with progress tracking
        with open(output_file, 'wb') as f:
            if total_size == 0:
                self.logger.warning("Could not determine file size, downloading without progress tracking")
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) == 0:  # Log every 1MB
                            self.logger.info(f"Download progress: {progress:.1f}% ({downloaded/1024/1024:.1f}MB/{total_size/1024/1024:.1f}MB)")
        
        self.logger.info(f"Download completed: {output_file}")
        return output_file

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download VS Code extensions from the marketplace"
    )
    parser.add_argument(
        "extension_name",
        help="Name of the extension to download"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Directory to save the downloaded file (default: current directory)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Create logger
    logger = ConsoleLogger()
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Initialize downloader
        downloader = VSIXDownloader(logger)
        
        # Download the extension
        output_file = downloader.download_extension(args.extension_name, args.output_dir)
        
        logger.info(f"Successfully downloaded to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
