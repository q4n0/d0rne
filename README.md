# d0rne: Your CLI Downloader

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

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/)
2. Open Command Prompt and run:
   ```
   pip install colorama requests libtorrent tqdm --break-system-packages
   ```
3. Download `d0rne.py` from the repository

### Linux (Ubuntu, Debian, etc.)

1. Open terminal and run:
   ```
   sudo apt update
   sudo apt install python3 python3-pip python3-libtorrent
   pip3 install requirements.txt --break-sytem-packages
   ```
2. Download `d0rne.py` from the repository

### Arch Linux and derivatives

1. Open terminal and run:
   ```
   sudo pacman -Syu python python-pip python-libtorrent
   pip install colorama requests tqdm libtorrent --break-system-packages
   ```
2. Download `d0rne.py` from the repository

### Fedora

1. Open terminal and run:
   ```
   sudo dnf update
   sudo dnf install python3 python3-pip python3-libtorrent
   pip3 install colorama requests tqdm libtorrent --break-system-packages
   ```
2. Download `d0rne.py` from the repository

### Termux (Android)

1. Open Termux and run:
   ```
   pkg update
   pkg install python libtorrent
   pip install colorama requests tqdm libtorrent
   ```
2. Download `d0rne.py` from the repository

## Usage

### Interactive Mode

Run d0rne in interactive mode:
```
python3 d0rne.py
```
Follow the on-screen menu to choose your download option.

### Command-line Usage

1. Download a file:
   ```
   python3 d0rne.py "https://example.com/file.zip" -o output.zip
   ```

2. Download a website:
   ```
   python3 d0rne.py "https://example.com" -w -d 2
   ```

3. Download from FTP:
   ```
   python3 d0rne.py "ftp://example.com/file.txt" --ftp-user username --ftp-pass password
   ```

4. Download a torrent:
   ```
   python3 d0rne.py "path/to/torrent/file.torrent" -t
   ```

5. Check website status:
   ```
   python3 d0rne.py "https://example.com" --check
   ```

6. Multiple downloads (interactive mode only):
   Choose option 7 from the main menu to queue and process multiple downloads.

### Options

- `-o, --output`: Specify output filename or directory
- `-r, --resume`: Resume partially downloaded files
- `-u, --user-agent`: Set user agent string
- `-w, --website`: Download entire website
- `-d, --depth`: Set depth for website download (default: 1)
- `-k, --convert-links`: Convert links for offline viewing
- `-p, --page-requisites`: Download all page requisites
- `-q, --quiet`: Quiet mode for downloads
- `-t, --torrent`: Download as torrent
- `--check`: Check website status
- `--proxy`: Set proxy server (e.g., http://proxy:port)
- `--limit-rate`: Limit download speed (e.g., 500k)

## Configuration

d0rne now supports configuration files for setting default options. The configuration file is located at `~/.config/d0rne/config` on Unix-like systems and `%USERPROFILE%\.config\d0rne\config` on Windows.

You can set default values for:
- Output directory
- User agent
- Proxy
- Download speed limit

To set or modify the configuration, use option 8 in the interactive mode.

## Logging

d0rne now includes enhanced logging capabilities. Logs are stored in `d0rne.log` in the same directory as the script.

## Troubleshooting

- If you encounter permission errors, try running the script with `sudo` (Linux/Termux) or as administrator (Windows).
- Ensure all dependencies are correctly installed.
- For Termux, you may need to grant storage permissions: `termux-setup-storage`
- Check the `d0rne.log` file for detailed error messages and debugging information.

## Credits

Created by b0urn3
- GitHub: [github.com/q4no](https://github.com/q4no)
- Instagram: [onlybyhive](https://www.instagram.com/onlybyhive)
