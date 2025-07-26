# SteamOS Backup & Sync Tool

A robust backup and sync application designed for SteamOS (e.g., Steam Deck), allowing seamless synchronization between your device and cloud storage using Rclone.

## Features

* **Multiple Backup Tasks**: Configure various source/destination pairs.
* **Trigger Options**:

  * **Scheduled**: Automatic sync at specified times.
  * **Wi-Fi Triggered**: Automatically sync upon connecting to specified Wi-Fi networks.
  * **Manual Trigger**: Initiate backup on demand via the GUI.
* **Efficient Syncing**: Hash comparisons to skip syncing identical files, reducing data usage.
* **User-Friendly GUI**: Easily configure and manage backup tasks.

## Requirements

* SteamOS 3.x (Arch Linux based)
* Python 3.x
* Rclone
* PyQt6
* rclone-python 0.1.23
* wireless\_tools

## Installation

### Step 1: Install Dependencies

Open a terminal in SteamOS Desktop Mode:

```bash
sudo pacman -S python python-pip rclone wireless_tools
pip install PyQt6==6.7.0 rclone-python==0.1.23
```

### Step 2: Setup

Clone or copy the provided files to your Steam Deck:

* `backup_service.py` → `~/.local/bin/`
* `gui.py` → `~/my_backup_app/`

Create configuration directory:

```bash
mkdir -p ~/.config/my_backup_app
```

Copy the systemd service:

```bash
sudo cp backup_service.service /etc/systemd/system/
sudo systemctl enable --now backup_service
```

## Usage

### Configure Rclone

Before using the tool, configure your cloud storage:

```bash
rclone config
```

### Using the GUI

Open a terminal and launch:

```bash
python ~/my_backup_app/gui.py
```

* **Add tasks** by specifying local paths, cloud destinations, and selecting trigger types.
* **Scheduled Tasks**: Set exact sync times.
* **Wi-Fi Tasks**: Enter the SSID of your Wi-Fi network.
* **Manual Tasks**: Sync anytime via the "Trigger Manual Sync Now" button.

### Sync Behavior

* **Scheduled** tasks execute once daily at the configured time.
* **Wi-Fi** tasks check for syncing at boot and every 15 minutes upon Wi-Fi connection.
* Sync operations will only execute if local and cloud file hashes differ, conserving bandwidth.

### Logs & Monitoring

View logs using:

```bash
journalctl -u backup_service -f
```

## Security & Recommendations

* Ensure your Rclone configuration is secure:

  ```bash
  chmod 600 ~/.config/rclone/rclone.conf
  ```

## Support & Issues

For issues or further assistance, contact the developer or raise an issue on the project repository.
