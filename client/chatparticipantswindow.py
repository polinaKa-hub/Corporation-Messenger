from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem,
                            QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt
from .addparticipantdialog import AddParticipantDialog

class ChatParticipantsWindow(QDialog):
    def __init__(self, participants, chat_window):
        super().__init__(chat_window)
        self.chat_window = chat_window
        self.setWindowTitle("Участники чата")
        self.setFixedSize(300, 400)
        
        layout = QVBoxLayout()
        
        self.participants_list = QListWidget()
        self.update_participants_list(participants)
        
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить участника")
        self.add_button.clicked.connect(self.show_add_participant_dialog)
        
        self.remove_button = QPushButton("Удалить участника")
        self.remove_button.clicked.connect(self.remove_participant)
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        
        layout.addWidget(self.participants_list)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def update_participants_list(self, participants):
        self.participants_list.clear()
        for p in participants:
            status = "🟢" if p['online'] else "🔴"
            item = QListWidgetItem(f"{status} {p['username']}")
            item.setData(Qt.ItemDataRole.UserRole, p['id'])
            self.participants_list.addItem(item) 

    def show_add_participant_dialog(self):
        dialog = AddParticipantDialog(self.chat_window)
        if dialog.exec():
            # Обновляем список участников после добавления
            response = self.chat_window.comm.send_message({
                'type': 'get_chat_participants',
                'chat_id': self.chat_window.current_chat
            })
            if response.get('status') == 'success':
                self.update_participants_list(response['participants'])
                self.chat_window.load_messages(self.chat_window.current_chat)
                self.chat_window.load_chats()

    
    def remove_participant(self):
        selected = self.participants_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите участника")
            return
        
        participant_id = selected.data(Qt.ItemDataRole.UserRole)
        
        try:
            response = self.chat_window.comm.send_message({
                'type': 'remove_participant',
                'chat_id': self.chat_window.current_chat,
                'user_id': self.chat_window.user_id,
                'participant_id': participant_id
            })
            
            if response.get('status') == 'success':
                # Обновляем список участников
                response = self.chat_window.comm.send_message({
                    'type': 'get_chat_participants',
                    'chat_id': self.chat_window.current_chat
                })
                if response.get('status') == 'success':
                    self.update_participants_list(response['participants'])
                    self.chat_window.load_messages(self.chat_window.current_chat)
                    self.chat_window.load_chats()
            else:
                QMessageBox.warning(self, "Ошибка", response.get('message', 'Ошибка удаления'))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка соединения: {str(e)}")
