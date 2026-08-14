import os
import shutil
import time
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

def get_all_file_sizes(folder_path):
    sizes = {}
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                sizes[fp] = os.path.getsize(fp)
    return sizes

class BackupWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, source_dir, dest_dir, max_backups=5):
        super().__init__()
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.max_backups = max_backups
        self.is_running = True

    def enforce_backup_limit(self, backup_dir):
        if not os.path.exists(backup_dir):
            return
        backups = [os.path.join(backup_dir, d) for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))]
        backups.sort(key=os.path.getctime)
        while len(backups) > self.max_backups:
            oldest_backup = backups.pop(0)
            shutil.rmtree(oldest_backup)
            self.log_signal.emit(f"🗑️ Storage Safe: Purana backup delete hua ({os.path.basename(oldest_backup)})")

    def run(self):
        self.log_signal.emit("🚀 Backup Engine Starting (Smart File-Level Scan)...")
        loop_count = 0
        last_valid_sizes = {}

        if os.path.exists(self.source_dir):
            last_valid_sizes = get_all_file_sizes(self.source_dir)
            total_size_kb = sum(last_valid_sizes.values()) / 1024
            self.log_signal.emit(f"📊 Total Save Size: {total_size_kb:.2f} KB | Files tracked: {len(last_valid_sizes)}")
        else:
            self.log_signal.emit("❌ Error: Source Save Folder nahi mila!")
            return

        min_1_dir = os.path.join(self.dest_dir, "1_Min_Backups")
        min_5_dir = os.path.join(self.dest_dir, "5_Min_Backups")
        os.makedirs(min_1_dir, exist_ok=True)
        os.makedirs(min_5_dir, exist_ok=True)

        while self.is_running:
            current_sizes = get_all_file_sizes(self.source_dir)
            corruption_detected = False
            corrupted_file_name = ""

            
            if len(current_sizes) == 0:
                self.log_signal.emit("⚠️ DANGER: Game save folder poori tarah khali (Empty) hai!")
                self.log_signal.emit("🛑 Backup loop PAUSED. Khali folder ka backup nahi liya jayega.")
                break 

            
            for fp, prev_size in last_valid_sizes.items():
                if fp not in current_sizes:
                    corruption_detected = True
                    corrupted_file_name = f"{os.path.basename(fp)} [GAYAB/DELETED]"
                    break
                else:
                    current_size = current_sizes[fp]
                    if prev_size > 100 and current_size < (prev_size * 0.5): 
                        corruption_detected = True
                        corrupted_file_name = f"{os.path.basename(fp)} [SIZE DROPPED]"
                        break

            if corruption_detected:
                self.log_signal.emit(f"⚠️ DANGER: '{corrupted_file_name}' detect hui!")
                self.log_signal.emit("🛑 Backup loop PAUSED. Corrupt ya missing file ka backup nahi liya gaya.")
                break 

            
            last_valid_sizes = current_sizes
            timestamp = datetime.now().strftime("%d-%m-%Y %H.%M")

            
            min_1_path = os.path.join(min_1_dir, f"Backup_{timestamp}")
            shutil.copytree(self.source_dir, min_1_path)
            self.log_signal.emit(f"✅ 1-Min Backup Saved: [{timestamp}]")
            self.enforce_backup_limit(min_1_dir)

            loop_count += 1

            
            if loop_count == 5:
                min_5_path = os.path.join(min_5_dir, f"Backup_{timestamp}")
                shutil.copytree(self.source_dir, min_5_path)
                self.log_signal.emit(f"🌟 5-Min Major Backup Saved: [{timestamp}]")
                self.enforce_backup_limit(min_5_dir)
                loop_count = 0

            
            for _ in range(60):
                if not self.is_running:
                    break
                time.sleep(1)
        self.log_signal.emit("🛑 Auto-Backup Stopped.")

    def stop(self):
        self.is_running = False