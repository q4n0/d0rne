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
import time
import sys
import signal

# Initialize colorama
init(autoreset=True)

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

def run_wget(command, show_progress=False, quiet_mode=False):
    loader = Loader("Preparing download...", "Download preparation complete.")
    loader.start()
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        last_update_time = 0
        update_interval = 5  # Update every 5 seconds in quiet mode

        loader.stop()
        print(f"{Fore.GREEN}Starting download...")

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                if show_progress and not quiet_mode:
                    progress_info = parse_wget_output(output)
                    if progress_info:
                        percentage, downloaded, speed, eta = progress_info
                        progress_bar = create_progress_bar(percentage)
                        status_line = f"\r{Fore.CYAN}{progress_bar} {Fore.GREEN}{downloaded} @ {speed} {Fore.YELLOW}ETA: {eta}"
                        sys.stdout.write(status_line)
                        sys.stdout.flush()
                elif show_progress and quiet_mode:
                    current_time = time.time()
                    if current_time - last_update_time >= update_interval:
                        progress_info = parse_wget_output(output)
                        if progress_info:
                            percentage, downloaded, speed, eta = progress_info
                            print(f"{Fore.CYAN}Progress: {Fore.GREEN}{percentage:.1f}% {Fore.YELLOW}({downloaded} @ {speed})")
                        last_update_time = current_time
                else:
                    print(output.strip())

        rc = process.poll()
        if rc != 0:
            print(f"\n{Fore.RED}Command failed with return code {rc}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n{Fore.RED}Error: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Download interrupted by user. Exiting...")
        return False
    finally:
        if loader.done == False:
            loader.stop()

def check_website_status(url):
    loader = Loader(f"d0rne is checking the status of {url}...", "Status check complete.")
    loader.start()
    try:
        response = requests.get(url, timeout=10)
        loader.stop()
        if response.status_code == 200:
            print(WEBSITE_UP_ASCII)
            print(f"{Fore.GREEN}Response time: {response.elapsed.total_seconds():.2f} seconds")
            print(f"{Fore.GREEN}Status code: {response.status_code}")
        else:
            print(WEBSITE_DOWN_ASCII)
            print(f"{Fore.RED}Status code: {response.status_code}")
    except requests.RequestException:
        loader.stop()
        print(WEBSITE_DOWN_ASCII)
        print(f"{Fore.RED}Could not connect to the website")

