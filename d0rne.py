#!/usr/bin/env python3
import argparse
import os
import sys
import time
import re
import signal
import logging
import asyncio
import aiohttp
import aiofiles
from aiohttp import ClientTimeout, TCPConnector
from aiohttp_socks import ProxyConnector
from yarl import URL
from colorama import init, Fore, Style
import libtorrent as lt
from tqdm import tqdm
import appdirs
from packaging import version
import configparser
import importlib.util
import subprocess
import threading
import itertools
from ftplib import FTP
from typing import Optional, List, Tuple, Any
import platform
from pathlib import Path

# Constants
CURRENT_VERSION = "1.0.3"
GITHUB_REPO = "q4no/d0rne"

# Initialize colorama
init(autoreset=True)

# Set up logging
logging.basicConfig(
    filename='d0rne.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
D0RNE_BANNER = f"""{Fore.CYAN}
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
{Fore.YELLOW}
        d0rne: Your cli Downloader Made by b0urn3 
  GITHUB: https://github.com/q4no | Instagram: onlybyhive 
              | TOOL VERSION: 1.0.3 |
            ----------------------------
"""

WEBSITE_UP_ASCII = f"{Fore.GREEN}[ONLINE] Website is UP and running!"
WEBSITE_DOWN_ASCII = f"{Fore.RED}[OFFLINE] Website is DOWN!"
DOWNLOAD_ASCII = f"{Fore.BLUE}[DOWNLOAD] Starting download..."
FTP_ASCII = f"{Fore.MAGENTA}[FTP] Connecting to FTP server..."

# Classes
class ConnectionPool:
    def __init__(self, limit=100, force_close=False, enable_cleanup_closed=True):
        self.connector = TCPConnector(
            limit=limit,
            force_close=force_close,
            enable_cleanup_closed=enable_cleanup_closed
        )
        self.session = None     

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=ClientTimeout(total=3600),
                headers={"User-Agent": "d0rne/1.0"}
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
        await self.connector.close()

class PluginManager:
    def __init__(self):
        self.plugins = {}

    def load_plugin(self, plugin_name):
        plugin_path = f"plugins/{plugin_name}.py"
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.plugins[plugin_name] = module

    def get_plugin(self, plugin_name):
        return self.plugins.get(plugin_name)

plugin_manager = PluginManager()

class Loader:
    def __init__(self, desc="Loading...", end="Done!", timeout=0.1):
        self.desc = desc
        self.end = end
        self.timeout = timeout
        self._thread = None
        self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.done = False

    def start(self):
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def _animate(self):
        for c in itertools.cycle(self.steps):
            if self.done:
                break
            print(f"\r{self.desc} {c}", flush=True, end="")
            time.sleep(self.timeout)

    def stop(self):
        self.done = True
        if self._thread is not None:
            self._thread.join()
        print(f"\r{self.end}", flush=True)

connection_pool = ConnectionPool()

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, size):
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.updated_at
            self.tokens = min(self.rate_limit, self.tokens + time_passed * self.rate_limit)
            self.updated_at = now

            if size > self.tokens:
                await asyncio.sleep((size - self.tokens) / self.rate_limit)
                self.tokens = 0
            else:
                self.tokens -= size

def get_downloads_folder():
    """
    Get the default downloads folder based on the operating system.
    """
    system = platform.system()
    if system == "Windows":
        return str(Path.home() / "Downloads")
    elif system == "Darwin":  # macOS
        return str(Path.home() / "Downloads")
    elif system == "Linux":
        return str(Path.home() / "Downloads")
    else:
        return str(Path.home())  # Fallback to home directory

