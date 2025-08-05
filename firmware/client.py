import requests
import json
import os
import time
import subprocess
import sys
from datetime import datetime

# --- Configuration Loading ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config():
    """Loads configuration from config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE} not found. Please create it.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {CONFIG_FILE}.")
        sys.exit(1)

config = load_config()

DISPLAY_UUID = config['display_uuid']
API_KEY = config['api_key']
BACKEND_BASE_URL = config['backend_base_url']
MEDIA_STORAGE_PATH = config['media_storage_path']
STATUS_CHECK_INTERVAL = config['status_check_interval_seconds']


# --- Global State ---
last_backend_update_timestamp = None
mpv_process = None # To hold the mpv subprocess

# --- API Interaction Functions ---
def get_new_media_ids():
    """Fetches a list of new media IDs from the backend."""
    url = f"{BACKEND_BASE_URL}/displays/{DISPLAY_UUID}/media_to_download"
    headers = {"X-API-KEY": API_KEY}
    print("Attempting to connect to backend at " + url) # NEW
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("Successfully connected to backend.") # NEW
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting new media IDs: {e}")
        return []

def download_media(media_id):
    """Downloads a specific media file by its ID."""
    url = f"{BACKEND_BASE_URL}/media/{media_id}"
    headers = {"X-API-KEY": API_KEY}
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        if 'image/jpeg' in content_type:
            extension = '.jpeg'
        elif 'image/png' in content_type:
            extension = '.png'
        elif 'image/gif' in content_type:
            extension = '.gif'
        elif 'image/webp' in content_type:
            extension = '.webp'
        elif 'image/svg+xml' in content_type:
            extension = '.svg'
        elif 'video/mp4' in content_type:
            extension = '.mp4'
        elif 'video/webm' in content_type:
            extension = '.webm'
        elif 'video/ogg' in content_type:
            extension = '.ogg'
        elif 'video/x-msvideo' in content_type:
            extension = '.avi'
        else:
            extension = '.bin'

        filepath = os.path.join(MEDIA_STORAGE_PATH, f"{media_id}{extension}")
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading media {media_id}: {e}")
        return None

def mark_media_downloaded_on_backend(media_id):
    """Marks a media item as downloaded on the backend."""
    url = f"{BACKEND_BASE_URL}/displays/{DISPLAY_UUID}/mark_downloaded/{media_id}"
    headers = {"X-API-KEY": API_KEY}
    try:
        response = requests.post(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Successfully marked media {media_id} as downloaded on backend.")
    except requests.exceptions.RequestException as e:
        print(f"Error marking media {media_id} as downloaded: {e}")

# --- MPV Control ---
def get_local_media_paths():
    """Builds a list of all media files currently in the local directory."""
    media_paths = []
    # Use a sorted list for consistent playback order
    for filename in sorted(os.listdir(MEDIA_STORAGE_PATH)):
        filepath = os.path.join(MEDIA_STORAGE_PATH, filename)
        if os.path.isfile(filepath):
            media_paths.append(filepath)
    return media_paths

def start_mpv_playlist():
    """Starts mpv with all locally stored media files and new options."""
    global mpv_process
    media_paths = get_local_media_paths()

    if not media_paths:
        print("No media to play. Stopping mpv if running.")
        stop_mpv()
        return

    # Updated mpv command with the requested flags
    mpv_command = [
        "mpv",
        "--image-display-duration=3",
        "--loop-playlist=inf",
        "--shuffle",
        "--fs",
        "--hwdec=auto",
       # "--no-osc",
        #"--no-osd-bar",
        "--vo=gpu",
        #"--input-ipc-server=/tmp/mpvsocket"
    ] + media_paths
    
    # Existing logic to handle a running mpv process
    if mpv_process and mpv_process.poll() is None:
        print("mpv is already running. Stopping to reload playlist...")
        stop_mpv()
        time.sleep(1)

    print(f"Starting mpv with: {' '.join(mpv_command)}")
    try:
        mpv_process = subprocess.Popen(mpv_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("mpv started.")
    except FileNotFoundError:
        print("Error: mpv command not found. Is mpv installed and in PATH?")
    except Exception as e:
        print(f"Error starting mpv: {e}")

def stop_mpv():
    """Stops the currently running mpv process."""
    global mpv_process
    if mpv_process and mpv_process.poll() is None:
        print("Terminating mpv process...")
        mpv_process.terminate()
        try:
            mpv_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mpv_process.kill()
            print("mpv process killed.")
        mpv_process = None
        print("mpv stopped.")

# --- Main Logic ---
def main_loop():
    """Main loop for checking status and updating media."""
    print("Digital Signage Client Starting...")
    
    print("Attempting to start initial mpv playlist...") # NEW
    start_mpv_playlist()
    print("Initial mpv playlist started. Entering main loop...") # NEW

    while True:
        print(f"\nChecking backend for new media...")
        new_media_ids = get_new_media_ids()

        if new_media_ids:
            print(f"Found {len(new_media_ids)} new media items to download.")
            
            downloaded_count = 0
            for media_id_str in new_media_ids:
                print(f"Downloading new media ID: {media_id_str}")
                filepath = download_media(media_id_str)
                if filepath:
                    mark_media_downloaded_on_backend(media_id_str)
                    downloaded_count += 1
            
            if downloaded_count > 0:
                print("Finished downloading new media. Restarting mpv with updated playlist.")
                start_mpv_playlist()

        else:
            print("No new media found on backend.")

        print(f"Waiting for {STATUS_CHECK_INTERVAL} seconds...") # NEW
        time.sleep(STATUS_CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    finally:
        stop_mpv()