from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem,
                            QMessageBox)
from PyQt6.QtCore import Qt

class AddParticipantDialog(QDialog):
    def __init__(self, chat_window):
        super().__init__(chat_window)
        self.chat_window = chat_window
        self.setWindowTitle("Добавить участника")
        self.setFixedSize(300, 400)
        
        layout = QVBoxLayout()
        
        self.users_list = QListWidget()
        self.load_users()
        
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_participant)
        
        layout.addWidget(self.users_list)
        layout.addWidget(self.add_button)
        self.setLayout(layout)
    
    def load_users(self):
        response = self.chat_window.comm.send_message({
            'type': 'get_users',
            'force_update': True
        })
        
        if response.get('status') == 'success':
            self.users_list.clear()
            
            # Получаем текущих участников чата
            participants_response = self.chat_window.comm.send_message({
                'type': 'get_chat_participants',
                'chat_id': self.chat_window.current_chat
            })
            
            current_participants = []
            if participants_response.get('status') == 'success':
                current_participants = [p['id'] for p in participants_response['participants']]
            
            # Фильтруем пользователей, которые ещё не в чате
            for user in response['users']:
                if user['id'] != self.chat_window.user_id and user['id'] not in current_participants:
                    status = "🟢" if user['online'] else "🔴"
                    item = QListWidgetItem(f"{status} {user['username']}")
                    item.setData(Qt.ItemDataRole.UserRole, user['id'])
                    self.users_list.addItem(item)
    
    def add_participant(self):
        selected = self.users_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
        
        participant_id = selected.data(Qt.ItemDataRole.UserRole)
        
        try:
            response = self.chat_window.comm.send_message({
                'type': 'add_participant',
                'chat_id': self.chat_window.current_chat,
                'user_id': self.chat_window.user_id,
                'participant_id': participant_id
            })
            
            if response.get('status') == 'success':
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", response.get('message', 'Ошибка добавления'))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка соединения: {str(e)}")
