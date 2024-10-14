import argparse
import os
import sys
import time
import re
import signal
import logging
import platform
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
import queue
import concurrent.futures

# Initialize colorama
init(autoreset=True)

# Set up logging
logging.basicConfig(filename='d0rne.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
              | TOOL VERSION: 1.0.2 |
            ----------------------------
"""

WEBSITE_UP_ASCII = f"{Fore.GREEN}[ONLINE] Website is UP and running!"
WEBSITE_DOWN_ASCII = f"{Fore.RED}[OFFLINE] Website is DOWN!"
DOWNLOAD_ASCII = f"{Fore.BLUE}[DOWNLOAD] Starting download..."
FTP_ASCII = f"{Fore.MAGENTA}[FTP] Connecting to FTP server..."

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

async def async_download_file(url, output, quiet_mode=False, resume=False, rate_limit=None):
    try:
        session = await connection_pool.get_session()
        headers = {}
        file_size = 0
        start_pos = 0

        if resume:
            if os.path.exists(output):
                start_pos = os.path.getsize(output)
                headers['Range'] = f'bytes={start_pos}-'

        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            file_size = int(response.headers.get('content-length', 0))

            if resume and response.status == 206:
                mode = 'ab'
            else:
                mode = 'wb'
                start_pos = 0

            limiter = RateLimiter(rate_limit) if rate_limit else None

            with tqdm(total=file_size, initial=start_pos, unit='iB', unit_scale=True, disable=quiet_mode) as progress_bar:
                async with aiofiles.open(output, mode) as f:
                    chunk_size = 8192
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if limiter:
                            await limiter.acquire(len(chunk))
                        await f.write(chunk)
                        progress_bar.update(len(chunk))

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"{Fore.RED}Error downloading file: {e}")
        return False
    return True

async def get_latest_version():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.github.com/repos/q4no/d0rne/releases/latest", timeout=5) as response:
                response.raise_for_status()  
                data = await response.json()
                if 'tag_name' in data:
                    return data['tag_name']
                else:
                    print(f"{Fore.YELLOW}Warning: Unable to parse version information from GitHub response.")
                    return None
    except aiohttp.ClientError as e:
        print(f"{Fore.YELLOW}Warning: Failed to check for updates: {e}")
        return None
    except ValueError as e:  
        print(f"{Fore.YELLOW}Warning: Failed to parse GitHub response: {e}")
        return None

async def check_for_updates():
    current_version = "1.0.2"
    latest_version = await get_latest_version()

    if latest_version is None:
        print(f"{Fore.YELLOW}Skipping update check due to error.")
        return

    if version.parse(latest_version) > version.parse(current_version):
        print(f"{Fore.YELLOW}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
        print(f"{Fore.YELLOW}┃ {Fore.GREEN}A new version of d0rne is available!              {Fore.YELLOW}┃")
        print(f"{Fore.YELLOW}┃ {Fore.CYAN}Current version: {current_version}                         {Fore.YELLOW}┃")
        print(f"{Fore.YELLOW}┃ {Fore.CYAN}Latest version: {latest_version}                          {Fore.YELLOW}┃")
        print(f"{Fore.YELLOW}┃ {Fore.CYAN}Run 'd0rne.py --update' to update automatically   {Fore.YELLOW}┃")
        print(f"{Fore.YELLOW}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}You are running the latest version of d0rne ({current_version}).{Style.RESET_ALL}")

def animated_exit():
    frames = [
        "Exiting d0rne |",
        "Exiting d0rne /",
        "Exiting d0rne -",
        "Exiting d0rne \\",
    ]
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

def print_banner():
    print(D0RNE_BANNER)

def create_progress_bar(percentage, width=50):
    filled_width = int(width * percentage // 100)
    bar = '█' * filled_width + '-' * (width - filled_width)
    return f"[{bar}] {percentage:.1f}%"

def parse_wget_output(line):
    progress_regex = r'(\d+)%\s+[\w.]+\s+([\d.]+\w)\s+([\d.]+\s*\w)/s(?:\s+eta\s+([\w\s]+))?'
    match = re.search(progress_regex, line)
    if match:
        percentage = float(match.group(1))
        downloaded = match.group(2)
        speed = match.group(3)
        eta = match.group(4) or "Unknown"
        return percentage, downloaded, speed, eta
    return None

def download_file(url, output, quiet_mode=False):
    if platform.system() == "Windows":
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 KB
            with open(output, 'wb') as f, tqdm(
                desc=output,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                disable=quiet_mode
            ) as progress_bar:
                for data in response.iter_content(block_size):
                    size = f.write(data)
                    progress_bar.update(size)
        except requests.RequestException as e:
            print(f"{Fore.RED}Error downloading file: {e}")
            return False
    else:
        try:
            wget_cmd = ["wget", "-O", output, url]
            if quiet_mode:
                wget_cmd.append("--quiet")
            else:
                wget_cmd.extend(["--progress=bar:force", "--show-progress"])
            subprocess.run(wget_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Error downloading file: {e}")
            return False
    return True
def run_wget(command, show_progress=False, quiet_mode=False):
    loader = Loader("Preparing download...", "Download preparation complete.")
    loader.start()
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        loader.stop()
        print(f"{Fore.GREEN}Starting download...")

        with tqdm(total=100, unit="%", bar_format="{l_bar}{bar}| {n:.2f}%", disable=quiet_mode) as pbar:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    progress_info = parse_wget_output(output)
                    if progress_info:
                        percentage, downloaded, speed, eta = progress_info
                        pbar.update(percentage - pbar.n)
                        pbar.set_postfix({"Downloaded": downloaded, "Speed": speed, "ETA": eta})
                    if not show_progress or quiet_mode:
                        logging.info(output.strip())

        rc = process.poll()
        if rc != 0:
            logging.error(f"Command failed with return code {rc}")
            print(f"\n{Fore.RED}Command failed with return code {rc}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: {e}")
        print(f"\n{Fore.RED}Error: {e}")
        return False
    except KeyboardInterrupt:
        logging.warning("Download interrupted by user.")
        print(f"\n{Fore.YELLOW}Download interrupted by user. Exiting...")
        return False
    finally:
        if loader.done == False:
            loader.stop()

def download_with_retry(url, output=None, resume=False, user_agent=None, retry_attempts=3, retry_delay=5, quiet_mode=False, proxy=None, limit_rate=None):
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
        if run_wget(command, show_progress=True, quiet_mode=quiet_mode):
            logging.info(f"Download completed successfully: {url}")
            print(f"\n{Fore.GREEN}Download completed successfully.")
            return True
        if attempt < retry_attempts - 1:
            logging.warning(f"Download failed. Retrying in {retry_delay} seconds...")
            print(f"\n{Fore.RED}Download failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    logging.error(f"Max retry attempts reached. Download failed: {url}")
    print(f"\n{Fore.RED}Max retry attempts reached. Download failed.")
    return False

def get_user_input(prompt, default=None):
    user_input = input(f"{Fore.YELLOW}{prompt}{Fore.RESET}")
    return user_input if user_input else default

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
{Fore.CYAN}║To quit:Use "CTRL+C" to EXIT tool{Fore.CYAN}       ║
{Fore.CYAN}╚════════════════════════════════════════╝
"""
    print(menu)

def interactive_mode():
    print_banner()
    config = load_config()
    while True:
        print_menu()
        choice = get_user_input("Enter your choice (1-7): ")
        
        if choice == '1':
            url = get_user_input("Enter the URL to download: ")
            output = get_user_input("Enter output filename (leave blank for default): ")
            resume = get_user_input("Resume partial download? (y/n): ").lower() == 'y'
            user_agent = get_user_input("Enter user agent (leave blank for default): ")
            proxy = get_user_input("Enter proxy (e.g., http://proxy:port) or leave blank: ")
            limit_rate = get_user_input("Enter download speed limit (e.g., 500k) or leave blank: ")
            asyncio.run(download_with_retry(url, output, resume, user_agent, quiet_mode=False, proxy=proxy, limit_rate=limit_rate))
        elif choice == '2':
            url = get_user_input("Enter the URL to download: ")
            output = get_user_input("Enter output filename (leave blank for default): ")
            resume = get_user_input("Resume partial download? (y/n): ").lower() == 'y'
            user_agent = get_user_input("Enter user agent (leave blank for default): ")
            asyncio.run(download_with_retry(url, output, resume, user_agent, quiet_mode=True))
        # ... (implement other menu options)
        else:
            print(f"{Fore.RED}Invalid choice. Please try again or use CTRL+C to exit.")

async def async_main():
    parser = argparse.ArgumentParser(description="d0rne: Your cli Downloader")
    parser.add_argument("url", nargs="?", help=_("URL or torrent file/magnet link to download"))
    parser.add_argument("-o", "--output", help=_("Output filename or directory"))
    parser.add_argument("-r", "--resume", action="store_true", help=_("Resume partially downloaded files"))
    parser.add_argument("-u", "--user-agent", help=_("Set user agent string"))
    parser.add_argument("-w", "--website", action="store_true", help=_("Download entire website"))
    parser.add_argument("-d", "--depth", type=int, default=1, help=_("Depth for website download (default: 1)"))
    parser.add_argument("-k", "--convert-links", action="store_true", help=_("Convert links for offline viewing"))
    parser.add_argument("-p", "--page-requisites", action="store_true", help=_("Download all page requisites"))
    parser.add_argument("--ftp-user", help=_("FTP username"))
    parser.add_argument("--ftp-pass", help=_("FTP password"))
    parser.add_argument("--check", action="store_true", help=_("Check website status"))
    parser.add_argument("-q", "--quiet", action="store_true", help=_("Quiet mode for downloads"))
    parser.add_argument("-t", "--torrent", action="store_true", help=_("Download as torrent"))
    parser.add_argument("--proxy", help=_("Set proxy server (e.g., http://proxy:port)"))
    parser.add_argument("--limit-rate", help=_("Limit download speed (e.g., 500k)"))
    parser.add_argument("--no-color", action="store_true", help=_("Disable colored output"))
    parser.add_argument("--update", action="store_true", help=_("Update d0rne to the latest version"))
    parser.add_argument("--http2", action="store_true", help=_("Use HTTP/2 for downloads"))
    parser.add_argument("--plugin", help=_("Use a specific plugin for download"))
    
   args = parser.parse_args()

    if args.update:
        await self_update()
        return

    config = load_config()
    if config:
       if not args.output:
            args.output = config.get('DEFAULT', 'output_dir', fallback=None)
        if not args.user_agent:
            args.user_agent = config.get('DEFAULT', 'user_agent', fallback=None)
        if not args.proxy:
            args.proxy = config.get('DEFAULT', 'proxy', fallback=None)
        if not args.limit_rate:
            args.limit_rate = config.get('DEFAULT', 'limit_rate', fallback=None)
    
 if args.no_color:
        init(strip=True, convert=False)
    
    await check_for_updates()

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
    finally:
        await connection_pool.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()  
        animated_exit()
