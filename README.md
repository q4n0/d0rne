# d0rne: Your CLI Downloader

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⢀⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣰⣿⣿⣿⣿⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⡿⠿⢿⣿⣿⣶⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢼⡟⠉⣻⣿⣿⡏⠰⣷⠀⢹⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢻⣷⡀⠙⣻⣿⣿⣄⣠⣴⡿⠋⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣭⣉⣛⣻⣿⣿⣿⣿⣿⣿⣿⣶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢠⠞⢡⣽⣿⣿⠿⢻⣿⣿⣿⣏⣿⣿⣿⣧⣤⣤⣤⣄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠘⣴⡨⠛⠋⠁⠀⣼⣿⣿⣿⡟⣿⣿⣿⣿⣯⢈⣿⣿⠂⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠘⠃⠀⠀⠀⢀⣤⣿⣷⡜⣿⣧⡉⠉⠙⠋⠁⠈⠉⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠁⢠⣾⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

        d0rne: Your cli Downloader Made by b0urn3 
  GITHUB: https://github.com/q4no | Instagram: onlybyhive 
              | TOOL VERSION: 1.0.2 |
            ----------------------------



d0rne is a versatile command-line downloader tool created by b0urn3. It supports various download types including single files, websites, FTP, torrents, and features multiple concurrent downloads.

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

### Linux

1. Install Python and pip if not already installed:
   ```
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. Install libtorrent:
   ```
   sudo apt install python3-libtorrent
   ```

3. Clone the repository or download `d0rne.py`

https://github.com/q4n0/d0rne/blob/main/d0rne.py

5. Install required packages:
   ```
   pip3 install colorama requests tqdm appdirs packaging aiohttp aiofiles aiohttp_socks yarl
   ```

### macOS

1. Install Homebrew if not already installed:
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python:
   ```
   brew install python
   ```

3. Install libtorrent:
   ```
   brew install libtorrent-rasterbar
   ```

4. Clone the repository or download `d0rne.py`
   
https://github.com/q4n0/d0rne/blob/main/d0rne.py

6. Install required packages:
   ```
   pip3 install colorama requests tqdm appdirs packaging aiohttp aiofiles aiohttp_socks yarl
   ```

### Windows

1. Download and install Python from [python.org](https://www.python.org/downloads/)

2. During installation, make sure to check "Add Python to PATH"

3. Open Command Prompt as Administrator

4. Install required packages:
   ```
   pip install colorama requests tqdm appdirs packaging aiohttp aiofiles aiohttp_socks yarl python-libtorrent
   ```

5. Clone the repository or download `d0rne.py`
   https://github.com/q4n0/d0rne/blob/main/d0rne.py

## Usage

### Interactive Mode

Run d0rne in interactive mode:

```
python3 d0rne.py
```

Note: On Windows, you might need to use `python` instead of `python3`.

For Linux users, it's recommended to run with sudo or in a virtual environment:

```
sudo python3 d0rne.py
```

Follow the on-screen menu to choose your download option.

### Command-line Usage

- Download a file:
  ```
  python3 d0rne.py "https://example.com/file.zip" -o output.zip
  ```

- Download a website:
  ```
  python3 d0rne.py "https://example.com" -w -d 2
  ```

- Download from FTP:
  ```
  python3 d0rne.py "ftp://example.com/file.txt" --ftp-user username --ftp-pass password
  ```

- Download a torrent:
  ```
  python3 d0rne.py "path/to/torrent/file.torrent" -t
  ```

- Check website status:
  ```
  python3 d0rne.py "https://example.com" --check
  ```

- Update d0rne:
  ```
  python3 d0rne.py --update
  ```

## Options

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
- `--update`: Update d0rne to the latest version
- `--no-color`: Disable colored output

# d0rne: Your CLI Downloader

## Configuration

d0rne supports configuration files for setting default options. The configuration file locations are:

- Unix-like systems (Linux, macOS): `~/.config/d0rne/config.ini`
- Windows: `%LOCALAPPDATA%\d0rne\config.ini`

### Default Configuration

d0rne comes with the following default configuration:

```ini
[DEFAULT]
output_dir = ~/Downloads
user_agent = d0rne/1.0
proxy = 
limit_rate = 
```

You can modify these defaults by editing the config file or by using command-line arguments, which will override the config file settings for that particular run.

### Customizing Configuration

To customize your configuration:

1. Create the configuration file if it doesn't exist.
2. Open the file in a text editor.
3. Modify the values as needed. For example:

```ini
[DEFAULT]
output_dir = /path/to/your/preferred/download/directory
user_agent = YourCustomUserAgent/2.0
proxy = http://your-proxy-server:port
limit_rate = 500k
```

### Configuration Options

- `output_dir`: The default directory where downloads are saved.
- `user_agent`: The default user agent string used for downloads.
- `proxy`: The default proxy server to use (if any).
- `limit_rate`: The default download speed limit.

These settings can be overridden by command-line arguments when running d0rne.


## Logging

d0rne includes enhanced logging capabilities. Logs are stored in `d0rne.log` in the same directory as the script.

## Troubleshooting

- If you encounter permission errors on Linux or macOS, try running the script with `sudo`.
- On Windows, run Command Prompt as Administrator if you encounter permission issues.
- Ensure all dependencies are correctly installed.
- Check the `d0rne.log` file for detailed error messages and debugging information.

## Credits

Created by b0urn3
- GitHub: [github.com/q4no](https://github.com/q4no)
- Instagram: onlybyhive
