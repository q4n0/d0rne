## d0rne: Your CLI Downloader

d0rne is a versatile command-line downloader tool created by b0urn3. It supports various download types including single files, websites, FTP, torrents, and now features multiple concurrent downloads.

## Features

- Download single or multiple files
- Quiet download mode for sensitive sites
- Website mirroring
- FTP downloads
- Torrent downloads
- Website status checking
- Multiple concurrent downloads
- Proxy support
- Download throttling
- Enhanced error handling and logging
- Configuration files for default settings
- Improved interactive progress display
- Self-update functionality
- Animated exit on interruption

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)
- python3-libtorrent

### Installation Steps

1. Clone the repository or download `d0rne.py`
2. Install the required packages:
3. For linux  also use
   sudo apt install python3-libtorrent

```bash
pip install colorama requests tqdm python-libtorrent appdirs packaging
Note: On some systems, you might need to use pip3 instead of pip.

## Usage

Interactive Mode
Run d0rne in interactive mode:
python3 d0rne.py

## linux users are recommended to run with sudo or virtual env

Follow the on-screen menu to choose your download option.
## Command-line Usage

Download a file:
python3 d0rne.py "https://example.com/file.zip" -o output.zip

Download a website:
python3 d0rne.py "https://example.com" -w -d 2

Download from FTP:
python3 d0rne.py "ftp://example.com/file.txt" --ftp-user username --ftp-pass password

Download a torrent:
python3 d0rne.py "path/to/torrent/file.torrent" -t

Check website status:
python3 d0rne.py "https://example.com" --check

Update d0rne:
python3 d0rne.py --update


## Options

-o, --output: Specify output filename or directory
-r, --resume: Resume partially downloaded files
-u, --user-agent: Set user agent string
-w, --website: Download entire website
-d, --depth: Set depth for website download (default: 1)
-k, --convert-links: Convert links for offline viewing
-p, --page-requisites: Download all page requisites
-q, --quiet: Quiet mode for downloads
-t, --torrent: Download as torrent
--check: Check website status
--proxy: Set proxy server (e.g., http://proxy:port)
--limit-rate: Limit download speed (e.g., 500k)
--update: Update d0rne to the latest version
--no-color: Disable colored output

## Configuration
d0rne supports configuration files for setting default options. The configuration file is located at ~/.config/d0rne/config on Unix-like systems and %LOCALAPPDATA%\d0rne\config on Windows.
You can set default values for:

Output directory
User agent
Proxy
Download speed limit

## Logging
d0rne includes enhanced logging capabilities. Logs are stored in d0rne.log in the same directory as the script.
Troubleshooting

If you encounter permission errors, try running the script with sudo (Linux) or as administrator (Windows).
Ensure all dependencies are correctly installed.
Check the d0rne.log file for detailed error messages and debugging information.

## Credits
Created by b0urn3

GitHub: github.com/q4no
Instagram: onlybyhive
