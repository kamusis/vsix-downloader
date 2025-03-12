#!/usr/bin/env python3
"""
Test script for the extension download functionality of VSIXDownloader.
"""

import sys
import os
import requests
from requests.exceptions import RequestException, Timeout

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

def validate_directory(directory: str) -> str:
    """
    Validate and prepare the download directory.
    
    Args:
        directory: Directory path to validate
        
    Returns:
        The validated directory path
        
    Raises:
        ValueError: If directory is invalid
        PermissionError: If directory can't be created or written to
    """
    if not directory:
        raise ValueError("Directory path cannot be empty")
    
    # Create the directory if it doesn't exist
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as e:
        raise PermissionError(f"Cannot create directory: {e}")
    
    # Check if we have write permissions
    if not os.access(directory, os.W_OK):
        raise PermissionError(f"No write permission for directory: {directory}")
    
    return directory

def main() -> int:
    """
    Main function to test the extension download functionality.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger = ConsoleLogger()
    downloader = None
    output_file = None
    
    # Default settings
    download_dir = 'downloads'
    extension_name = 'gitlens'
    
    try:
        # Get extension name from command line argument if provided
        if len(sys.argv) > 1:
            extension_name = validate_extension_name(sys.argv[1])
        
        # Get download directory from command line if provided
        if len(sys.argv) > 2:
            download_dir = sys.argv[2]
        
        # Validate and prepare download directory
        download_dir = validate_directory(download_dir)
        
        # Create a subclass for testing that overrides the interactive methods
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
                
            def download_extension(self, extension_name, output_dir='.'):
                # Get extension info without prompting
                extension_info = self.extract_extension_info(extension_name)
                
                # Create output directory if it doesn't exist
                os.makedirs(output_dir, exist_ok=True)
                
                # Skip the confirmation prompt
                download_url = self.construct_download_url(
                    str(extension_info["publisher_name"]),
                    str(extension_info["extension_id"]),
                    str(extension_info["version"])
                )
                
                # Continue with download logic
                self.logger.info(f"Downloading from: {download_url}")
                response = self.session.get(download_url, stream=True, timeout=60)
                response.raise_for_status()
                
                # Construct filename from extension info
                filename = f"{extension_info['publisher_name']}.{extension_info['extension_id']}-{extension_info['version']}.vsix"
                output_path = os.path.join(output_dir, filename)
                
                # Save file with progress but silently
                file_size = int(response.headers.get('Content-Length', 0))
                chunk_size = 1024  # 1 KB
                
                with open(output_path, 'wb') as f:
                    for data in response.iter_content(chunk_size=chunk_size):
                        size = f.write(data)
                
                self.logger.info(f"Downloaded to: {output_path}")
                return output_path
        
        # Use our test subclass instead
        downloader = TestVSIXDownloader(logger)
        
        # Download the extension
        print(f"Downloading extension: {extension_name}")
        print(f"Download directory: {os.path.abspath(download_dir)}")
        
        output_file = downloader.download_extension(extension_name, download_dir)
        
        # Verify the downloaded file
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"Download failed: Output file not found: {output_file}")
        
        file_size = os.path.getsize(output_file)
        if file_size == 0:
            raise ValueError(f"Download failed: File is empty: {output_file}")
        
        # Report success
        print(f'\nDownload completed successfully!')
        print(f'File saved to: {output_file}')
        print(f'File size: {file_size/1024/1024:.1f}MB')
        
        return 0
        
    except ValueError as e:
        print(f'Validation Error: {e}')
        return 1
    except PermissionError as e:
        print(f'Permission Error: {e}')
        return 2
    except RequestException as e:
        if isinstance(e, Timeout):
            print(f'Network Timeout: {e}')
        else:
            print(f'Network Error: {e}')
        return 3
    except FileNotFoundError as e:
        print(f'File Error: {e}')
        return 4
    except KeyboardInterrupt:
        print(f'\nDownload cancelled by user')
        return 5
    except Exception as e:
        print(f'Unexpected Error: {type(e).__name__}: {e}')
        return 6
    finally:
        # Clean up resources
        if downloader and hasattr(downloader, 'session'):
            downloader.session.close()

if __name__ == '__main__':
    sys.exit(main())
