from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem,
                            QLineEdit, QLabel, QHBoxLayout, QMessageBox, QApplication)
from PyQt6.QtCore import Qt

class NewChatDialog(QDialog):
    def __init__(self, comm, user_id):
        super().__init__()
        self.comm = comm
        self.user_id = user_id
        self.selected_users = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Создать новый чат")
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout()
        
        # Название чата
        self.chat_name_label = QLabel("Название чата (обязательно для групповых чатов):")
        self.chat_name_input = QLineEdit()
        self.chat_name_input.setPlaceholderText("Введите название чата")
        
        # Список пользователей
        self.users_label = QLabel("Выберите участников:")
        self.users_list = QListWidget()
        self.users_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Кнопки
        self.create_button = QPushButton("Создать чат")
        self.create_button.clicked.connect(self.create_chat)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        # Добавляем элементы в layout
        layout.addWidget(self.chat_name_label)
        layout.addWidget(self.chat_name_input)
        layout.addWidget(self.users_label)
        layout.addWidget(self.users_list)
        
        # Горизонтальный layout для кнопок
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        self.load_users()
        
    def load_users(self):
        response = self.comm.send_message({
            'type': 'get_users',
            'force_update': True
        })
        
        if response.get('status') == 'success':
            self.users_list.clear()
            
            # Сортировка: онлайн -> по имени
            online_users = []
            offline_users = []
            
            for user in response['users']:
                if user['id'] == self.user_id:
                    continue  # Пропускаем текущего пользователя
                    
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
                
    def create_chat(self):
        selected_items = self.users_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного участника")
            return
            
        chat_name = self.chat_name_input.text().strip()
        participant_ids = [self.user_id]  # Текущий пользователь всегда участник
        
        for item in selected_items:
            participant_ids.append(item.data(Qt.ItemDataRole.UserRole))
            
        # Для групповых чатов проверяем название
        if len(participant_ids) > 2 and not chat_name:
            QMessageBox.warning(self, "Ошибка", "Для группового чата необходимо указать название")
            return
            
        # Показываем индикатор загрузки
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        try:
            response = self.comm.send_message({
                'type': 'create_chat',
                'user_id': self.user_id,
                'participant_ids': participant_ids,
                'is_group': len(participant_ids) > 2,
                'name': chat_name if chat_name else None
            })
            
            if response.get('status') == 'success':
                QMessageBox.information(self, "Успех", "Чат успешно создан")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", response.get('message', 'Не удалось создать чат'))
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка соединения: {str(e)}")
        finally:
            QApplication.restoreOverrideCursor()
