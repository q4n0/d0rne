import argparse
import subprocess
import concurrent.futures
import queue
import os
import time
import sys
import socket
import urllib.parse
import re
import requests
from colorama import init, Fore, Back, Style
import threading
import itertools
import libtorrent as lt
import signal
import configparser
import logging
from tqdm import tqdm

# New imports
import platform
import getpass
import gettext
import appdirs
from packaging import version

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(filename='d0rne.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ASCII art and banners remain unchanged
D0RNE_BANNER = f"""{Fore.CYAN}
                      .                             .                           
                    //                             \\\\                          
                   //                               \\\\                         
                  //                                 \\\\                        
                 //                *.*                \\\\                       
              .---.              .//|\\\\.              .---.                    
    ________ / .-. \_________..-~ *.-.* ~-..________ / .-. \\_________ -sr      
             \\ ~-~ /   /H-     `-=.___.=-'     -H\\   \\ ~-~ /                   
               ~~~    / H          [H]          H \\    ~~~                     
                     / *H*         *H*         *H* \\                           
                       UUU         UUU         UUU
{Fore.YELLOW}
          d0rne: Your cli Downloader Made by b0urn3 
        GITHUB:github.com/q4no | Instagram:onlybyhive 
        -------------------------------------------
"""

WEBSITE_UP_ASCII = f"""{Fore.GREEN}
   ____ _____  _  _____ _   _ ____  
  / ___|_   _|/ \|_   _| | | / ___| 
  \___ \ | | / _ \ | | | | | \___ \ 
   ___) || |/ ___ \| | | |_| |___) |
  |____/ |_/_/   \_\_|  \___/|____/ 
                                    
     Website is UP and running!
"""

WEBSITE_DOWN_ASCII = f"""{Fore.RED}
   ____  _____    _    ____  
  |  _ \| ____|  / \  |  _ \ 
  | | | |  _|   / _ \ | | | |
  | |_| | |___ / ___ \| |_| |
  |____/|_____/_/   \_\____/ 
                             
    Website is DOWN! :(
"""

DOWNLOAD_ASCII = f"""{Fore.BLUE}
   ____                      _                 _ 
  |  _ \  _____      ___ __ | | ___   __ _  __| |
  | | | |/ _ \ \ /\ / / '_ \| |/ _ \ / _` |/ _` |
  | |_| | (_) \ V  V /| | | | | (_) | (_| | (_| |
  |____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|
                                                 
"""

FTP_ASCII = f"""{Fore.MAGENTA}
   _____ _____ ____  
  |  ___|_   _|  _ \ 
  | |_    | | | |_) |
  |  _|   | | |  __/ 
  |_|     |_| |_|    
                     
"""

# New function for localization
def setup_localization():
    locales_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "locales")
    lang = gettext.translation("d0rne", locales_dir, fallback=True)
    lang.install()
    return lang.gettext

_ = setup_localization()

# New configuration functions
def get_config_path():
    config_dir = appdirs.user_config_dir("d0rne")
    return os.path.join(config_dir, "config")

def load_config():
    config = configparser.ConfigParser()
    config_file = get_config_path()
    if os.path.exists(config_file):
        config.read(config_file)
    return config

def save_config(config):
    config_file = get_config_path()
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w') as f:
        config.write(f)

# New safe_execute function
def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except requests.RequestException as e:
        print(f"{Fore.RED}{_('Network error')}: {e}")
    except IOError as e:
        print(f"{Fore.RED}{_('File I/O error')}: {e}")
    except ValueError as e:
        print(f"{Fore.RED}{_('Invalid input')}: {e}")
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}\n{_('Operation cancelled by user.')}")
    except Exception as e:
        print(f"{Fore.RED}{_('An unexpected error occurred')}: {e}")
    return None

# New function to check for updates
def check_for_updates(current_version):
    try:
        response = requests.get("https://api.github.com/repos/q4no/d0rne/releases/latest")
        response.raise_for_status()
        latest_version = response.json()["tag_name"]
        if version.parse(latest_version) > version.parse(current_version):
            print(f"{Fore.YELLOW}{_('A new version')} ({latest_version}) {_('is available. Please update.')}")
    except requests.RequestException as e:
        print(f"{Fore.RED}{_('Failed to check for updates')}: {e}")

class Loader:
    # Loader class remains unchanged

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

# Modified download_file function
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
            print(f"{Fore.RED}{_('Error downloading file')}: {e}")
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
            print(f"{Fore.RED}{_('Error downloading file')}: {e}")
            return False
    return True

