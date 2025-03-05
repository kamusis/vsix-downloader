#!/usr/bin/env python3
"""
Test script for the extension search functionality of VSIXDownloader.
"""

import sys
import os
from typing import Dict, Any
import requests
from requests.exceptions import RequestException

from vsix_downloader import VSIXDownloader
from log_utils import ConsoleLogger

def validate_extension_name(name: str) -> str:
    """
    Validate the extension name.
    
    Args:
        name: The extension name to validate
        
    Returns:
        The validated extension name
        
    Raises:
        ValueError: If name is empty or contains invalid characters
    """
    if not name:
        raise ValueError("Extension name cannot be empty")
    
    # Basic validation - allow alphanumeric, dot, hyphen, underscore
    import re
    if not re.match(r'^[a-zA-Z0-9.\-_]+$', name):
        raise ValueError("Extension name contains invalid characters")
    
    return name

def main() -> int:
    """
    Main function to test the extension search functionality.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger = ConsoleLogger()
    downloader = None
    
    try:
        # Get extension name from command line argument or use default
        extension_name = 'gitlens'
        if len(sys.argv) > 1:
            extension_name = validate_extension_name(sys.argv[1])
        
        # Create a subclass for testing that overrides the interactive method
        class TestVSIXDownloader(VSIXDownloader):
            def _extract_from_search(self, extension_name):
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
                
                response = self.session.post(url, json=data, timeout=30)
                response.raise_for_status()
                
                results = response.json()
                if not results.get("results") or not results["results"][0].get("extensions"):
                    raise ValueError(f"No extensions found matching: {extension_name}")
                
                extensions = results["results"][0]["extensions"]
                
                # Just return the first extension with a score of 100
                return 100.0, extensions[0]
        
        # Use our test subclass instead
        downloader = TestVSIXDownloader(logger)
        
        # Search for extension information
        extension_info = downloader.extract_extension_info(extension_name)
        
        # Display results
        print(f'\nExtension info:')
        print(f'Display Name: {extension_info["display_name"]}')
        print(f'Publisher: {extension_info["publisher_name"]}')
        print(f'Extension ID: {extension_info["extension_id"]}')
        print(f'Version: {extension_info["version"]}')
        print(f'Installs: {extension_info["install_count"]}')
        print(f'Rating: {extension_info["rating"]} ({extension_info["rating_count"]} ratings)')
        print(f'Relevance Score: {extension_info["relevance_score"]:.1f}/100')
        
        return 0
        
    except ValueError as e:
        print(f'Validation Error: {e}')
        return 1
    except RequestException as e:
        print(f'Network Error: {e}')
        return 2
    except KeyError as e:
        print(f'Data Error: Missing field {e} in response')
        return 3
    except Exception as e:
        print(f'Unexpected Error: {e}')
        return 4
    finally:
        # Clean up resources
        if downloader and hasattr(downloader, 'session'):
            downloader.session.close()

if __name__ == '__main__':
    sys.exit(main())
