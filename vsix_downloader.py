#!/usr/bin/env python3
"""
VSIX Downloader - A tool to download VS Code extensions from the marketplace.

This script automates the process of downloading VSIX files from the Visual Studio Code
marketplace by using the marketplace API to search for and download extensions.
"""

import argparse
import os
import sys
from typing import Optional, Tuple, List, Dict
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
    
    def _extract_from_search(self, extension_name: str) -> Dict:
        """
        Search for extension and extract information from search results.
        
        Args:
            extension_name: Name of the extension to search for
            
        Returns:
            Dictionary containing extension information including:
            - publisher_name: Publisher name
            - extension_id: Extension ID
            - version: Version number
            - display_name: Display name of the extension
            - short_description: Short description
            - install_count: Number of installations
            - rating: Average rating
            - rating_count: Number of ratings
            
        Raises:
            ValueError: If extension cannot be found
            requests.RequestException: If network request fails
        """
        self.logger.debug(f"Searching marketplace API for: {extension_name}")
        
        url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
        data = {
            "filters": [{
                "criteria": [{
                    "filterType": 8,
                    "value": "Microsoft.VisualStudio.Code"
                }, {
                    "filterType": 10,
                    "value": extension_name
                }],
                "pageNumber": 1,
                "pageSize": 50
            }],
            "flags": self._get_api_flags('search')
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        results = response.json()
        if not results.get("results"):
            raise ValueError(f"No extensions found matching: {extension_name}")
            
        extensions = results["results"][0].get("extensions", [])
        if not extensions:
            raise ValueError(f"No extensions found matching: {extension_name}")
            
        extension = extensions[0]
        statistics = {stat["statisticName"]: stat["value"] 
                     for stat in extension.get("statistics", [])}
        
        # Format install count with commas
        install_count = int(statistics.get("install", 0))
        formatted_install_count = "{:,}".format(install_count)
        
        # Format rating
        weighted_rating = float(statistics.get("weightedRating", 0))
        rating = round(weighted_rating / 5, 2) if weighted_rating else 0
        rating_count = int(statistics.get("ratingcount", 0))
        
        extension_info = {
            "publisher_name": extension["publisher"]["publisherName"],
            "extension_id": extension["extensionName"],
            "version": extension["versions"][0]["version"],
            "display_name": extension.get("displayName", extension["extensionName"]),
            "short_description": extension.get("shortDescription", ""),
            "install_count": formatted_install_count,
            "rating": rating,
            "rating_count": rating_count
        }
        
        # Log extension statistics
        self.logger.info(f"Extension install count: {extension_info['install_count']}")
        self.logger.info(f"Extension rating: {extension_info['rating']}")
        self.logger.info(f"Number of ratings: {extension_info['rating_count']}")
        
        return extension_info
    
    def extract_extension_info(self, extension_name: str) -> Dict:
        """
        Search for and extract extension information from the marketplace.
        
        Args:
            extension_name: Name of the extension to search for
            
        Returns:
            Dictionary containing extension information
            
        Raises:
            ValueError: If extension cannot be found or information cannot be extracted
            requests.RequestException: If network request fails
        """
        return self._extract_from_search(extension_name)
    
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
        extension_info = self.extract_extension_info(extension_name)
        
        # Construct download URL
        download_url = self.construct_download_url(extension_info['publisher_name'], extension_info['extension_id'], extension_info['version'])
        
        # Construct output filename
        output_file = os.path.join(output_dir, f"{extension_info['publisher_name']}.{extension_info['extension_id']}-{extension_info['version']}.vsix")
        
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
        nargs='?',  # Make it optional
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
    
    # Create logger with appropriate level
    logger = ConsoleLogger()
    logger.set_level('DEBUG' if args.verbose else 'INFO')
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Get extension name from argument or prompt user
        extension_name = args.extension_name
        if not extension_name:
            while True:
                extension_name = input("\nEnter the name of the VS Code extension to download: ").strip()
                if extension_name:
                    break
                print("Please enter a valid extension name.")
        
        # Create downloader instance
        downloader = VSIXDownloader(logger)
        
        # Search for extension and get information
        extension_info = downloader.extract_extension_info(extension_name)
        
        # Display extension information
        print("\nFound Extension:")
        print(f"Name: {extension_info['display_name']}")
        print(f"Publisher: {extension_info['publisher_name']}")
        print(f"Version: {extension_info['version']}")
        print(f"Description: {extension_info['short_description']}")
        print(f"Install Count: {extension_info['install_count']}")
        print(f"Rating: {extension_info['rating']} ({extension_info['rating_count']} ratings)")
        
        # Ask for confirmation
        while True:
            response = input("\nDo you want to download this extension? [Y/n]: ").lower()
            if not response:  # 如果用户直接回车
                response = 'y'
            if response in ['y', 'n']:
                break
            print("Please enter 'y' for yes or 'n' for no (or press Enter for yes).")
        
        if response == 'n':
            print("Download cancelled.")
            return
        
        # Download the extension
        file_path = downloader.download_extension(
            extension_name,
            args.output_dir
        )
        print(f"\nExtension downloaded successfully to: {file_path}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
