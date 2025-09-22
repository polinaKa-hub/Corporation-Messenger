from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QDialog, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt

class ProfileWidget(QWidget):
    update_success = pyqtSignal()
    logout_requested = pyqtSignal()
    back_to_chat = pyqtSignal()

    def __init__(self, comm, user_id, username, name):
        super().__init__()
        self.comm = comm
        self.user_id = user_id
        self.username = username
        self.name = name
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Информация о пользователе
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title = QLabel("Профиль пользователя")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        info_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.name_label = QLabel(f"Имя: {self.name}")
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.username_label = QLabel(f"Логин: {self.username}")
        self.username_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.username_label)
        
        # Кнопки действий
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(5)
        
        self.edit_name_btn = QPushButton('Изменить имя')
        self.edit_name_btn.clicked.connect(self.edit_name)
        
        self.edit_username_btn = QPushButton('Изменить логин')
        self.edit_username_btn.clicked.connect(self.edit_username)
        
        self.edit_password_btn = QPushButton('Изменить пароль')
        self.edit_password_btn.clicked.connect(self.edit_password)
        
        self.logout_btn = QPushButton('Выйти из аккаунта')
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        self.logout_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        
        buttons_layout.addWidget(self.edit_name_btn)
        buttons_layout.addWidget(self.edit_username_btn)
        buttons_layout.addWidget(self.edit_password_btn)
        buttons_layout.addWidget(self.logout_btn)
        
        layout.addLayout(info_layout)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        self.setLayout(layout)

    def edit_name(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Изменение имени")
        dialog.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        label = QLabel("Введите новое имя:")
        self.name_input = QLineEdit()
        self.name_input.setText(self.name)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self.save_name(dialog))
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addWidget(label)
        layout.addWidget(self.name_input)
        layout.addLayout(buttons)
        
        dialog.setLayout(layout)
        dialog.exec()

    def save_name(self, dialog):
        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Введите новое имя")
            return
            
        response = self.comm.send_message({
            'type': 'update_profile',
            'user_id': self.user_id,
            'new_name': new_name
        })
        
        if response.get('status') == 'success':
            self.name = response.get('new_name', new_name)
            self.name_label.setText(f"Имя: {self.name}")
            self.update_success.emit()
            dialog.accept()
            QMessageBox.information(self, "Успех", "Имя успешно изменено")
        else:
            QMessageBox.warning(self, "Ошибка", response.get('message', 'Не удалось изменить имя'))

    def edit_username(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Изменение логина")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        label1 = QLabel("Введите новый логин:")
        self.username_input = QLineEdit()
        self.username_input.setText(self.username)
        
        label2 = QLabel("Введите текущий пароль:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self.save_username(dialog))
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addWidget(label1)
        layout.addWidget(self.username_input)
        layout.addWidget(label2)
        layout.addWidget(self.password_input)
        layout.addLayout(buttons)
        
        dialog.setLayout(layout)
        dialog.exec()

    def save_username(self, dialog):
        new_username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not new_username:
            QMessageBox.warning(self, "Ошибка", "Введите новый логин")
            return
        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите пароль")
            return
            
        response = self.comm.send_message({
            'type': 'update_profile',
            'user_id': self.user_id,
            'new_username': new_username,
            'password': password
        })
        
        if response.get('status') == 'success':
            self.username = response.get('new_username', new_username)
            self.username_label.setText(f"Логин: {self.username}")
            self.update_success.emit()
            dialog.accept()
            QMessageBox.information(self, "Успех", "Логин успешно изменен")
        else:
            QMessageBox.warning(self, "Ошибка", response.get('message', 'Не удалось изменить логин'))

    def edit_password(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Изменение пароля")
        dialog.setFixedSize(300, 250)
        
        layout = QVBoxLayout()
        
        label1 = QLabel("Введите текущий пароль:")
        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        label2 = QLabel("Введите новый пароль:")
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        label3 = QLabel("Повторите новый пароль:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self.save_password(dialog))
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addWidget(label1)
        layout.addWidget(self.old_password_input)
        layout.addWidget(label2)
        layout.addWidget(self.new_password_input)
        layout.addWidget(label3)
        layout.addWidget(self.confirm_password_input)
        layout.addLayout(buttons)
        
        dialog.setLayout(layout)
        dialog.exec()

    def save_password(self, dialog):
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not old_password or not new_password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if new_password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
            
        response = self.comm.send_message({
            'type': 'update_profile',
            'user_id': self.user_id,
            'old_password': old_password,
            'new_password': new_password
        })
        
        if response.get('status') == 'success':
            dialog.accept()
            QMessageBox.information(self, "Успех", "Пароль успешно изменен")
        else:
            QMessageBox.warning(self, "Ошибка", response.get('message', 'Не удалось изменить пароль'))
