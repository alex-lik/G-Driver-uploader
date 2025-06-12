import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QVBoxLayout,
                             QWidget)

from db import init_db
from sync import SyncWorker

CONFIG_FILE = "sync_settings.json"

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def add_to_startup(exe_path=None, app_name="GDriveSync"):
    try:
        import os
        import sys
        if exe_path is None:
            exe_path = sys.executable
        startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        shortcut_path = os.path.join(startup_dir, f"{app_name}.lnk")
        # Только для exe, иначе не сработает
        if not exe_path.lower().endswith(".exe"):
            return False
        import pythoncom  # pip install pywin32
        from win32com.client import Dispatch
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        return True
    except Exception as e:
        return False

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GDrive Folder Uploader")
        self.setWindowIcon(QIcon("icon.ico"))  # твоя иконка

        self.layout = QVBoxLayout()

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.folder_label = QLabel("Папка для синхронизации:")
        self.folder_path = QLineEdit()
        self.folder_btn = QPushButton("Выбрать папку")

        self.sa_label = QLabel("Файл сервисного аккаунта:")
        self.sa_path = QLineEdit()
        self.sa_btn = QPushButton("Выбрать JSON")

        self.gd_label = QLabel("Google Drive FOLDER_ID:")
        self.gd_id = QLineEdit()

        # --- Новое: Telegram token/chat_id
        self.tg_token_label = QLabel("Telegram Bot Token (необязательно):")
        self.tg_token = QLineEdit()
        self.tg_chat_label = QLabel("Telegram Chat ID (необязательно):")
        self.tg_chat = QLineEdit()

        self.save_btn = QPushButton("Сохранить настройки и запустить")
        self.autorun_btn = QPushButton("Добавить в автозагрузку")
        self.worker = None

        self.layout.addWidget(self.folder_label)
        hl1 = QHBoxLayout()
        hl1.addWidget(self.folder_path)
        hl1.addWidget(self.folder_btn)
        self.layout.addLayout(hl1)

        self.layout.addWidget(self.sa_label)
        hl2 = QHBoxLayout()
        hl2.addWidget(self.sa_path)
        hl2.addWidget(self.sa_btn)
        self.layout.addLayout(hl2)

        self.layout.addWidget(self.gd_label)
        self.layout.addWidget(self.gd_id)

        # Telegram token/chat_id
        self.layout.addWidget(self.tg_token_label)
        self.layout.addWidget(self.tg_token)
        self.layout.addWidget(self.tg_chat_label)
        self.layout.addWidget(self.tg_chat)

        self.layout.addWidget(self.save_btn)
        self.layout.addWidget(self.autorun_btn)
        self.layout.addWidget(QLabel("Лог:"))
        self.layout.addWidget(self.log)
        self.setLayout(self.layout)

        self.folder_btn.clicked.connect(self.select_folder)
        self.sa_btn.clicked.connect(self.select_json)
        self.save_btn.clicked.connect(self.save_and_start)
        self.autorun_btn.clicked.connect(self.add_to_autorun)

        # Восстановление настроек
        cfg = load_config()
        if cfg:
            self.folder_path.setText(cfg.get("folder", ""))
            self.sa_path.setText(cfg.get("sa_file", ""))
            self.gd_id.setText(cfg.get("gd_id", ""))
            self.tg_token.setText(cfg.get("tg_token", ""))
            self.tg_chat.setText(cfg.get("tg_chat_id", ""))

            # Если все данные есть — автозапуск синхронизации
            if all([cfg.get("folder"), cfg.get("sa_file"), cfg.get("gd_id")]):
                self.save_and_start()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if folder:
            self.folder_path.setText(folder)

    def select_json(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выбрать service-account.json", "", "JSON Files (*.json)")
        if file:
            self.sa_path.setText(file)

    def save_and_start(self):
        folder = self.folder_path.text()
        sa_file = self.sa_path.text()
        gd_id = self.gd_id.text()
        tg_token = self.tg_token.text().strip()
        tg_chat = self.tg_chat.text().strip()
        save_config({
            "folder": folder,
            "sa_file": sa_file,
            "gd_id": gd_id,
            "tg_token": tg_token,
            "tg_chat_id": tg_chat
        })
        try:
            credentials = service_account.Credentials.from_service_account_file(
                sa_file, scopes=['https://www.googleapis.com/auth/drive.file'])
            service = build('drive', 'v3', credentials=credentials)
        except Exception as e:
            self.log.append(f"Ошибка авторизации: {e}")
            return
        self.worker = SyncWorker(
            folder, service, gd_id,
            tg_token=tg_token if tg_token else None,
            tg_chat_id=tg_chat if tg_chat else None
        )
        self.worker.log.connect(self.log.append)
        self.worker.start()
        self.log.append("Синхронизация запущена!")

    def add_to_autorun(self):
        success = add_to_startup()
        if success:
            self.log.append("Программа добавлена в автозагрузку Windows!")
        else:
            self.log.append("Ошибка добавления в автозагрузку (возможно, не exe-файл или не установлены pywin32)")

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    window.show()
    sys.exit(app.exec_())