# Modified run_wget function
def run_wget(command, show_progress=False, quiet_mode=False):
    loader = Loader(_("Preparing download..."), _("Download preparation complete."))
    loader.start()
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        last_update_time = 0
        update_interval = 5  # Update every 5 seconds in quiet mode

        loader.stop()
        print(f"{Fore.GREEN}{_('Starting download...')}")

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
            print(f"\n{Fore.RED}{_('Command failed with return code')} {rc}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: {e}")
        print(f"\n{Fore.RED}{_('Error')}: {e}")
        return False
    except KeyboardInterrupt:
        logging.warning("Download interrupted by user.")
        print(f"\n{Fore.YELLOW}{_('Download interrupted by user. Exiting...')}")
        return False
    finally:
        if loader.done == False:
            loader.stop()

# Modified download_with_retry function
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
        print(f"{Fore.YELLOW}{_('Download attempt')} {attempt + 1} {_('of')} {retry_attempts}")
        if run_wget(command, show_progress=True, quiet_mode=quiet_mode):
            logging.info(f"Download completed successfully: {url}")
            print(f"\n{Fore.GREEN}{_('Download completed successfully.')}")
            return True
        if attempt < retry_attempts - 1:
            logging.warning(f"Download failed. Retrying in {retry_delay} seconds...")
            print(f"\n{Fore.RED}{_('Download failed. Retrying in')} {retry_delay} {_('seconds')}...")
            time.sleep(retry_delay)
    
    logging.error(f"Max retry attempts reached. Download failed: {url}")
    print(f"\n{Fore.RED}{_('Max retry attempts reached. Download failed.')}")
    return False

def get_user_input(prompt, default=None):
    user_input = input(f"{Fore.YELLOW}{prompt}{Fore.RESET}")
    return user_input if user_input else default

# Modified download_torrent function
def download_torrent(torrent_path, save_path='.'):
    print(TORRENT_ASCII)
    ses = lt.session()
    params = {
        'save_path': save_path,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse,
    }
    
    print(f"{Fore.YELLOW}{_('Loading torrent...')}")
    try:
        if torrent_path.startswith('magnet:'):
            atp = lt.parse_magnet_uri(torrent_path)
            atp.save_path = save_path
            handle = ses.add_torrent(atp)
            print(f"{Fore.YELLOW}{_('Downloading metadata...')}")
            while not handle.status().has_metadata:
                time.sleep(1)
            print(f"{Fore.GREEN}{_('Got metadata, starting torrent download...')}")
        else:
            info = lt.torrent_info(torrent_path)
            handle = ses.add_torrent({'ti': info, 'save_path': save_path})
            print(f"{Fore.GREEN}{_('Torrent loaded, starting download...')}")

        print(f"{Fore.CYAN}{_('Starting download...')}")
        with tqdm(total=100, unit='%') as pbar:
            while (handle.status().state != lt.torrent_status.seeding):
                s = handle.status()
                
                state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
                try:
                    state = state_str[s.state]
                except IndexError:
                    state = 'unknown'
                
                pbar.update(s.progress * 100 - pbar.n)
                pbar.set_postfix({
                    'state': state,
                    'down': f"{s.download_rate / 1000:.1f} kB/s",
                    'up': f"{s.upload_rate / 1000:.1f} kB/s",
                    'peers': s.num_peers
                })
                
                time.sleep(1)

        print(f"\n{Fore.GREEN}{_('Download complete!')}")
    finally:
        print(f"{Fore.YELLOW}{_('Cleaning up...')}")
        ses.remove_torrent(handle)

def multiple_downloads():
    download_queue = DownloadQueue()
    while True:
        print(f"\n{Fore.CYAN}{_('Current download queue')}: {download_queue.queue.qsize()} {_('item(s)')}")
        choice = get_user_input(_("Add a download (y/n) or start processing queue (s): ")).lower()
        
        if choice == 'y':
            url = get_user_input(_("Enter the URL to download: "))
            output = get_user_input(_("Enter output filename (leave blank for default): "))
            resume = get_user_input(_("Resume partial download? (y/n): ")).lower() == 'y'
            user_agent = get_user_input(_("Enter user agent (leave blank for default): "))
            quiet_mode = get_user_input(_("Use quiet mode? (y/n): ")).lower() == 'y'
            
            download_queue.add_download(download_with_retry, url, output, resume, user_agent, quiet_mode=quiet_mode)
            print(f"{Fore.GREEN}{_('Download added to queue.')}")
        
        elif choice == 's':
            if download_queue.queue.empty():
                print(f"{Fore.YELLOW}{_('Queue is empty. Add some downloads first.')}")
            else:
                print(f"{Fore.GREEN}{_('Processing download queue...')}")
                download_queue.process_queue()
                print(f"{Fore.GREEN}{_('All downloads completed.')}")
            break
        
        elif choice == 'n':
            if not download_queue.queue.empty():
                confirm = get_user_input(_("Queue is not empty. Are you sure you want to exit? (y/n): ")).lower()
                if confirm == 'y':
                    break
            else:
                break
        
        else:
            print(f"{Fore.RED}{_('Invalid choice. Please try again.')}")

