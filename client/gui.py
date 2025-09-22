from PyQt6.QtWidgets import QMessageBox
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from client.mainwindow import MainWindow
from client.communication import ClientCommunication
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='messenger.log'
)
logger = logging.getLogger(__name__)

# Установка пути к Qt плагинам втлытлвытловы
qt_plugin_path = Path(__file__).resolve().parent.parent / 'venv' / 'Lib' / 'site-packages' / 'PyQt6' / 'Qt6' / 'plugins'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(qt_plugin_path)

class MessengerApp:
    def __init__(self):
        self.app = QApplication([])
        self.host = 'localhost'
        self.port = 5555
        
        # Инициализация соединения
        self.comm = ClientCommunication(self.host, self.port)
        if not self.comm.connect_to_server():
            QMessageBox.critical(None, 'Ошибка', 'Не удалось подключиться к серверу')
            return
            
        self.main_window = MainWindow(self.comm)
        self.main_window.show()
        
    def run(self):
        self.app.exec()
        self.comm.close_connection()


if __name__ == "__main__":
    # Проверка пути к плагинам
    if not qt_plugin_path.exists():
        print(f"ОШИБКА: Qt плагины не найдены по пути {qt_plugin_path}")
        print("Установите PyQt6 правильно: pip install PyQt6")
        sys.exit(1)
    
    messenger = MessengerApp()
    messenger.app.setProperty('messenger_app', messenger)  # Добавляем это
    messenger.run()