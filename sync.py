import os

from googleapiclient.http import MediaFileUpload
from PyQt5.QtCore import QThread, pyqtSignal
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from db import add_file, get_file, remove_file
from logger_setup import logger
from notify import send_telegram_message


class SyncHandler(FileSystemEventHandler):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker

    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"Обнаружен новый файл: {event.src_path}")
            self.worker.log.emit(f"Обнаружен новый файл: {event.src_path}")
            self.worker.sync_file(event.src_path, is_new=True)

    def on_modified(self, event):
        if not event.is_directory:
            self.worker.sync_file(event.src_path, is_new=False)

    def on_deleted(self, event):
        if not event.is_directory:
            self.worker.delete_file(event.src_path)

class SyncWorker(QThread):
    log = pyqtSignal(str)

    def __init__(self, folder, service, folder_id, tg_token=None, tg_chat_id=None):
        super().__init__()
        self.folder = folder
        self.service = service
        self.folder_id = folder_id
        self.tg_token = tg_token
        self.tg_chat_id = tg_chat_id
        self.running = True

    def run(self):
        logger.info("Стартовый скан папки...")
        self.log.emit("Стартовый скан папки...")
        for root, _, files in os.walk(self.folder):
            for fname in files:
                fpath = os.path.join(root, fname)
                self.sync_file(fpath, is_new=False)
        logger.info("Мониторинг изменений запущен.")
        self.log.emit("Мониторинг изменений запущен.")
        observer = Observer()
        handler = SyncHandler(self)
        observer.schedule(handler, self.folder, recursive=True)
        observer.start()
        while self.running:
            self.msleep(500)
        observer.stop()
        observer.join()

    def sync_file(self, fpath, is_new=False):
        try:
            if not os.path.exists(fpath):
                return
            fname = os.path.basename(fpath)
            stat = os.stat(fpath)
            row = get_file(fpath)
            if row and row[1] == stat.st_mtime:
                return  # уже загружено и не менялось
            if row:
                try:
                    self.service.files().delete(fileId=row[0]).execute()
                except Exception:
                    pass
            media = MediaFileUpload(fpath, resumable=True)
            metadata = {"name": fname, "parents": [self.folder_id]}
            uploaded = self.service.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()
            add_file(fpath, uploaded["id"], stat.st_mtime)
            logger.info(f"Загружен: {fname}")
            self.log.emit(f"Загружен: {fname}")
        except Exception as e:
            msg = f"Ошибка загрузки {fpath}: {e}"
            logger.error(msg)
            self.log.emit(msg)
            if self.tg_token and self.tg_chat_id:
                send_telegram_message(self.tg_token, self.tg_chat_id, msg)

    def delete_file(self, fpath):
        try:
            row = get_file(fpath)
            if row:
                self.service.files().delete(fileId=row[0]).execute()
                remove_file(fpath)
                logger.info(f"Удалён: {os.path.basename(fpath)}")
                self.log.emit(f"Удалён: {os.path.basename(fpath)}")
        except Exception as e:
            msg = f"Ошибка удаления {fpath}: {e}"
            logger.error(msg)
            self.log.emit(msg)
            if self.tg_token and self.tg_chat_id:
                send_telegram_message(self.tg_token, self.tg_chat_id, msg)
            if self.tg_token and self.tg_chat_id:
                send_telegram_message(self.tg_token, self.tg_chat_id, msg)