def ensure_dir(file_path):
    """
    Ensure that the directory for the given file path exists.
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

async def download_torrent(torrent_path: str, save_path: str = '.') -> None:
    ses = lt.session()
    params = {
        'save_path': save_path,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse,
    }
    
    print(f"{Fore.YELLOW}Loading torrent...")
    try:
        if torrent_path.startswith('magnet:'):
            atp = lt.parse_magnet_uri(torrent_path)
            atp.save_path = save_path
            handle = ses.add_torrent(atp)
            print(f"{Fore.YELLOW}Downloading metadata...")
            while not handle.status().has_metadata:
                await asyncio.sleep(1)
            print(f"{Fore.GREEN}Got metadata, starting torrent download...")
        else:
            info = lt.torrent_info(torrent_path)
            handle = ses.add_torrent({'ti': info, 'save_path': save_path})
            print(f"{Fore.GREEN}Torrent loaded, starting download...")

        print(f"{Fore.CYAN}Starting download...")
        with tqdm(total=100, unit='%') as pbar:
            while not handle.status().is_seeding:
                s = handle.status()
                
                state_str = ['queued', 'checking', 'downloading metadata', 
                             'downloading', 'finished', 'seeding', 'allocating']
                try:
                    state = state_str[s.state]
                except IndexError:
                    state = 'unknown'
                
                pbar.update(int(s.progress * 100) - pbar.n)
                pbar.set_postfix({
                    'state': state,
                    'down_speed': f"{s.download_rate / 1000:.1f} kB/s",
                    'up_speed': f"{s.upload_rate / 1000:.1f} kB/s",
                    'peers': s.num_peers
                })
                
                await asyncio.sleep(1)

        print(f"\n{Fore.GREEN}Download complete!")
    except Exception as e:
        print(f"{Fore.RED}Error downloading torrent: {e}")
    finally:
        print(f"{Fore.YELLOW}Cleaning up...")
        ses.remove_torrent(handle)

async def async_download_file(url, output=None, quiet_mode=False, resume=False, rate_limit=None):
    """
    Asynchronously download a file with a loading animation and progress bar.
    """
    loader = Loader("Initializing download...", "Download initialized!", 0.1)
    loader.start()
    try:
        session = await connection_pool.get_session()
        headers = {}
        file_size = 0
        start_pos = 0

        if output is None:
            # Extract filename from URL or use a default name
            output = os.path.join(get_downloads_folder(), os.path.basename(url) or "download")
        
        ensure_dir(output)

        if resume and os.path.exists(output):
            start_pos = os.path.getsize(output)
            headers['Range'] = f'bytes={start_pos}-'

        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            file_size = int(response.headers.get('content-length', 0))

            mode = 'ab' if resume and response.status == 206 else 'wb'
            start_pos = start_pos if mode == 'ab' else 0

            limiter = RateLimiter(rate_limit) if rate_limit else None

            loader.stop()  # Stop the loader before starting the progress bar

            with tqdm(total=file_size, initial=start_pos, unit='iB', unit_scale=True, disable=quiet_mode) as progress_bar:
                async with aiofiles.open(output, mode) as f:
                    chunk_size = 8192
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if limiter:
                            await limiter.acquire(len(chunk))
                        await f.write(chunk)
                        progress_bar.update(len(chunk))

        print(f"\n{Fore.GREEN}Download completed successfully. File saved to: {output}")
        return True
    except aiohttp.ClientError as e:
        print(f"{Fore.RED}Network error: {e}")
        logging.error(f"Network error while downloading {url}: {e}")
    except asyncio.TimeoutError:
        print(f"{Fore.RED}Download timed out.")
        logging.error(f"Timeout while downloading {url}")
    except IOError as e:
        print(f"{Fore.RED}File I/O error: {e}")
        logging.error(f"File I/O error while downloading {url}: {e}")
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}")
        logging.error(f"Unexpected error while downloading {url}: {e}")
    finally:
        loader.stop()  # Ensure the loader is stopped in case of any exceptions
    return False
  
async def download_website(url, depth, convert_links, page_requisites):
    loader = Loader("Preparing to download website...", "Website download prepared!", 0.1)
    loader.start()
    try:
        command = ["wget", "--recursive", f"--level={depth}", "--no-clobber", "--page-requisites", 
                   "--html-extension", "--convert-links", "--restrict-file-names=windows", "--no-parent", url]
        if convert_links:
            command.append("--convert-links")
        if page_requisites:
            command.append("--page-requisites")
        
        loader.stop()  # Stop the loader before starting the download
        
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print(f"{Fore.GREEN}Website downloaded successfully.")
        else:
            print(f"{Fore.RED}Error downloading website: {stderr.decode()}")
    finally:
        loader.stop()

async def download_ftp(url, username, password):
    loader = Loader("Connecting to FTP server...", "FTP connection established!", 0.1)
    loader.start()
    try:
        def ftp_download():
            with FTP(url) as ftp:
                ftp.login(user=username, passwd=password)
                files = ftp.nlst()
                
                loader.stop()  # Stop the loader before starting the download
                
                for file in files:
                    print(f"Downloading {file}...")
                    local_path = os.path.join(get_downloads_folder(), file)
                    ensure_dir(local_path)
                    with open(local_path, 'wb') as local_file:
                        ftp.retrbinary(f'RETR {file}', local_file.write)
            
            print(f"{Fore.GREEN}FTP download completed successfully.")

        await asyncio.to_thread(ftp_download)
    except Exception as e:
        print(f"{Fore.RED}Error during FTP download: {e}")
    finally:
        loader.stop()

async def check_website_status(url: str) -> None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    print(WEBSITE_UP_ASCII)
                else:
                    print(WEBSITE_DOWN_ASCII)
    except aiohttp.ClientError:
        print(WEBSITE_DOWN_ASCII)


def parse_rate_limit(limit):
    if not limit:
        return None
    
    units = {'k': 1024, 'm': 1024*1024}
    number = float(limit[:-1])
    unit = limit[-1].lower()
    
    return int(number * units[unit]) if unit in units else int(number)
        
def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(appdirs.user_config_dir("d0rne"), "config.ini")
    
    if os.path.exists(config_path):
        config.read(config_path)
    return config

def save_config(config):
    config_dir = appdirs.user_config_dir("d0rne")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.ini")
    with open(config_path, 'w') as configfile:
        config.write(configfile)
        
def manage_config():
    config = load_config()
    print(f"{Fore.CYAN}Current Configuration:")
    for key, value in config['DEFAULT'].items():
        print(f"{key}: {value}")
    
    print(f"\n{Fore.YELLOW}Enter new values (or press Enter to keep current value)")
    
    config['DEFAULT'] = {
        'output_dir': input(f"Output directory [{config.get('DEFAULT', 'output_dir', fallback='')}]: ").strip() or config.get('DEFAULT', 'output_dir', fallback=''),
        'user_agent': input(f"User agent [{config.get('DEFAULT', 'user_agent', fallback='')}]: ").strip() or config.get('DEFAULT', 'user_agent', fallback=''),
        'proxy': input(f"Proxy [{config.get('DEFAULT', 'proxy', fallback='')}]: ").strip() or config.get('DEFAULT', 'proxy', fallback=''),
        'limit_rate': input(f"Limit rate [{config.get('DEFAULT', 'limit_rate', fallback='')}]: ").strip() or config.get('DEFAULT', 'limit_rate', fallback='')
    }

    save_config(config)
    print(f"{Fore.GREEN}Configuration saved successfully.")

def print_banner():
    print(D0RNE_BANNER)

def create_progress_bar(percentage, width=50):
    filled_width = int(width * percentage // 100)
    return f"[{'█' * filled_width}{'-' * (width - filled_width)}] {percentage:.1f}%"

def parse_wget_output(line):
    progress_regex = r'(\d+)%\s+[\w.]+\s+([\d.]+\w)\s+([\d.]+\s*\w)/s(?:\s+eta\s+([\w\s]+))?'
    match = re.search(progress_regex, line)
    if match:
        return float(match.group(1)), match.group(2), match.group(3), match.group(4) or "Unknown"
    return None

def get_user_input(prompt, default=None):
    user_input = input(f"{Fore.YELLOW}{prompt}{Fore.RESET}")
    return user_input or default

def animated_exit():
    frames = ["Exiting d0rne |", "Exiting d0rne /", "Exiting d0rne -", "Exiting d0rne \\"]
    for _ in range(10):  
        for frame in frames:
            sys.stdout.write(f'\r{Fore.YELLOW}{frame}{Style.RESET_ALL}')
            sys.stdout.flush()
            time.sleep(0.1)
    
    sys.stdout.write('\r' + ' ' * 20 + '\r')  # Clear the line
    print(f"{Fore.GREEN}Thanks for using d0rne! Goodbye!{Style.RESET_ALL}")

def ctrl_c_handler(signum, frame):
    print()  
    animated_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, ctrl_c_handler)

class Loader:
    def __init__(self, desc="Loading...", end="Done!", timeout=0.1):
        self.desc = desc
        self.end = end
        self.timeout = timeout
        self._thread = None
        self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.done = False

    def start(self):
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def _animate(self):
        for c in itertools.cycle(self.steps):
            if self.done:
                break
            print(f"\r{self.desc} {c}", flush=True, end="")
            time.sleep(self.timeout)

    def stop(self):
        self.done = True
        if self._thread is not None:
            self._thread.join()
        print(f"\r{self.end}", flush=True)

async def download_file(url, output, quiet_mode=False):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                with open(output, 'wb') as f, tqdm(
                    desc=output,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                    disable=quiet_mode
                ) as progress_bar:
                    chunk_size = 8192
                    async for chunk in response.content.iter_chunked(chunk_size):
                        size = f.write(chunk)
                        progress_bar.update(size)
        return True
    except aiohttp.ClientError as e:
        print(f"{Fore.RED}Error downloading file: {e}")
        return False

async def download_with_retry(url, output=None, resume=False, user_agent=None, retry_attempts=3, retry_delay=5, quiet_mode=False, proxy=None, limit_rate=None):
    print(DOWNLOAD_ASCII)
    command = ["wget", "--progress=bar:force"]
    
    if output:
        command.extend(["-O", output])
    if resume:
        command.append("-c")
    if user_agent:
        command.extend(["--user-agent", user_agent])
    if quiet_mode:
        command.append("--quiet")
    if proxy:
        command.extend(["--proxy", proxy])
    if limit_rate:
        command.extend(["--limit-rate", limit_rate])
    
    command.append(url)

    for attempt in range(retry_attempts):
        print(f"{Fore.YELLOW}Download attempt {attempt + 1} of {retry_attempts}")
        if await run_wget(command, show_progress=True, quiet_mode=quiet_mode):
            logging.info(f"Download completed successfully: {url}")
            print(f"\n{Fore.GREEN}Download completed successfully.")
            return True
        if attempt < retry_attempts - 1:
            logging.warning(f"Download failed. Retrying in {retry_delay} seconds...")
            print(f"\n{Fore.RED}Download failed. Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
    
    logging.error(f"Max retry attempts reached. Download failed: {url}")
    print(f"\n{Fore.RED}Max retry attempts reached. Download failed.")
    return False

def print_menu():
    menu = f"""
{Fore.CYAN}╔════════════════════════════════════════╗
{Fore.CYAN}║       d0rne-Downloader Menu            ║{Fore.CYAN} 
{Fore.CYAN}╠════════════════════════════════════════╝
{Fore.CYAN}║ {Fore.GREEN}1. Download file(s){Fore.CYAN}                    ║
{Fore.CYAN}║ {Fore.GREEN}2. Q-download best for sensitive sites{Fore.CYAN} ║
{Fore.CYAN}║ {Fore.GREEN}3. Download a website{Fore.CYAN}                  ║
{Fore.CYAN}║ {Fore.GREEN}4. Download from FTP{Fore.CYAN}                   ║
{Fore.CYAN}║ {Fore.GREEN}5. Download torrent{Fore.CYAN}                    ║
{Fore.CYAN}║ {Fore.GREEN}6. Check web status-Is website online?{Fore.CYAN} ║
{Fore.CYAN}║ {Fore.GREEN}7. Multiple downloads{Fore.CYAN}                  ║
{Fore.CYAN}║ {Fore.GREEN}8. Manage Configuration{Fore.CYAN}                ║
{Fore.CYAN}║To quit:Use "CTRL+C" to EXIT tool{Fore.CYAN}       ║
{Fore.CYAN}╚════════════════════════════════════════╝
"""
    print(menu)

async def multiple_downloads():
    download_queue = []
    while True:
        print(f"\n{Fore.CYAN}Current download queue: {len(download_queue)} item(s)")
        choice = get_user_input("Add a download (y/n) or start processing queue (s): ").lower()
        
        if choice == 'y':
            download_queue.append((
                get_user_input("Enter the URL to download: "),
                get_user_input("Enter output filename (leave blank for default): "),
                get_user_input("Resume partial download? (y/n): ").lower() == 'y',
                get_user_input("Enter user agent (leave blank for default): "),
                get_user_input("Enter proxy (e.g., http://proxy:port) or leave blank: "),
                get_user_input("Enter download speed limit (e.g., 500k) or leave blank: ")
            ))
            print(f"{Fore.GREEN}Download added to queue.")
        
        elif choice == 's':
            if not download_queue:
                print(f"{Fore.YELLOW}Queue is empty. Add some downloads first.")
            else:
                print(f"{Fore.GREEN}Processing download queue...")
                tasks = [asyncio.create_task(
                    async_download_file(
                        url, output, quiet_mode=False, 
                        resume=resume, rate_limit=parse_rate_limit(limit_rate)
                    )
                ) for url, output, resume, user_agent, proxy, limit_rate in download_queue]
                results = await asyncio.gather(*tasks)
                print(f"{Fore.GREEN}All downloads completed. {sum(results)}/{len(results)} successful.")
                download_queue.clear()
            break
        
        elif choice == 'n':
            if download_queue and get_user_input("Queue is not empty. Are you sure you want to exit? (y/n): ").lower() != 'y':
                continue
            break
        
        else:
            print(f"{Fore.RED}Invalid choice. Please enter 'y', 'n', or 's'.")

async def run_wget(command, show_progress=False, quiet_mode=False):
    if not quiet_mode:
        print(f"{Fore.GREEN}Starting download...")

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        logging.info(f"Download completed successfully: {command[-1]}")
        print(f"\n{Fore.GREEN}Download completed successfully.")
        return True
    
    logging.error(f"Command failed with return code {process.returncode}")
    print(f"\n{Fore.RED}Command failed with return code {process.returncode}")
    return False
    
async def download_torrent(torrent_path: str, save_path: str = None):
    if save_path is None:
        save_path = get_downloads_folder()
    
    loader = Loader("Initializing torrent download...", "Torrent download initialized!", 0.1)
    loader.start()
    
    ses = lt.session()
    params = {
        'save_path': save_path,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse,
    }
    
    try:
        if torrent_path.startswith('magnet:'):
            atp = lt.parse_magnet_uri(torrent_path)
            atp.save_path = save_path
            handle = ses.add_torrent(atp)
            loader.stop()
            print(f"{Fore.YELLOW}Downloading metadata...")
            while not handle.status().has_metadata:
                await asyncio.sleep(1)
            print(f"{Fore.GREEN}Got metadata, starting torrent download...")
        else:
            info = lt.torrent_info(torrent_path)
            handle = ses.add_torrent({'ti': info, 'save_path': save_path})
            loader.stop()
            print(f"{Fore.GREEN}Torrent loaded, starting download...")

        print(f"{Fore.CYAN}Starting download...")
        with tqdm(total=100, unit='%') as pbar:
            while not handle.status().is_seeding:
                s = handle.status()
                
                state_str = ['queued', 'checking', 'downloading metadata', 
                             'downloading', 'finished', 'seeding', 'allocating']
                try:
                    state = state_str[s.state]
                except IndexError:
                    state = 'unknown'
                
                pbar.update(int(s.progress * 100) - pbar.n)
                pbar.set_postfix({
                    'state': state,
                    'down_speed': f"{s.download_rate / 1000:.1f} kB/s",
                    'up_speed': f"{s.upload_rate / 1000:.1f} kB/s",
                    'peers': s.num_peers
                })
                
                await asyncio.sleep(1)

        print(f"\n{Fore.GREEN}Download complete!")
    except Exception as e:
        print(f"{Fore.RED}Error downloading torrent: {e}")
    finally:
        loader.stop()
        print(f"{Fore.YELLOW}Cleaning up...")
        ses.remove_torrent(handle)
        
async def interactive_mode():
    print_banner()
    config = load_config()
    while True:
        try:
            print_menu()
            choice = get_user_input("Enter your choice (1-8): ")
            
            if choice == '1':
                await download_with_retry(
                    get_user_input("Enter the URL to download: "),
                    get_user_input("Enter output filename (leave blank for default): "),
                    get_user_input("Resume partial download? (y/n): ").lower() == 'y',
                    get_user_input("Enter user agent (leave blank for default): "),
                    quiet_mode=False,
                    proxy=get_user_input("Enter proxy (e.g., http://proxy:port) or leave blank: "),
                    limit_rate=get_user_input("Enter download speed limit (e.g., 500k) or leave blank: ")
                )
            elif choice == '2':
                await download_with_retry(
                    get_user_input("Enter the URL to download: "),
                    get_user_input("Enter output filename (leave blank for default): "),
                    get_user_input("Resume partial download? (y/n): ").lower() == 'y',
                    get_user_input("Enter user agent (leave blank for default): "),
                    quiet_mode=True
                )
            elif choice == '3':
                await download_website(
                    get_user_input("Enter the website URL: "),
                    int(get_user_input("Enter depth (default 1): ", "1")),
                    get_user_input("Convert links for offline viewing? (y/n): ").lower() == 'y',
                    get_user_input("Download all page requisites? (y/n): ").lower() == 'y'
                )
            elif choice == '4':
                await download_ftp(
                    get_user_input("Enter the FTP URL: "),
                    get_user_input("Enter FTP username (leave blank for anonymous): "),
                    get_user_input("Enter FTP password (leave blank if not required): ")
                )
            elif choice == '5':
                await download_torrent(
                    get_user_input("Enter the torrent file path or magnet link: "),
                    get_user_input("Enter the save path (leave blank for current directory): ") or '.'
                )
            elif choice == '6':
                await check_website_status(get_user_input("Enter the website URL to check: "))
            elif choice == '7':
                await multiple_downloads()
            elif choice == '8':
                manage_config()
            else:
                print(f"{Fore.RED}Invalid choice. Please try again or use CTRL+C to exit.")
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}")
            logging.error(f"Error in interactive mode: {e}")

async def async_main():
    parser = argparse.ArgumentParser(description="d0rne: Your cli Downloader")
    parser.add_argument("url", nargs="?", help="URL or torrent file/magnet link to download")
    parser.add_argument("-o", "--output", help="Output filename or directory")
    parser.add_argument("-r", "--resume", action="store_true", help="Resume partially downloaded files")
    parser.add_argument("-u", "--user-agent", help="Set user agent string")
    parser.add_argument("-w", "--website", action="store_true", help="Download entire website")
    parser.add_argument("-d", "--depth", type=int, default=1, help="Depth for website download (default: 1)")
    parser.add_argument("-k", "--convert-links", action="store_true", help="Convert links for offline viewing")
    parser.add_argument("-p", "--page-requisites", action="store_true", help="Download all page requisites")
    parser.add_argument("--ftp-user", help="FTP username")
    parser.add_argument("--ftp-pass", help="FTP password")
    parser.add_argument("--check", action="store_true", help="Check website status")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode for downloads")
    parser.add_argument("-t", "--torrent", action="store_true", help="Download as torrent")
    parser.add_argument("--proxy", help="Set proxy server (e.g., http://proxy:port)")
    parser.add_argument("--limit-rate", help="Limit download speed (e.g., 500k)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--http2", action="store_true", help="Use HTTP/2 for downloads")
    parser.add_argument("--plugin", help="Use a specific plugin for download")

    args = parser.parse_args()

    if args.no_color:
        init(strip=True, convert=False)
    config = load_config()
    if config:
        args.output = args.output or config.get('DEFAULT', 'output_dir', fallback=None)
        args.user_agent = args.user_agent or config.get('DEFAULT', 'user_agent', fallback=None)
        args.proxy = args.proxy or config.get('DEFAULT', 'proxy', fallback=None)
        args.limit_rate = args.limit_rate or config.get('DEFAULT', 'limit_rate', fallback=None)

    try:
        if args.url:
            print_banner()
            if args.check:
                await check_website_status(args.url)
            elif args.website:
                await download_website(args.url, args.depth, args.convert_links, args.page_requisites)
            elif args.ftp_user or args.ftp_pass:
                await download_ftp(args.url, args.ftp_user, args.ftp_pass)
            elif args.torrent:
                await download_torrent(args.url, args.output or '.')
            else:
                plugin = plugin_manager.get_plugin(args.plugin) if args.plugin else None
                if plugin and hasattr(plugin, 'download'):
                    await plugin.download(args.url, args.output, args.resume, args.user_agent, quiet_mode=args.quiet, proxy=args.proxy, limit_rate=args.limit_rate)
                else:
                    await async_download_file(args.url, args.output, args.quiet, args.resume, parse_rate_limit(args.limit_rate))
        else:
            await interactive_mode()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation interrupted by user. Exiting...")
        logging.info("Operation interrupted by user.")
    except aiohttp.ClientError as e:
        print(f"{Fore.RED}Network error: {e}")
        logging.error(f"Network error: {e}")
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {e}")
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        await connection_pool.close()

def main() -> None:
    if sys.version_info < (3, 7):
        print(f"{Fore.RED}Python 3.7 or higher is required to run this script.")
        sys.exit(1)
    asyncio.run(async_main())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()  
        animated_exit()
