import sys, json, os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLineEdit,
    QLabel, QComboBox, QListWidget, QMessageBox, QHBoxLayout, QTimeEdit
)

CONFIG_PATH = "/home/deck/.config/my_backup_app/config.json"
MANUAL_TRIGGER = "/tmp/manual_sync.trigger"

class ConfigApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backup Task Manager")
        self.resize(600, 500)

        self.layout = QVBoxLayout()

        self.task_list = QListWidget()
        self.layout.addWidget(self.task_list)

        self.local_input = QLineEdit()
        self.local_btn = QPushButton("Select Local Folder")
        self.local_btn.clicked.connect(self.select_local)

        self.remote_input = QLineEdit()

        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["upload", "download"])

        self.trigger_type_combo = QComboBox()
        self.trigger_type_combo.addItems(["scheduled", "wifi", "manual"])
        self.trigger_type_combo.currentTextChanged.connect(self.toggle_trigger_input)

        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm")
        self.wifi_input = QLineEdit()

        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self.add_task)

        remove_btn = QPushButton("Remove Selected Task")
        remove_btn.clicked.connect(self.remove_task)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_settings)

        manual_sync_btn = QPushButton("Trigger Manual Sync Now")
        manual_sync_btn.clicked.connect(self.trigger_manual_sync)

        self.layout.addWidget(QLabel("Local Path"))
        self.layout.addWidget(self.local_input)
        self.layout.addWidget(self.local_btn)

        self.layout.addWidget(QLabel("Remote Path (remote:path)"))
        self.layout.addWidget(self.remote_input)

        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Direction"))
        hlayout.addWidget(self.direction_combo)
        hlayout.addWidget(QLabel("Trigger"))
        hlayout.addWidget(self.trigger_type_combo)
        self.layout.addLayout(hlayout)

        self.layout.addWidget(QLabel("Scheduled Time (HH:MM)"))
        self.layout.addWidget(self.time_input)

        self.layout.addWidget(QLabel("Wi-Fi SSID"))
        self.layout.addWidget(self.wifi_input)

        self.layout.addWidget(add_btn)
        self.layout.addWidget(remove_btn)
        self.layout.addWidget(save_btn)
        self.layout.addWidget(manual_sync_btn)

        self.setLayout(self.layout)
        self.toggle_trigger_input()
        self.load_settings()

    def select_local(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Local Folder")
        if folder:
            self.local_input.setText(folder)

    def toggle_trigger_input(self):
        trigger_type = self.trigger_type_combo.currentText()
        self.time_input.setEnabled(trigger_type == "scheduled")
        self.wifi_input.setEnabled(trigger_type == "wifi")

    def add_task(self):
        local = self.local_input.text()
        remote = self.remote_input.text()
        direction = self.direction_combo.currentText()
        trigger_type = self.trigger_type_combo.currentText()

        if not local or not remote:
            QMessageBox.warning(self, "Incomplete Task", "Specify both local and remote paths.")
            return

        task_str = f"{direction.upper()}: {local} ↔ {remote} [{trigger_type}]"
        if trigger_type == "scheduled":
            task_str += f" at {self.time_input.time().toString('HH:mm')}"
        elif trigger_type == "wifi":
            ssid = self.wifi_input.text()
            if not ssid:
                QMessageBox.warning(self, "Wi-Fi SSID Missing", "Please specify the Wi-Fi SSID.")
                return
            task_str += f" on Wi-Fi '{ssid}'"

        self.task_list.addItem(task_str)
        self.local_input.clear()
        self.remote_input.clear()

    def remove_task(self):
        selected = self.task_list.currentRow()
        if selected >= 0:
            self.task_list.takeItem(selected)

    def save_settings(self):
        tasks = []
        for i in range(self.task_list.count()):
            item_text = self.task_list.item(i).text()
            parts = item_text.split(": ")
            direction = parts[0].lower()
            paths, trigger_info = parts[1].split(" [")
            local, remote = paths.split(" ↔ ")
            trigger_type = trigger_info.rstrip("]").split()[0]
            trigger = {"type": trigger_type}

            if trigger_type == "scheduled":
                time_str = trigger_info.split("at ")[1]
                trigger["time"] = time_str
            elif trigger_type == "wifi":
                ssid = trigger_info.split("'")[1]
                trigger["ssid"] = ssid

            tasks.append({
                "local_path": local,
                "remote_path": remote,
                "direction": direction,
                "trigger": trigger
            })

        with open(CONFIG_PATH, 'w') as f:
            json.dump({"tasks": tasks}, f, indent=4)

        QMessageBox.information(self, "Saved", "Configuration saved successfully!")

    def trigger_manual_sync(self):
        open(MANUAL_TRIGGER, 'w').close()
        QMessageBox.information(self, "Manual Sync", "Manual sync triggered successfully!")

    def load_settings(self):
        self.task_list.clear()
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                for task in config.get('tasks', []):
                    t = task['trigger']
                    task_str = f"{task['direction'].upper()}: {task['local_path']} ↔ {task['remote_path']} [{t['type']}]"
                    if t['type'] == "scheduled":
                        task_str += f" at {t['time']}"
                    elif t['type'] == "wifi":
                        task_str += f" on Wi-Fi '{t['ssid']}'"
                    self.task_list.addItem(task_str)
        except FileNotFoundError:
            pass

app = QApplication(sys.argv)
window = ConfigApp()
window.show()
app.exec()
