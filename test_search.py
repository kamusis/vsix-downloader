#!/usr/bin/env python3

from vsix_downloader import VSIXDownloader

def main():
    downloader = VSIXDownloader()
    try:
        publisher, extension_id, version = downloader.extract_extension_info('gitlens')
        print(f'\nExtension info:')
        print(f'Publisher: {publisher}')
        print(f'Extension ID: {extension_id}')
        print(f'Version: {version}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
