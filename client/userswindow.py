from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem,
                            QMessageBox, QApplication)
from PyQt6.QtCore import Qt

class UsersWindow(QDialog):
    def __init__(self, comm, user_id):
        super().__init__()
        self.comm = comm
        self.user_id = user_id
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Список пользователей")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout()
        
        self.users_list = QListWidget()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_users)
        
        self.new_chat_button = QPushButton("Создать чат")
        self.new_chat_button.clicked.connect(self.create_chat_with_selected)
        
        layout.addWidget(self.users_list)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.new_chat_button)
        
        self.setLayout(layout)
        self.load_users()
        
    def load_users(self):
        try:
            # Явно запрашиваем обновление статусов
            response = self.comm.send_message({
                'type': 'get_users',
                'force_update': True  # Флаг для принудительного обновления
            })
            
            if not response:
                raise ValueError("Пустой ответ от сервера")
                
            if response.get('status') != 'success':
                raise ValueError(response.get('message', 'Неизвестная ошибка сервера'))
                
            self.users_list.clear()
            
            # Сортировка: онлайн -> по имени
            online_users = []
            offline_users = []
            
            for user in response['users']:
                if user['id'] == self.user_id:
                    continue
                    
                item_data = {
                    'id': user['id'],
                    'text': f"{'🟢' if user['online'] else '🔴'} {user.get('name', user['username'])} ({user['username']})",
                    'online': user['online']
                }
                
                if user['online']:
                    online_users.append(item_data)
                else:
                    offline_users.append(item_data)
            
            # Сортировка по алфавиту
            online_users.sort(key=lambda x: x['text'])
            offline_users.sort(key=lambda x: x['text'])
            
            # Добавляем в список
            for user in online_users + offline_users:
                item = QListWidgetItem(user['text'])
                item.setData(Qt.ItemDataRole.UserRole, user['id'])
                self.users_list.addItem(item)
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить пользователей: {str(e)}")
            print(f"Error loading users: {e}")
                
    def create_chat_with_selected(self):
        selected = self.users_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
        
        try:
            # Показываем индикатор загрузки
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            # Получаем ID выбранного пользователя
            user_id = selected.data(Qt.ItemDataRole.UserRole)
            
            # Отправляем запрос с таймаутом
            response = self.comm.send_message({
                'type': 'create_chat',
                'user_id': self.user_id,
                'participant_ids': [self.user_id, user_id],
                'is_group': False
            })
            
            if not response:
                raise ValueError("Не получен ответ от сервера")
            
            if response.get('status') == 'success':
                if response.get('existing'):
                    QMessageBox.information(self, "Успех", "Чат уже существует")
                else:
                    QMessageBox.information(self, "Успех", "Чат успешно создан")
                self.accept()
                # Обновляем список чатов
                if hasattr(self.parent(), 'load_chats'):
                    self.parent().load_chats()
            else:
                error_msg = response.get('message', 'Неизвестная ошибка')
                QMessageBox.critical(self, "Ошибка", f"Ошибка создания чата: {error_msg}")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка соединения",
                f"Не удалось создать чат: {str(e)}\n\nПопробуйте еще раз."
            )
        finally:
            QApplication.restoreOverrideCursor()
