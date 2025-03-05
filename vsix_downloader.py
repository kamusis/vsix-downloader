#!/usr/bin/env python3
"""
VSIX Downloader - A tool to download VS Code extensions from the marketplace.

This script automates the process of downloading VSIX files from the Visual Studio Code
marketplace by using the marketplace API to search for and download extensions.
"""

import argparse
import os
import sys
from typing import Optional, Tuple, List, Dict, Any
import requests
from requests.adapters import HTTPAdapter, Retry
from log_utils import ConsoleLogger
import math
from datetime import datetime
from tqdm import tqdm

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
        
        # Enable SSL verification
        self.session.verify = True
        
        # Set default timeouts
        self.default_timeout = 30  # 30 seconds for regular requests
        self.download_timeout = 120  # 2 minutes for downloads
        
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
    
    def _score_extension(self, extension: Dict[str, Any], search_term: str) -> float:
        """
        Score an extension based on various factors.
        
        Args:
            extension: Extension data from API
            search_term: Original search term
            
        Returns:
            Score value (higher is better)
        """
        score = 0.0
        
        # 1. Name matching (max: 40 points)
        name = extension.get("extensionName", "").lower()
        display_name = extension.get("displayName", "").lower()
        search_term = search_term.lower()
        
        # Exact match gets highest score
        if search_term == name or search_term == display_name:
            score += 40
        # Contains as whole word
        elif f" {search_term} " in f" {name} " or f" {search_term} " in f" {display_name} ":
            score += 30
        # Contains as part
        elif search_term in name or search_term in display_name:
            score += 20
            
        # 2. Install count (max: 30 points)
        statistics = {stat["statisticName"]: stat["value"] 
                     for stat in extension.get("statistics", [])}
        try:
            # Handle extremely large values and potential overflow
            install_count = min(int(statistics.get("install", 0)), 1_000_000_000)  # Cap at 1 billion
        except (ValueError, TypeError):
            install_count = 0
            
        # Log scale for install count (0 to 30 points)
        if install_count > 0:
            try:
                score += min(30, math.log(install_count, 10) * 3)
            except (ValueError, OverflowError):
                # Fallback if math calculation fails
                score += 30  # Assume maximum for extremely large values
            
        # 3. Ratings (max: 20 points)
        weighted_rating = float(statistics.get("weightedRating", 0))
        rating_count = int(statistics.get("ratingCount", 0))
        # Combine rating value and count
        if rating_count > 0:
            rating_score = (weighted_rating / 5) * min(1, math.log(rating_count + 1, 100))
            score += min(20, rating_score * 20)  # Scale to max 20 points
            
        # 4. Last updated (max: 10 points)
        last_updated = extension.get("lastUpdated", "")
        if last_updated:
            try:
                # Handle different date formats
                if "." in last_updated:
                    # Parse date like "2024-02-23T12:00:00.000Z"
                    parts = last_updated.split(".")
                    if len(parts) >= 1:
                        date_part = parts[0]
                        # Try various formats
                        if "T" in date_part:
                            try:
                                updated_date = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S")
                            except ValueError:
                                updated_date = datetime.strptime(date_part, "%Y-%m-%d")
                        else:
                            updated_date = datetime.strptime(date_part, "%Y-%m-%d")
                else:
                    # Try to parse without milliseconds
                    updated_date = datetime.strptime(last_updated, "%Y-%m-%d")
                
                # Calculate age in days with bounds checking
                current_date = datetime.now()
                if updated_date > current_date:  # Future date
                    days_old = 0
                else:
                    days_old = (current_date - updated_date).days
                
                # Newer updates get more points (max 10 points, decreasing with age)
                score += max(0, 10 - min(10, days_old / 30))
            except (ValueError, TypeError, AttributeError, OverflowError) as e:
                # Better error logging for debugging
                self.logger.debug(f"Error parsing date '{last_updated}': {e}")
                pass
                
        return score

    def _extract_from_search(self, extension_name: str) -> Tuple[Dict[str, Any], float]:
        """
        Search for extension and extract information from search results.
        
        Args:
            extension_name: Name of the extension to search for
            
        Returns:
            Tuple containing:
            - Dictionary with extension information including:
              - publisher_name: Publisher name
              - extension_id: Extension ID
              - version: Version number
              - display_name: Display name of the extension
              - short_description: Short description
              - install_count: Number of installations
              - rating: Average rating
              - rating_count: Number of ratings
            - Score value indicating the relevance (0-100)
            
        Raises:
            ValueError: If extension cannot be found
            requests.RequestException: If network request fails
            KeyboardInterrupt: If user cancels the selection
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
        
        try:
            response = self.session.post(url, json=data, timeout=self.default_timeout)
            response.raise_for_status()
            
            results = response.json()
            if not results.get("results"):
                raise ValueError(f"No extensions found matching: {extension_name}")
                
            extensions = results["results"][0].get("extensions", [])
            if not extensions:
                raise ValueError(f"No extensions found matching: {extension_name}")
        except requests.exceptions.Timeout:
            raise ValueError(f"Request timed out while searching for: {extension_name}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Network error while searching for {extension_name}: {e}")
            
        # Score and sort extensions
        scored_extensions = [
            (self._score_extension(ext, extension_name), ext)
            for ext in extensions
        ]
        scored_extensions.sort(reverse=True)  # Sort by score descending
        
        total_results = len(extensions)
        print(f"\nFound {total_results} matching extensions (showing top 5 by relevance score)")
        print("Scoring is based on: name matching (40%), downloads (30%), ratings (20%), and update frequency (10%)")
        
        # Take top 5 results
        top_extensions = scored_extensions[:5]
        
        # If multiple extensions found, let user choose
        if len(top_extensions) > 1:
            print("\nTop matching extensions:")
            for i, (score, ext) in enumerate(top_extensions, 1):
                publisher = ext["publisher"]["publisherName"]
                display_name = ext.get("displayName", ext["extensionName"])
                short_desc = ext.get("shortDescription", "")[:100] + "..." if ext.get("shortDescription", "") else ""
                stats = {stat["statisticName"]: stat["value"] 
                        for stat in ext.get("statistics", [])}
                install_count = int(stats.get("install", 0))
                rating = float(stats.get("weightedRating", 0))
                rating_count = int(stats.get("ratingCount", 0))
                
                print(f"\n{i}. {display_name} by {publisher}")
                print(f"   Relevance score: {score:.1f}/100")
                print(f"   Downloads: {install_count:,}")
                print(f"   Rating: {rating:.1f} ({rating_count:,} ratings)")
                print(f"   {short_desc}")
            
            print("\nEnter a number to select an extension, or 'c' to cancel.")
            while True:
                try:
                    try:
                        choice = input(f"\nPlease choose an extension (1-{len(top_extensions)}) or 'c' to cancel [1]: ").lower()
                        if choice == 'c':
                            raise KeyboardInterrupt("User cancelled extension selection")
                        if not choice:  # Default to first option
                            choice = "1"
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(top_extensions):
                            return top_extensions[choice_idx]  # Return (score, extension) tuple
                        print(f"Please enter a number between 1 and {len(top_extensions)} or 'c' to cancel")
                    except EOFError:
                        # Handle case where stdin is not available (e.g. in CI/CD or automated testing)
                        self.logger.info("Non-interactive environment detected, defaulting to first option")
                        return top_extensions[0]  # Default to first option
                except ValueError:
                    print("Please enter a valid number or 'c' to cancel")
        else:
            return top_extensions[0]  # Return (score, extension) tuple

    def extract_extension_info(self, extension_name: str) -> Dict[str, Any]:
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
        score, extension = self._extract_from_search(extension_name)
        
        statistics = {stat["statisticName"]: stat["value"] 
                     for stat in extension.get("statistics", [])}
        
        # Format install count with commas
        install_count = int(statistics.get("install", 0))
        formatted_install_count = "{:,}".format(install_count)
        
        # Format rating
        weighted_rating = float(statistics.get("weightedRating", 0))
        rating = round(weighted_rating / 5, 2) if weighted_rating else 0
        rating_count = int(statistics.get("ratingCount", 0))
        
        extension_info = {
            "publisher_name": extension["publisher"]["publisherName"],
            "extension_id": extension["extensionName"],
            "version": extension.get("versions", [{}])[0].get("version", "Unknown") if extension.get("versions") else "Unknown",
            "display_name": extension.get("displayName", extension["extensionName"]),
            "short_description": extension.get("shortDescription", ""),
            "install_count": formatted_install_count,
            "rating": rating,
            "rating_count": rating_count,
            "relevance_score": score
        }
        
        return extension_info
    
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
            ValueError: If extension cannot be found or input is invalid
            requests.RequestException: If download fails
            OSError: If output directory cannot be created/accessed
            KeyboardInterrupt: If user cancels the download
        """
        # Validate inputs
        if not extension_name:
            raise ValueError("Extension name cannot be empty")
        
        # Validate and sanitize extension name for security
        import re
        if not re.match(r'^[a-zA-Z0-9.\-_\s]+$', extension_name):
            raise ValueError("Extension name contains invalid characters")
        
        # Validate output directory
        if not output_dir:
            raise ValueError("Output directory cannot be empty")
        
        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create output directory: {e}")
            
        # Check write permissions
        if not os.access(output_dir, os.W_OK):
            raise PermissionError(f"No write permission for directory: {output_dir}")
        
        # Get extension info
        extension_info = self.extract_extension_info(extension_name)
        
        # Display extension information and ask for confirmation
        print(f"\nExtension Details:")
        print(f"  Name: {extension_info['display_name']}")
        print(f"  Publisher: {extension_info['publisher_name']}")
        print(f"  Version: {extension_info['version']}")
        print(f"  Downloads: {extension_info['install_count']}")
        print(f"  Rating: {extension_info['rating']} ({extension_info['rating_count']} ratings)")
        print(f"  Relevance Score: {extension_info['relevance_score']:.1f}/100")
        
        print("\nDo you want to download this extension? [Y/n]: ", end='')
        try:
            choice = input().lower()
            if choice in ['n', 'no']:
                self.logger.info("Download cancelled by user")
                raise KeyboardInterrupt("User cancelled download")
        except EOFError:
            # Handle case where we're in a non-interactive environment
            self.logger.info("Non-interactive environment detected, proceeding with download")
            print("Y (auto-selected in non-interactive mode)")  # Show what action was taken
            
        # Use the validated output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct download URL
        download_url = self.construct_download_url(
            extension_info["publisher_name"],
            extension_info["extension_id"],
            extension_info["version"]
        )
        
        # Download the file
        self.logger.info(f"Downloading from: {download_url}")
        try:
            response = self.session.get(download_url, stream=True, timeout=self.download_timeout)
            response.raise_for_status()
            
            # Construct filename from extension info
            filename = f"{extension_info['publisher_name']}.{extension_info['extension_id']}-{extension_info['version']}.vsix"
            output_path = os.path.join(output_dir, filename)
            
            # Save the file with progress bar
            file_size = int(response.headers.get('Content-Length', 0))
            chunk_size = 1024  # 1 KB
            
            try:
                with open(output_path, 'wb') as f, tqdm(
                    desc=f"Downloading {filename}",
                    total=file_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for data in response.iter_content(chunk_size=chunk_size):
                        size = f.write(data)
                        pbar.update(size)
                        
                # Verify file was downloaded correctly
                if os.path.getsize(output_path) == 0:
                    raise ValueError(f"Downloaded file is empty: {output_path}")
                    
            except (IOError, OSError) as e:
                # Clean up partial downloads on error
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except:
                        pass
                raise OSError(f"Failed to write file {output_path}: {e}")
                
        except requests.exceptions.Timeout:
            raise ValueError(f"Download timed out for extension: {extension_info['display_name']}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Network error during download: {e}")
        
        self.logger.info(f"Downloaded to: {output_path}")
        return output_path

    def __del__(self):
        """Clean up resources when the object is garbage collected."""
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except:
                pass

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
                extension_name = input("\nEnter the name of the VS Code extension to download (or 'c' to cancel): ").strip().lower()
                if extension_name == 'c':
                    print("Operation cancelled.")
                    return
                if extension_name:
                    break
                print("Please enter a valid extension name.")
        
        # Create downloader instance
        downloader = VSIXDownloader(logger)
        
        try:
            # Download the extension
            output_file = downloader.download_extension(extension_name, args.output_dir)
            print(f"\nExtension downloaded successfully to: {output_file}")
        except KeyboardInterrupt as e:
            if str(e) == "User cancelled extension selection":
                print("\nOperation cancelled.")
                return
            if str(e) == "User cancelled download":
                print("\nDownload cancelled.")
                return
            raise
        except ValueError as e:
            print(f"\nError: {e}")
            return 1
        except requests.RequestException as e:
            print(f"\nNetwork error: {e}")
            return 1
        except OSError as e:
            print(f"\nFile system error: {e}")
            return 1
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    main()
