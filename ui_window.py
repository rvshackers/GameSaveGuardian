import os
import sys
import shutil
import json
import requests
import webbrowser
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, 
                             QFileDialog, QMessageBox, QGroupBox, QComboBox)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal
from backup_core import BackupWorker

CONFIG_FILE = "settings.json"
CURRENT_VERSION = "1.0"  # Hamara current V1 version
UPDATE_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/GameSaveGuardian/main/version.json" # Placeholder
def get_asset_path(filename):
    """Yeh check karega ki hum .exe chala rahe hain ya normal python script"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller .exe ke andar ka hidden path
        return os.path.join(sys._MEIPASS, 'assets', filename)
    # Normal VS Code wala path
    return os.path.join('assets', filename)
# --- NAYA: Update Check Karne Wala Background Worker ---
class UpdateChecker(QThread):
    update_found = pyqtSignal(str, str) # version, youtube_url

    def run(self):
        try:
            # Internet se check karega (Timeout 5 second rakha hai taaki app slow na ho)
            response = requests.get(UPDATE_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                online_version = data.get("latest_version", "1.0")
                video_url = data.get("video_url", "")
                
                # Agar online version hamare 1.0 se bada hai, toh signal bhejo!
                if float(online_version) > float(CURRENT_VERSION):
                    self.update_found.emit(online_version, video_url)
        except Exception:
            pass # Agar net nahi chal raha, toh chupchaap ignore kar do (no crash)

# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"GameSave Guardian v{CURRENT_VERSION}")
        self.setWindowIcon(QIcon(get_asset_path("logo.ico")))
        self.resize(650, 600)
        self.worker = None


        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QGroupBox { color: #00FF66; font-weight: bold; border: 1px solid #333; margin-top: 10px; padding: 10px; }
            QLabel { color: #E0E0E0; font-size: 13px; }
            QLineEdit { background-color: #1E1E1E; color: #FFF; border: 1px solid #444; padding: 6px; border-radius: 4px; }
            QPushButton { background-color: #2A2A2A; color: #FFF; border: 1px solid #555; padding: 8px 15px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #3A3A3A; border-color: #00FF66; }
            QTextEdit { background-color: #0A0A0A; color: #00FF66; font-family: Consolas, Monospace; border: 1px solid #222; }
            QComboBox { background-color: #1E1E1E; color: #FFF; border: 1px solid #444; padding: 5px; }
        """)

        self.init_ui()
        self.load_config()
        
        # App open hote hi Update check karna shuru karega (Background mein)
        self.updater = UpdateChecker()
        self.updater.update_found.connect(self.show_update_popup)
        self.updater.start()

    def init_ui(self):
        main_layout = QVBoxLayout()

        config_box = QGroupBox("Directory Configuration")
        config_layout = QVBoxLayout()
        src_layout = QHBoxLayout()
        self.src_input = QLineEdit()
        src_btn = QPushButton("Browse")
        src_btn.clicked.connect(self.browse_source)
        src_layout.addWidget(QLabel("Game Save Path:"))
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(src_btn)

        dest_layout = QHBoxLayout()
        self.dest_input = QLineEdit()
        dest_btn = QPushButton("Browse")
        dest_btn.clicked.connect(self.browse_dest)
        dest_layout.addWidget(QLabel("Backup Location:"))
        dest_layout.addWidget(self.dest_input)
        dest_layout.addWidget(dest_btn)

        config_layout.addLayout(src_layout)
        config_layout.addLayout(dest_layout)
        config_box.setLayout(config_layout)

        restore_box = QGroupBox("One-Click Restore System")
        restore_layout = QHBoxLayout()
        self.backup_combo = QComboBox()
        self.backup_combo.setMinimumWidth(250)
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.clicked.connect(self.refresh_backups)
        restore_btn = QPushButton("⏪ RESTORE SAVE")
        restore_btn.setStyleSheet("background-color: #D2691E; color: white;")
        restore_btn.clicked.connect(self.restore_backup)
        restore_layout.addWidget(self.backup_combo)
        restore_layout.addWidget(refresh_btn)
        restore_layout.addWidget(restore_btn)
        restore_box.setLayout(restore_layout)

        control_box = QGroupBox("System Controls")
        control_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("▶ START AUTO-BACKUP")
        self.toggle_btn.setStyleSheet("background-color: #008C45; color: white; font-size: 14px;")
        self.toggle_btn.clicked.connect(self.toggle_backup)
        control_layout.addWidget(self.toggle_btn)
        control_box.setLayout(control_layout)

        log_box = QGroupBox("Live Console Log")
        log_layout = QVBoxLayout()
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        log_layout.addWidget(self.log_console)
        log_box.setLayout(log_layout)

        main_layout.addWidget(config_box)
        main_layout.addWidget(restore_box)
        main_layout.addWidget(control_box)
        main_layout.addWidget(log_box)

