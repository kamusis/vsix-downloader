#!/usr/bin/env python3

from vsix_downloader import VSIXDownloader
import os

def main():
    # Create a downloads directory if it doesn't exist
    download_dir = 'downloads'
    
    downloader = VSIXDownloader()
    try:
        output_file = downloader.download_extension('gitlens', download_dir)
        print(f'\nDownload completed successfully!')
        print(f'File saved to: {output_file}')
        print(f'File size: {os.path.getsize(output_file)/1024/1024:.1f}MB')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
