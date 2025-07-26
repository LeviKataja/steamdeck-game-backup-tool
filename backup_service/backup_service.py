import rclone
import json
import time
import logging
import subprocess
import datetime
import hashlib
import os

CONFIG_PATH = "/home/deck/.config/my_backup_app/config.json"
MANUAL_TRIGGER = "/tmp/manual_sync.trigger"
logging.basicConfig(level=logging.INFO)

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def get_connected_ssid():
    try:
        ssid = subprocess.check_output(['iwgetid', '-r'], text=True).strip()
        return ssid
    except subprocess.CalledProcessError:
        return None

def file_hash(path):
    hash_md5 = hashlib.md5()
    if os.path.isfile(path):
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    return None

def directory_hash(path):
    hashes = []
    for root, dirs, files in os.walk(path):
        for names in sorted(files):
            file_path = os.path.join(root, names)
            hashes.append(file_hash(file_path))
    combined_hash = hashlib.md5("".join(sorted(hashes)).encode()).hexdigest()
    return combined_hash

def remote_hash(remote_path):
    try:
        result = rclone.lsf(remote_path, flags=["--hash", "MD5"])
        combined_hash = hashlib.md5("".join(sorted(result)).encode()).hexdigest()
        return combined_hash
    except Exception as e:
        logging.error(f"Failed to get remote hash: {e}")
        return None

def needs_sync(local, remote, direction):
    if direction == 'upload':
        local_hash = directory_hash(local)
        remote_hash_val = remote_hash(remote)
    else:  # download
        remote_hash_val = remote_hash(remote)
        local_hash = directory_hash(local)

    logging.info(f"Local Hash: {local_hash}, Remote Hash: {remote_hash_val}")

    return local_hash != remote_hash_val

def run_task(task):
    local = task['local_path']
    remote = task['remote_path']
    direction = task.get('direction', 'upload')

    if not needs_sync(local, remote, direction):
        logging.info("Hashes match; skipping sync.")
        return

    if direction == 'upload':
        logging.info(f"Uploading: {local} → {remote}")
        result = rclone.sync(local, remote)
    else:
        logging.info(f"Downloading: {remote} → {local}")
        result = rclone.sync(remote, local)

    logging.info(f"Sync completed: {result}")

def should_run(task, last_run_times):
    trigger = task.get('trigger', {})
    trigger_type = trigger.get('type')
    now = datetime.datetime.now()
    task_id = f"{task['local_path']}-{task['remote_path']}"

    if trigger_type == 'scheduled':
        sched_time = datetime.datetime.strptime(trigger.get('time'), "%H:%M").time()
        last_run = last_run_times.get(task_id)
        if now.time() >= sched_time and (not last_run or last_run.date() < now.date()):
            last_run_times[task_id] = now
            return True

    elif trigger_type == 'wifi':
        connected_ssid = get_connected_ssid()
        ssid = trigger.get('ssid')
        last_run = last_run_times.get(task_id)

        if connected_ssid == ssid:
            if not last_run or (now - last_run).seconds >= 900:  # every 15 mins
                last_run_times[task_id] = now
                return True

    elif trigger_type == 'manual':
        if os.path.exists(MANUAL_TRIGGER):
            os.remove(MANUAL_TRIGGER)
            return True

    return False

def main():
    last_run_times = {}
    logging.info("Service started, initial Wi-Fi checks in progress.")

    # Initial Wi-Fi check immediately after boot
    config = load_config()
    for task in config.get('tasks', []):
        if task.get('trigger', {}).get('type') == 'wifi' and should_run(task, last_run_times):
            run_task(task)

    while True:
        config = load_config()
        tasks = config.get('tasks', [])
        for task in tasks:
            try:
                if should_run(task, last_run_times):
                    run_task(task)
            except Exception as e:
                logging.error(f"Task failed: {task}, Error: {e}")

        time.sleep(60)  # Check triggers every minute

if __name__ == "__main__":
    main()