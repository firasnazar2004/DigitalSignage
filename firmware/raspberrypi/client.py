import requests
import json
import os
import time
import subprocess
import sys
import shutil
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


last_backend_update_timestamp = None
mpv_process = None 

# --- API Interaction Functions ---
def get_new_media():
    """Fetches a list of new media IDs from the backend."""
    url = f"{BACKEND_BASE_URL}/displays/{DISPLAY_UUID}/sync"
    headers = {"X-API-KEY": API_KEY}
    print("Attempting to connect to backend at " + url)
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("Successfully connected to backend.")
        sync_data = response.json()
        return sync_data.get('new_media' ,[])
    except requests.exceptions.RequestException as e:
        print(f"Error getting new media IDs: {e}")
        return []

def clear_media_folder():
    """Deletes all files in the media folder."""
    if os.path.exists(MEDIA_STORAGE_PATH):
        for filename in os.listdir(MEDIA_STORAGE_PATH):
            file_path = os.path.join(MEDIA_STORAGE_PATH, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

def download_media(media_id , original_filename):
    url = f"{BACKEND_BASE_URL}/media/{media_id}"
    headers = {"X-API-KEY": API_KEY}
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        filepath = os.path.join(MEDIA_STORAGE_PATH, original_filename)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading media {media_id}: {e}")
        return None

def mark_media_downloaded_on_backend(media_ids):
    """Marks a media item as downloaded on the backend using the bulk endpoint."""
    url = f"{BACKEND_BASE_URL}/displays/{DISPLAY_UUID}/mark_downloaded_bulk"
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}

    payload = {"media_ids": media_ids}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        print(f"Successfully marked {len(media_ids)} media items as downloaded on backend.")
    except requests.exceptions.RequestException as e:
        print(f"Error marking media as downloaded: {e}")

# --- MPV Control ---
def get_local_media_paths():
    """Builds a list of all media files currently in the local directory."""
    media_paths = []

    for filename in sorted(os.listdir(MEDIA_STORAGE_PATH)):
        filepath = os.path.join(MEDIA_STORAGE_PATH, filename)
        if os.path.isfile(filepath):
            media_paths.append(filepath)
    return media_paths

def start_mpv_playlist():
    """Starts mpv with all locally stored media files and new options"""
    global mpv_process
    media_paths = get_local_media_paths()

    if not media_paths:
        print("No media to play. Stopping mpv if running.")
        stop_mpv()
        return


    mpv_command = [
        "mpv",
        "--image-display-duration=3",
        "--loop-playlist=inf",
        "--shuffle",
        "--fs",
        "--hwdec=auto",
        "--vo=gpu",
    ] + media_paths


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
    time.sleep(5)
    print("Digital Signage Client Starting...")

    print("Attempting to start initial mpv playlist...")
    start_mpv_playlist()
    print("Initial mpv playlist started. Entering main loop...")

    while True:
        print(f"\nChecking backend for new media...")
        new_media = get_new_media()

        if new_media:
            print(f"Found {len(new_media)} new media items to download.")
            downloaded_ids = []


            override_flag = any(item.get("override", False) for item in new_media)
            if override_flag:
                print("Override=True → clearing media folder before download...")
                clear_media_folder()

            for media_item in new_media:
                media_id_str = media_item['id']
                original_filename = media_item['original_filename']

                print(f"Downloading new media: {original_filename}")
                filepath = download_media(media_id_str, original_filename)
                if filepath:
                    downloaded_ids.append(media_id_str) 

            if downloaded_ids:

                mark_media_downloaded_on_backend(downloaded_ids)
                print("Finished downloading new media. Restarting mpv with updated playlist.")
                start_mpv_playlist()

        else:
            print("No new media found on backend.")

        print(f"Waiting for {STATUS_CHECK_INTERVAL} seconds...")
        time.sleep(STATUS_CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    finally:
        stop_mpv()