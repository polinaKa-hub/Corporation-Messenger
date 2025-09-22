from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from .loginwindow import LoginWindow
from .chatwindow import ChatWindow
from .communication import ClientCommunication

class MainWindow(QMainWindow):
    def __init__(self, comm):
        super().__init__()
        self.comm = comm
        self.user_id = None
        self.username = None
        self.name = None
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Инициализируем как None, чтобы отслеживать состояние
        self.login_window = None
        self.chat_window = None
        
        self.show_login_window()
        
    def show_login_window(self):
        # Очищаем stacked_widget
        while self.stacked_widget.count():
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Создаём новое окно входа
        self.login_window = LoginWindow(self.comm)
        self.login_window.login_success.connect(self.handle_login_success)
        self.stacked_widget.addWidget(self.login_window)
        self.setWindowTitle('Корпоративный мессенджер - Вход')
        
        # Сбрасываем ссылку на chat_window, так как он удалён
        self.chat_window = None
        
    def handle_login_success(self, user_id, username, name):
        self.user_id = user_id
        self.username = username
        self.name = name
        
        # Удаляем старый chat_window только если он существует
        if self.chat_window is not None:
            self.stacked_widget.removeWidget(self.chat_window)
            self.chat_window.deleteLater()
            self.chat_window = None
            
        # Создаём новое окно чата
        self.chat_window = ChatWindow(self.comm, user_id, username, name)
        self.chat_window.logout_requested.connect(self.logout)
        self.stacked_widget.addWidget(self.chat_window)
        self.stacked_widget.setCurrentIndex(1)
        
        self.setWindowTitle(f'Корпоративный мессенджер - {name} ({username})')
        
    def logout(self):
        # Очищаем данные пользователя
        self.user_id = None
        self.username = None
        self.name = None
        
        # Закрываем соединение и создаём новое
        self.comm.close_connection()
        self.comm = ClientCommunication(self.comm.host, self.comm.port)
        if not self.comm.connect_to_server():
            QMessageBox.critical(self, 'Ошибка', 'Не удалось подключиться к серверу')
        
        # Показываем окно входа
        self.show_login_window()
