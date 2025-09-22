from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                            QPushButton)
from PyQt6.QtCore import pyqtSignal, Qt
import re

class LoginWindow(QWidget):
    login_success = pyqtSignal(int, str, str)  # user_id, username, name
    
    def __init__(self, comm):
        super().__init__()
        self.comm = comm
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Корпоративный мессенджер - Вход')
        self.setFixedSize(350, 250)
        
        layout = QVBoxLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Имя пользователя (логин)')
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton('Войти')
        self.login_button.clicked.connect(self.handle_login)
        
        self.register_button = QPushButton('Регистрация')
        self.register_button.clicked.connect(self.handle_register)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet('color: red; font-size: 10px;')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(35)

        self.instruction_label = QLabel("Для регистрации заполните поля и нажмите кнопку")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(QLabel('Логин:'))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel('Пароль:'))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.register_button)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            self.status_label.setText('Введите логин и пароль')
            return
            
        response = self.comm.send_message({
            'type': 'login',
            'username': username,
            'password': password
        })
        
        if response.get('status') == 'success':
            self.login_success.emit(response['user_id'], username, response.get('name', ''))
        else:
            self.status_label.setText(response.get('message', 'Ошибка входа'))
            
    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Проверки
        if not username or not password:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Введите логин и пароль")
            return

        # Проверка имени (латиница или кириллица, цифры, _ , длина 3-20)
        if not re.match(r'^[A-Za-zА-Яа-яЁё0-9_]{3,20}$', username):
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Логин может содержать буквы (вкл. кириллицу), цифры и _, длина 3–20")
            return

        # Проверка пароля
        if len(password) < 8:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Пароль должен быть не короче 8 символов")
            return
        if password.isalpha() or password.isdigit():
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Пароль должен содержать буквы и цифры")
            return
        if not re.search(r'[^A-Za-z0-9А-Яа-яЁё]', password):
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Пароль должен содержать хотя бы один спецсимвол (!@#$%^&*...)")
            return

        # Отправляем запрос на сервер
        response = self.comm.send_message({
            'type': 'register',
            'username': username,
            'password': password
        })

        if response.get('status') == 'success':
            self.status_label.setStyleSheet("color: green;")
            self.status_label.setText("Регистрация успешна. Теперь войдите.")
            self.username_input.clear()
            self.password_input.clear()
        else:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText(response.get('message', 'Ошибка регистрации'))