def download_with_retry(url, output=None, resume=False, user_agent=None, retry_attempts=3, retry_delay=5, quiet_mode=False):
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
    
    command.append(url)

    for attempt in range(retry_attempts):
        print(f"{Fore.YELLOW}d0rne download attempt {attempt + 1} of {retry_attempts}")
        if run_wget(command, show_progress=True, quiet_mode=quiet_mode):
            print(f"\n{Fore.GREEN}d0rne has completed the download successfully.")
            return True
        if attempt < retry_attempts - 1:
            print(f"\n{Fore.RED}Download failed. d0rne will retry in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print(f"\n{Fore.RED}Max retry attempts reached. d0rne could not complete the download.")
    return False

def download_website(url, depth=1, convert_links=False, page_requisites=False, quiet_mode=False):
    print(DOWNLOAD_ASCII)
    command = ["wget", "-r", "-l", str(depth), "--no-parent", "--progress=bar:force"]
    
    if convert_links:
        command.append("-k")
    if page_requisites:
        command.append("-p")
    if quiet_mode:
        command.append("--quiet")
    
    command.append(url)
    if run_wget(command, show_progress=True, quiet_mode=quiet_mode):
        print(f"\n{Fore.GREEN}d0rne has completed the website download successfully.")
    else:
        print(f"\n{Fore.RED}d0rne encountered an error during the website download.")

def download_ftp(url, username=None, password=None, quiet_mode=False):
    print(FTP_ASCII)
    command = ["wget", "--progress=bar:force"]
    
    if username:
        command.extend(["--ftp-user", username])
    if password:
        command.extend(["--ftp-password", password])
    if quiet_mode:
        command.append("--quiet")
    
    command.append(url)
    if run_wget(command, show_progress=True, quiet_mode=quiet_mode):
        print(f"\n{Fore.GREEN}d0rne has completed the FTP download successfully.")
    else:
        print(f"\n{Fore.RED}d0rne encountered an error during the FTP download.")

def get_user_input(prompt, default=None):
    user_input = input(f"{Fore.YELLOW}{prompt}{Fore.RESET}")
    return user_input if user_input else default
import libtorrent as lt
import time
import sys

# ... (previous imports and code remain the same)

TORRENT_ASCII = f"""{Fore.GREEN}
  _________ ____  _____  _____  ______ _   _ _______ 
 |__   __/ __ \|  __ \|  __ \|  ____| \ | |__   __|
    | | | |  | | |__) | |__) | |__  |  \| |  | |   
    | | | |  | |  _  /|  _  /|  __| | . ` |  | |   
    | | | |__| | | \ \| | \ \| |____| |\  |  | |   
    |_|  \____/|_|  \_\_|  \_\______|_| \_|  |_|   
"""

def tiny_missile_animation():
    missile_frames = [">", "->", "-->", "--->", "---->", "----->"]
    explosion_frames = ["*", "x", "X", "#", "*"]
    
    for frame in missile_frames:
        sys.stdout.write('\r' + frame.ljust(6))
        sys.stdout.flush()
        time.sleep(0.1)
    
    for frame in explosion_frames:
        sys.stdout.write('\r' + frame.center(6))
        sys.stdout.flush()
        time.sleep(0.1)
    
    sys.stdout.write('\r' + "BOOM!".center(6))
    sys.stdout.flush()
    time.sleep(0.5)
    print(f"\n{Fore.RED}Mayday! Mayday!")
    print(f"{Fore.YELLOW}Mission Aborted!")

def interrupt_handler(signum, frame):
    print()  # Move to a new line
    tiny_missile_animation()
    sys.exit(1)

# Register the interrupt handler
signal.signal(signal.SIGINT, interrupt_handler)

# Wrap all main functions with try-except to catch any other exceptions
def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"\n{Fore.RED}An error occurred: {e}")
        tiny_missile_animation()