# RVS HACKERS BRANDING FOOTER
        brand_label = QLabel("<center><span style='color: #888888; font-size: 11px;'>Designed & Developed by <b style='color: #00FF66;'>RVS Hackers</b></span></center>")
        main_layout.addWidget(brand_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # --- NAYA: Update Popup Function ---
    def show_update_popup(self, version, url):
        reply = QMessageBox.question(self, "🎉 New Update Available!", 
                                     f"GameSave Guardian ka naya Version {version} aa gaya hai!\n\nKya aap YouTube par nayi features ki video dekhna aur update karna chahte hain?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                     
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(url) # Yeh seedha user ka browser khol kar YouTube video chala dega!

    # --- Config Logic ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.src_input.setText(data.get("src", ""))
                    self.dest_input.setText(data.get("dest", ""))
                    if data.get("dest", ""):
                        self.refresh_backups()
            except Exception:
                pass

    def save_config(self):
        data = {
            "src": self.src_input.text().strip(),
            "dest": self.dest_input.text().strip()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

    def reset_ui_state(self):
        self.toggle_btn.setText("▶ START AUTO-BACKUP")
        self.toggle_btn.setStyleSheet("background-color: #008C45; color: white; font-size: 14px;")
        self.src_input.setEnabled(True)
        self.dest_input.setEnabled(True)

    # --- Actions ---
    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Game Save Folder")
        if folder:
            self.src_input.setText(folder)
            self.save_config()

    def browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            self.dest_input.setText(folder)
            self.save_config()
            self.refresh_backups()

    def log(self, message):
        self.log_console.append(message)

    def toggle_backup(self):
        if self.worker is None or not self.worker.isRunning():
            src = self.src_input.text().strip()
            dest = self.dest_input.text().strip()

            if not src or not dest:
                QMessageBox.warning(self, "Input Error", "Kripya dono Source aur Destination paths select karein!")
                return
            
            self.save_config() 
            self.worker = BackupWorker(src, dest)
            self.worker.log_signal.connect(self.log)
            self.worker.finished.connect(self.reset_ui_state) 
            self.worker.start()

            self.toggle_btn.setText("⏹ STOP AUTO-BACKUP")
            self.toggle_btn.setStyleSheet("background-color: #B22222; color: white; font-size: 14px;")
            self.src_input.setEnabled(False)
            self.dest_input.setEnabled(False)
        else:
            self.worker.stop()
            self.reset_ui_state()

    def refresh_backups(self):
        dest = self.dest_input.text().strip()
        self.backup_combo.clear()
        if not dest or not os.path.exists(dest): return
        min_1_dir = os.path.join(dest, "1_Min_Backups")
        min_5_dir = os.path.join(dest, "5_Min_Backups")

        if os.path.exists(min_1_dir):
            for d in sorted(os.listdir(min_1_dir), reverse=True): 
                self.backup_combo.addItem(f"[1-Min] {d.replace('Backup_', '')}", os.path.join(min_1_dir, d))
                
        if os.path.exists(min_5_dir):
            for d in sorted(os.listdir(min_5_dir), reverse=True):
                self.backup_combo.addItem(f"[5-Min] {d.replace('Backup_', '')}", os.path.join(min_5_dir, d))
        self.log("🔄 Backup list refreshed.")

    def restore_backup(self):
        src = self.src_input.text().strip()
        selected_backup = self.backup_combo.currentData()

        if not src or not selected_backup:
            QMessageBox.warning(self, "Error", "Path ya backup select nahi hai!")
            return

        reply = QMessageBox.question(self, "Confirm Restore", 
                                     f"WARNING: Kya aap current save ko replace karna chahte hain?\n\nBackup: {os.path.basename(selected_backup)}", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                     
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.worker and self.worker.isRunning():
                    self.toggle_backup()
                shutil.copytree(selected_backup, src, dirs_exist_ok=True)
                self.log(f"🎉 RESTORE SUCCESSFUL: {os.path.basename(selected_backup)}")
                QMessageBox.information(self, "Success", "Save file successfully restore ho chuki hai!")
            except Exception as e:
                self.log(f"❌ Restore Failed: {str(e)}")