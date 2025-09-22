from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QPushButton, QListWidget, QStackedWidget,QListWidgetItem,
                            QMessageBox, QDialog, QLineEdit, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from datetime import datetime
from .profilewidget import ProfileWidget
from .userswindow import UsersWindow
from .newchatdialog import NewChatDialog
from .chatparticipantswindow import ChatParticipantsWindow

class ChatWindow(QWidget):
    logout_requested = pyqtSignal()
  
    def __init__(self, comm, user_id, username, name):
        super().__init__()
        self.comm = comm
        self.user_id = user_id
        self.username = username
        self.name = name
        self.current_chat = None
        self.init_ui()
        self.load_chats()

        self.profile_widget.logout_requested.connect(self.logout)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_statuses)
        self.status_timer.start(10000)  # Обновление каждые 10 секунд

    def show_chat_participants(self):
        if not self.current_chat:
            QMessageBox.warning(self, "Ошибка", "Выберите чат сначала")
            return
            
        response = self.comm.send_message({
            'type': 'get_chat_participants',
            'chat_id': self.current_chat
        })
        
        if response.get('status') == 'success':
            participants_window = ChatParticipantsWindow(response['participants'], self)
            participants_window.exec()
        else:
            QMessageBox.warning(self, "Ошибка", response.get('message', 'Не удалось получить участников'))

    def closeEvent(self, event):
        self.comm.close_connection()
        event.accept()

    def init_ui(self):
        self.setWindowTitle(f'Корпоративный мессенджер - {self.name} ({self.username})')
        self.setMinimumSize(800, 600)
        
        main_layout = QHBoxLayout()
        
        # Левая панель
        sidebar = QVBoxLayout()
        
        self.chats_list = QListWidget()
        self.chats_list.itemClicked.connect(self.select_chat)
        
        self.users_button = QPushButton('Пользователи')
        self.users_button.clicked.connect(self.show_users)
        
        self.profile_button = QPushButton('Мой профиль')
        self.profile_button.clicked.connect(self.show_profile)
        
        self.new_chat_button = QPushButton('Создать групповой чат')
        self.new_chat_button.clicked.connect(self.create_new_chat)

        self.participants_button = QPushButton('Участники чата')
        self.participants_button.clicked.connect(self.show_chat_participants)
        sidebar.addWidget(self.participants_button)
        
        self.rename_button = QPushButton('Переименовать чат')
        self.rename_button.clicked.connect(self.show_rename_dialog)
        sidebar.addWidget(self.rename_button)
        self.rename_button.setVisible(False)  # Показывать только когда чат выбран

        sidebar.addWidget(QLabel('Чаты'))
        sidebar.addWidget(self.chats_list)
        sidebar.addWidget(self.users_button)
        sidebar.addWidget(self.profile_button)
        sidebar.addWidget(self.new_chat_button)
        
        # Правая панель - область чата
        self.chat_area = QVBoxLayout()
        
        # Виджет для отображения разных экранов (чат/профиль)
        self.content_stack = QStackedWidget()
        
        # Экран чата
        self.chat_screen = QWidget()
        chat_layout = QVBoxLayout()
        
        self.chat_header = QLabel('Выберите чат')
        self.chat_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText('Введите сообщение...')
        
        self.send_button = QPushButton('Отправить')
        self.send_button.clicked.connect(self.send_message)
        
        chat_layout.addWidget(self.chat_header)
        chat_layout.addWidget(self.messages_area)
        chat_layout.addWidget(self.message_input)
        chat_layout.addWidget(self.send_button)
        
        self.chat_screen.setLayout(chat_layout)
        self.content_stack.addWidget(self.chat_screen)
        
        # Экран профиля
        self.profile_widget = ProfileWidget(self.comm, self.user_id, self.username, self.name)
        self.profile_widget.update_success.connect(self.profile_updated)
        self.profile_widget.logout_requested.connect(self.logout)
        self.profile_widget.back_to_chat.connect(self.show_chat)
        self.content_stack.addWidget(self.profile_widget)
        
        self.chat_area.addWidget(self.content_stack)
        
        main_layout.addLayout(sidebar, 1)
        main_layout.addLayout(self.chat_area, 3)
        
        self.setLayout(main_layout)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_current_chat)
        self.update_timer.start(3000)  # Обновление каждые 3 секунды
    
    def update_current_chat(self):
        if self.current_chat:
            self.load_messages(self.current_chat)

    def show_chat(self):
        """Возвращает пользователя в окно чата"""
        self.content_stack.setCurrentIndex(0)  # 0 - индекс виджета чата

    def load_chats(self):
        response = self.comm.send_message({
            'type': 'get_chats',
            'user_id': self.user_id,
            'username': self.username
        })
        
        if response.get('status') == 'success':
            self.chats_list.clear()
            for chat in response['chats']:
                item = QListWidgetItem(chat['name'])
                item.setData(Qt.ItemDataRole.UserRole, chat['id'])
                self.chats_list.addItem(item)
                
    def select_chat(self, item):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_chat = chat_id
        self.chat_header.setText(f"Чат: {item.text()}")
        self.content_stack.setCurrentIndex(0)  # Переключаемся на экран чата
        self.load_messages(chat_id)
        
        # 👇 проверяем групповой ли чат
        chats = self.comm.send_message({
            'type': 'get_chats',
            'user_id': self.user_id,
            'username': self.username
        })

        if chats.get('status') == 'success':
            current = next((c for c in chats['chats'] if c['id'] == chat_id), None)
            if current and current.get('is_group', False):
                self.rename_button.setVisible(True)
                self.participants_button.setVisible(True)
            else:
                self.rename_button.setVisible(False)
                self.participants_button.setVisible(False)
        
    def load_messages(self, chat_id):
        response = self.comm.send_message({
            'type': 'get_messages',
            'chat_id': chat_id
        })
        
        if response.get('status') == 'success':
            self.messages_area.clear()
            
            html_output = """<html><head><style>
                .message-block { 
                    margin: 8px 0;
                    display: flex;
                    flex-direction: column;
                }
                .my-message-block {
                    justify-content: flex-end;
                }
                .other-message-block {
                    justify-content: flex-start;
                }
                .message-container {
                    display: inline-block;
                    max-width: 30%;
                    margin: 2px 0;
                }
                .my-message, .other-message {
                    border-radius: 15px;
                    padding: 8px 12px;
                    word-wrap: break-word;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }
                .my-message {
                    background-color: rgba(173, 216, 230, 0.5);
                    border: 1px solid rgba(100, 180, 200, 0.3);
                    margin-left: 20%;
                    text-align: right;
                    color: black;
                }
                .other-message {
                    background-color: rgba(245, 245, 245, 0.5);
                    border: 1px solid rgba(200, 200, 200, 0.3);
                    margin-right: 20%;
                    text-align: left;
                    color: black;
                }
                .system-message {
                    color: gray;
                    font-style: italic;
                    text-align: center;
                    margin: 15px 0;
                    font-size: 11px;
                    padding: 5px;
                }
                .timestamp {
                    font-size: 10px;
                    color: #777;
                    margin: 2px 8px 0 8px;
                    padding: 0;
                    background-color: transparent;
                }
                .timestamp-right {
                    text-align: right;
                }
                .timestamp-left {
                    text-align: left;
                }
                .username {
                    font-size: 11px;
                    font-weight: bold;
                    margin: 0 8px 2px 8px;
                    color: #9e9e9e;
                    background-color: transparent;
                }
            </style></head><body>
            """

            for msg in response['messages']:
                timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%d.%m.%Y %H:%M')
                text = msg['text'].replace('<', '&lt;').replace('>', '&gt;')  # защита от HTML
                username = msg.get('username', '???')
                is_system = msg.get('is_system', False)
                is_mine = msg.get('user_id') == self.user_id

                if is_system:
                    html_output += f"""
                        <div class="system-message">[{timestamp}] {text}</div>
                    """
                elif is_mine:
                    html_output += f"""
                        <div class="message-block my-message-block">
                            <div class="message-container">
                                <div class="my-message">{text}</div>
                                <div class="timestamp timestamp-right">{timestamp}</div>
                            </div>
                        </div>
                    """
                else:
                    html_output += f"""
                        <div class="message-block other-message-block">
                            <div class="message-container">
                                <span class="username">{username}</span>
                                <div class="other-message">{text}</div>
                                <div class="timestamp timestamp-left">{timestamp}</div>
                            </div>
                        </div>
                    """

            html_output += "</body></html>"

            self.messages_area.setHtml(html_output)

            # Автопрокрутка вниз
            self.messages_area.verticalScrollBar().setValue(
                self.messages_area.verticalScrollBar().maximum())
   
    def send_message(self):
        if not self.current_chat:
            QMessageBox.warning(self, 'Ошибка', 'Выберите чат сначала')
            return
            
        text = self.message_input.toPlainText().strip()
        if not text:
            return
            
        response = self.comm.send_message({
            'type': 'send_message',
            'user_id': self.user_id,
            'chat_id': self.current_chat,
            'text': text
        })
        
        if response.get('status') == 'success':
            self.message_input.clear()
            self.load_messages(self.current_chat)
            
    def show_users(self):
        users_window = UsersWindow(self.comm, self.user_id)
        users_window.exec()
        self.load_chats()  # Обновляем список чатов после возможного создания нового
        
    def show_profile(self):
        # Обновляем данные перед показом профиля
        self.profile_widget.name = self.name
        self.profile_widget.username = self.username
        self.profile_widget.name_label.setText(f"Имя: {self.name}")
        self.profile_widget.username_label.setText(f"Логин: {self.username}")
        self.content_stack.setCurrentIndex(1)  # Переключаемся на экран профиля
        
    def create_new_chat(self):
        new_chat_dialog = NewChatDialog(self.comm, self.user_id)
        if new_chat_dialog.exec():
            self.load_chats()  # Обновляем список чатов после создания

    def show_rename_dialog(self):
        if not self.current_chat:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Изменение названия чата")
        layout = QVBoxLayout()
        
        label = QLabel("Новое название:")
        name_input = QLineEdit()
        name_input.setPlaceholderText("Введите новое название")
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.rename_chat(name_input.text(), dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(label)
        layout.addWidget(name_input)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def rename_chat(self, new_name, dialog):
        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return
            
        try:
            response = self.comm.send_message({
                'type': 'update_chat_name',
                'chat_id': self.current_chat,
                'new_name': new_name,
                'user_id': self.user_id
            })
            
            if not response:  # Если ответ пустой (разрыв соединения)
                raise ConnectionError("No response from server")
                
            if response.get('status') == 'success':
                dialog.accept()
                self.load_chats()  # Обновляем список чатов
                self.chat_header.setText(f"Чат: {new_name}")
                self.load_messages(self.current_chat)  # Обновляем сообщения
            else:
                QMessageBox.warning(self, "Ошибка", response.get('message', 'Ошибка'))
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка соединения", 
                f"Не удалось изменить название чата: {str(e)}\n\nПопробуйте переподключиться.")
            self.comm.close_connection()

    def update_statuses(self):  
        if self.current_chat:
            self.load_messages(self.current_chat)

    def profile_updated(self):
        # Обновляем данные после изменения профиля
        response = self.comm.send_message({
            'type': 'get_user_info',  # Убедитесь, что сервер поддерживает этот тип запроса
            'user_id': self.user_id
        })
        
        if response.get('status') == 'success':
            self.username = response.get('username', self.username)
            self.name = response.get('name', self.name)
            self.setWindowTitle(f'Корпоративный мессенджер - {self.name} ({self.username})')
            self.profile_widget.username = self.username
            self.profile_widget.name = self.name
            self.profile_widget.name_label.setText(f"Имя: {self.name}")
            self.profile_widget.username_label.setText(f"Логин: {self.username}")

    def logout(self):
        # Просто передаем сигнал выше
        self.logout_requested.emit()