def print_menu():
    menu = f"""
{Fore.CYAN}╔════════════════════════════════════════╗
{Fore.CYAN}║       {_('d0rne-Downloader Menu')}            ║{Fore.CYAN} 
{Fore.CYAN}╠════════════════════════════════════════╝
{Fore.CYAN}║ {Fore.GREEN}1. {_('Download file(s)')}{Fore.CYAN}                    ║
{Fore.CYAN}║ {Fore.GREEN}2. {_('Q-download best for sensitive sites')}{Fore.CYAN} ║
{Fore.CYAN}║ {Fore.GREEN}3. {_('Download a website')}{Fore.CYAN}                  ║
{Fore.CYAN}║ {Fore.GREEN}4. {_('Download from FTP')}{Fore.CYAN}                   ║
{Fore.CYAN}║ {Fore.GREEN}5. {_('Download torrent')}{Fore.CYAN}                    ║
{Fore.CYAN}║ {Fore.GREEN}6. {_('Check web status-Is website online?')}{Fore.CYAN} ║
{Fore.CYAN}║ {Fore.GREEN}7. {_('Multiple downloads')}{Fore.CYAN}                  ║
{Fore.CYAN}║{_('To quit:Use "CTRL+C" to EXIT tool')}{Fore.CYAN}       ║
{Fore.CYAN}╚════════════════════════════════════════╝
"""
    print(menu)

def interactive_mode():
    print_banner()
    config = load_config()
    while True:
        print_menu()
        choice = get_user_input(_("Enter your choice (1-7): "))
        
        if choice == '1':
            url = get_user_input(_("Enter the URL to download: "))
            output = get_user_input(_("Enter output filename (leave blank for default): "))
            resume = get_user_input(_("Resume partial download? (y/n): ")).lower() == 'y'
            user_agent = get_user_input(_("Enter user agent (leave blank for default): "))
            proxy = get_user_input(_("Enter proxy (e.g., http://proxy:port) or leave blank: "))
            limit_rate = get_user_input(_("Enter download speed limit (e.g., 500k) or leave blank: "))
            safe_execute(download_with_retry, url, output, resume, user_agent, quiet_mode=False, proxy=proxy, limit_rate=limit_rate)
        elif choice == '2':
            url = get_user_input(_("Enter the URL to download: "))
            output = get_user_input(_("Enter output filename (leave blank for default): "))
            resume = get_user_input(_("Resume partial download? (y/n): ")).lower() == 'y'
            user_agent = get_user_input(_("Enter user agent (leave blank for default): "))
            safe_execute(download_with_retry, url, output, resume, user_agent, quiet_mode=True)
        elif choice == '3':
            url = get_user_input(_("Enter the website URL: "))
            depth = int(get_user_input(_("Enter depth (default 1): "), "1"))
            convert_links = get_user_input(_("Convert links for offline viewing? (y/n): ")).lower() == 'y'
            page_requisites = get_user_input(_("Download all page requisites? (y/n): ")).lower() == 'y'
            safe_execute(download_website, url, depth, convert_links, page_requisites)
        elif choice == '4':
            url = get_user_input(_("Enter the FTP URL: "))
            username = get_user_input(_("Enter FTP username (leave blank for anonymous): "))
            password = get_user_input(_("Enter FTP password (leave blank if not required): "))
            safe_execute(download_ftp, url, username, password)
        elif choice == '5':
            torrent_path = get_user_input(_("Enter the torrent file path or magnet link: "))
            save_path = get_user_input(_("Enter the save path (leave blank for current directory): ")) or '.'
            safe_execute(download_torrent, torrent_path, save_path)
        elif choice == '6':
            url = get_user_input(_("Enter the website URL to check: "))
            safe_execute(check_website_status, url)
        elif choice == '7':
            safe_execute(multiple_downloads)
        else:
            print(f"{Fore.RED}{_('Invalid choice. Please try again or use CTRL+C to exit.')}")

def main():
    parser = argparse.ArgumentParser(description=_("d0rne: Your cli Downloader\n Made by b0urn3 \n GITHUB:github.com/q4no | Instagram:onlybyhive "))
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

    args = parser.parse_args()

    config = load_config()
    if config:
        # Use config values as defaults if not specified in command line
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
    
    check_for_updates("1.0.2")  

    if args.url:
        print_banner()
        if args.check:
            safe_execute(check_website_status, args.url)
        elif args.website:
            safe_execute(download_website, args.url, args.depth, args.convert_links, args.page_requisites)
        elif args.ftp_user or args.ftp_pass:
            safe_execute(download_ftp, args.url, args.ftp_user, args.ftp_pass)
        elif args.torrent:
            safe_execute(download_torrent, args.url, args.output or '.')
        else:
            safe_execute(download_with_retry, args.url, args.output, args.resume, args.user_agent, quiet_mode=args.quiet, proxy=args.proxy, limit_rate=args.limit_rate)
    else:
        safe_execute(interactive_mode)

if __name__ == "__main__":
    main()