# Modify all your main functions to use safe_execute
class DownloadQueue:
    def __init__(self, max_concurrent=3):
        self.queue = queue.Queue()
        self.max_concurrent = max_concurrent

    def add_download(self, download_func, *args, **kwargs):
        self.queue.put((download_func, args, kwargs))

    def process_queue(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            while not self.queue.empty():
                download_func, args, kwargs = self.queue.get()
                executor.submit(safe_execute, download_func, *args, **kwargs)
                self.queue.task_done()

def download_torrent(torrent_path, save_path='.'):
    print(TORRENT_ASCII)
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
                time.sleep(1)
            print(f"{Fore.GREEN}Got metadata, starting torrent download...")
        else:
            info = lt.torrent_info(torrent_path)
            handle = ses.add_torrent({'ti': info, 'save_path': save_path})
            print(f"{Fore.GREEN}Torrent loaded, starting download...")

        print(f"{Fore.CYAN}Starting download...")
        while (handle.status().state != lt.torrent_status.seeding):
            s = handle.status()
            
            state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
            try:
                state = state_str[s.state]
            except IndexError:
                state = 'unknown'
            
            print(f'\r{state} {s.progress*100:.2f}% complete (down: {s.download_rate/1000:.1f} kB/s up: {s.upload_rate/1000:.1f} kB/s peers: {s.num_peers})', end=' ')
            
            sys.stdout.flush()
            time.sleep(1)

        print(f"\n{Fore.GREEN}Download complete!")
    finally:
        print(f"{Fore.YELLOW}Cleaning up...")
        ses.remove_torrent(handle)

def multiple_downloads():
    download_queue = DownloadQueue()
    while True:
        print(f"\n{Fore.CYAN}Current download queue: {download_queue.queue.qsize()} item(s)")
        choice = get_user_input("Add a download (y/n) or start processing queue (s): ").lower()
        
        if choice == 'y':
            url = get_user_input("Enter the URL to download: ")
            output = get_user_input("Enter output filename (leave blank for default): ")
            resume = get_user_input("Resume partial download? (y/n): ").lower() == 'y'
            user_agent = get_user_input("Enter user agent (leave blank for default): ")
            quiet_mode = get_user_input("Use quiet mode? (y/n): ").lower() == 'y'
            
            download_queue.add_download(download_with_retry, url, output, resume, user_agent, quiet_mode=quiet_mode)
            print(f"{Fore.GREEN}Download added to queue.")
        
        elif choice == 's':
            if download_queue.queue.empty():
                print(f"{Fore.YELLOW}Queue is empty. Add some downloads first.")
            else:
                print(f"{Fore.GREEN}Processing download queue...")
                download_queue.process_queue()
                print(f"{Fore.GREEN}All downloads completed.")
            break
        
        elif choice == 'n':
            if not download_queue.queue.empty():
                confirm = get_user_input("Queue is not empty. Are you sure you want to exit? (y/n): ").lower()
                if confirm == 'y':
                    break
            else:
                break
        
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.")

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
    while True:
        print_menu()
        choice = get_user_input("Enter your choice (1-7): ")
        
        if choice == '1':
            url = get_user_input("Enter the URL to download: ")
            output = get_user_input("Enter output filename (leave blank for default): ")
            resume = get_user_input("Resume partial download? (y/n): ").lower() == 'y'
            user_agent = get_user_input("Enter user agent (leave blank for default): ")
            safe_execute(download_with_retry, url, output, resume, user_agent, quiet_mode=False)
        elif choice == '2':
            url = get_user_input("Enter the URL to download: ")
            output = get_user_input("Enter output filename (leave blank for default): ")
            resume = get_user_input("Resume partial download? (y/n): ").lower() == 'y'
            user_agent = get_user_input("Enter user agent (leave blank for default): ")
            safe_execute(download_with_retry, url, output, resume, user_agent, quiet_mode=True)
        elif choice == '3':
            url = get_user_input("Enter the website URL: ")
            depth = int(get_user_input("Enter depth (default 1): ", "1"))
            convert_links = get_user_input("Convert links for offline viewing? (y/n): ").lower() == 'y'
            page_requisites = get_user_input("Download all page requisites? (y/n): ").lower() == 'y'
            safe_execute(download_website, url, depth, convert_links, page_requisites)
        elif choice == '4':
            url = get_user_input("Enter the FTP URL: ")
            username = get_user_input("Enter FTP username (leave blank for anonymous): ")
            password = get_user_input("Enter FTP password (leave blank if not required): ")
            safe_execute(download_ftp, url, username, password)
        elif choice == '5':
            torrent_path = get_user_input("Enter the torrent file path or magnet link: ")
            save_path = get_user_input("Enter the save path (leave blank for current directory): ") or '.'
            safe_execute(download_torrent, torrent_path, save_path)
        elif choice == '6':
            url = get_user_input("Enter the website URL to check: ")
            safe_execute(check_website_status, url)
        elif choice == '7':
            safe_execute(multiple_downloads)
        else:
            print(f"{Fore.RED}Invalid choice. Please try again or use CTRL+C to exit.")
            
def main():
    parser = argparse.ArgumentParser(description="d0rne: Your cli Downloader\n Made by b0urn3 \n GITHUB:github.com/q4no | Instagram:onlybyhive ")
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

    args = parser.parse_args()

    if args.url:
        print_banner()
        if args.check:
            safe_execute(check_website_status, args.url)
        elif args.website:
            safe_execute(download_website, args.url, args.depth, args.convert_links, args.page_requisites)
        elif args.ftp_user or args.ftp_pass:
            safe_execute(download_ftp, args.url, args.ftp_user, args.ftp_pass)
        else:
            safe_execute(download_with_retry, args.url, args.output, args.resume, args.user_agent)
    else:
        safe_execute(interactive_mode)

if __name__ == "__main__":
    main()
