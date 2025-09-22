import socket
from sqlalchemy import func
import threading
import json
from server.database import get_db, init_db
from .models import User, Chat, Message, ChatParticipant
from sqlalchemy.orm import Session
from datetime import datetime
from Crypto.Hash import SHA256
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='messenger.log'
)
logger = logging.getLogger(__name__)

class Server:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.clients = {}
        self.init_database()
        
    def init_database(self):
        init_db()
        
    def hash_password(self, password):
        return SHA256.new(password.encode()).hexdigest()
        
    def handle_client(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")
        user_id = None
        db = next(get_db())
        
        try:
            while True:
                try:
                    # Читаем заголовок с размером данных (4 байта)
                    header = conn.recv(4)
                    if not header:
                        break
                        
                    data_size = int.from_bytes(header, byteorder='big')
                    
                    # Получаем данные частями
                    received_data = b''
                    while len(received_data) < data_size:
                        chunk = conn.recv(min(data_size - len(received_data), 4096))
                        if not chunk:
                            raise ConnectionError("Connection broken")
                        received_data += chunk
                    
                    # Декодируем и парсим JSON
                    message = json.loads(received_data.decode('utf-8'))
                    
                    if not isinstance(message, dict):
                        raise ValueError("Invalid message format")
                        
                    if message.get('type') == 'login':
                        user_id = message.get('user_id')
                    
                    try:
                        response = self.process_message(message)
                        response_data = json.dumps(response, default=str).encode('utf-8')
                        conn.send(len(response_data).to_bytes(4, byteorder='big'))
                        conn.sendall(response_data)
                    except Exception as e:
                        logger.error(f"Ошибка сериализации ответа для клиента {addr}: {e}")
                        error_response = {'status': 'error', 'message': f'Serialization error: {str(e)}'}
                        error_data = json.dumps(error_response).encode('utf-8')
                        conn.send(len(error_data).to_bytes(4, byteorder='big'))
                        conn.sendall(error_data)
                    
                except json.JSONDecodeError as e:
                    print(f"[JSON ERROR] {addr}: {e}")
                    error_response = {'status': 'error', 'message': 'Invalid JSON'}
                    error_data = json.dumps(error_response).encode('utf-8')
                    conn.send(len(error_data).to_bytes(4, byteorder='big'))
                    conn.sendall(error_data)
                except UnicodeDecodeError as e:
                    print(f"[DECODE ERROR] {addr}: {e}")
                    continue
                except Exception as e:
                    print(f"[PROCESSING ERROR] {addr}: {e}")
                    break
                    
        except ConnectionResetError:
            print(f"[CONNECTION RESET] {addr}")
        except Exception as e:
            print(f"[CLIENT ERROR] {addr}: {e}")
        finally:
            if user_id:
                try:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.online = False
                        user.last_seen = datetime.utcnow()
                        db.commit()
                except Exception as e:
                    print(f"Error updating user status: {e}")
            conn.close()
            print(f"[DISCONNECTED] {addr} disconnected.")
            
    def process_message(self, message):
        db = next(get_db())
        try:
            msg_type = message.get('type')
            
            if msg_type == 'register':
                return self.register_user(db, message)
            elif msg_type == 'login':
                return self.login_user(db, message)
            elif msg_type == 'get_chats':
                return self.get_user_chats(db, message)
            elif msg_type == 'get_messages':
                return self.get_chat_messages(db, message)
            elif msg_type == 'send_message':
                return self.save_message(db, message)
            elif msg_type == 'create_chat':
                return self.create_chat(db, message)
            elif msg_type == 'update_profile':
                return self.update_profile(db, message)
            elif msg_type == 'get_users':
                return self.get_all_users(db, message)
            elif msg_type == 'update_chat_name':
                return self.update_chat_name(db, message)
            elif msg_type == 'get_chat_participants':
                return self.get_chat_participants(db, message)
            elif msg_type == 'remove_participant':
                return self.remove_chat_participant(db, message)
            elif msg_type == 'add_participant':
                return self.add_chat_participant(db, message)
            else:
                return {'status': 'error', 'message': 'Unknown message type'}
        finally:
            db.close()

    def update_profile(self, db: Session, message):
        user_id = message.get('user_id')
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'status': 'error', 'message': 'User not found'}
        
        response = {'status': 'success'}
        
        # Обновление имени
        if 'new_name' in message:
            user.name = message['new_name']
            response['new_name'] = user.name
        
        # Обновление логина
        if 'new_username' in message:
            new_username = message['new_username']
            existing_user = db.query(User).filter(User.username == new_username).first()
            if existing_user and existing_user.id != user_id:
                return {'status': 'error', 'message': 'Username already exists'}
            
            # Проверка пароля при изменении логина
            if 'password' in message and user.password_hash != self.hash_password(message['password']):
                return {'status': 'error', 'message': 'Invalid password'}
            
            user.username = new_username
            response['new_username'] = user.username
        
        # Обновление пароля
        if 'new_password' in message:
            if 'old_password' not in message or user.password_hash != self.hash_password(message['old_password']):
                return {'status': 'error', 'message': 'Invalid current password'}
            
            user.password_hash = self.hash_password(message['new_password'])
        
        db.commit()
        return response

    def register_user(self, db: Session, message):
        username = message.get('username')
        password = message.get('password')
        
        if not username or not password:
            return {'status': 'error', 'message': 'Username and password required'}
            
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return {'status': 'error', 'message': 'Username already exists'}
            
        hashed_password = self.hash_password(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        
        return {'status': 'success', 'message': 'User registered successfully'}
        
    def login_user(self, db: Session, message):
        username = message.get('username')
        password = message.get('password')
        
        user = db.query(User).filter(User.username == username).first()
        if not user or user.password_hash != self.hash_password(password):
            return {'status': 'error', 'message': 'Invalid credentials'}
        
        user.online = True
        user.last_seen = datetime.utcnow()
        db.commit()
        
        return {
            'status': 'success', 
            'message': 'Login successful', 
            'user_id': user.id,
            'name': user.name if user.name else username
        }
        
    def get_user_chats(self, db: Session, message):
        user_id = message.get('user_id')
        chats = db.query(Chat).join(ChatParticipant).filter(ChatParticipant.user_id == user_id).all()
        
        chats_data = []
        for chat in chats:
            participants = [p.user.username for p in chat.participants]
            chats_data.append({
                'id': chat.id,
                'name': chat.name if chat.is_group else participants[0] if participants[0] != message.get('username') else participants[1],
                'is_group': chat.is_group,
                'participants': participants
            })
            
        return {'status': 'success', 'chats': chats_data}
        
    def get_chat_messages(self, db: Session, message):
        chat_id = message.get('chat_id')
        messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'user_id': msg.user_id,
                'username': msg.user.username,
                'text': msg.text,
                'timestamp': msg.timestamp.isoformat(),
                'is_system': msg.is_system  # ← добавлено
            })
            
        return {'status': 'success', 'messages': messages_data}
        
    def save_message(self, db: Session, message):
        user_id = message.get('user_id')
        chat_id = message.get('chat_id')
        text = message.get('text')
        
        new_message = Message(user_id=user_id, chat_id=chat_id, text=text)
        db.add(new_message)
        db.commit()
        
        return {'status': 'success', 'message': 'Message sent'}
        
    def create_chat(self, db: Session, message):
        try:
            # Проверка обязательных полей
            if not all(k in message for k in ['user_id', 'participant_ids']):
                return {'status': 'error', 'message': 'Missing required fields'}
            
            user_id = message['user_id']
            participant_ids = message['participant_ids']
            is_group = message.get('is_group', len(participant_ids) > 2)
        
            # Для групповых чатов проверяем название
            if is_group and len(participant_ids) > 2 and not message.get('name'):
                return {'status': 'error', 'message': 'Group chat requires a name'}
            
            # Валидация участников
            if not isinstance(participant_ids, list) or user_id not in participant_ids:
                return {'status': 'error', 'message': 'Invalid participants'}
            
            # Проверка существования пользователей
            users = db.query(User).filter(User.id.in_(participant_ids)).all()
            if len(users) != len(participant_ids):
                return {'status': 'error', 'message': 'One or more users not found'}
            
            # Для приватных чатов проверяем существование
            if not is_group and len(participant_ids) == 2:
                existing_chat = db.query(Chat).join(ChatParticipant).filter(
                    Chat.is_group == False,
                    ChatParticipant.user_id.in_(participant_ids)
                ).group_by(Chat.id).having(func.count(ChatParticipant.user_id) == 2).first()
                
                if existing_chat:
                    return {
                        'status': 'success', 
                        'chat_id': existing_chat.id,
                        'message': 'Chat already exists',
                        'existing': True
                    }
            
            # Создаем чат
            name = self.generate_chat_name(db, participant_ids, is_group, message.get('name'))
            chat = Chat(is_group=is_group, name=name)
            db.add(chat)
            db.flush()  # Получаем ID чата без коммита
            
            # Добавляем участников
            for participant_id in participant_ids:
                db.add(ChatParticipant(
                    user_id=participant_id,
                    chat_id=chat.id
                ))
            
            db.commit()
            
            return {
                'status': 'success',
                'chat_id': chat.id,
                'chat_name': name,
                'message': 'Chat created successfully'
            }
            
        except Exception as e:
            db.rollback()
            return {
                'status': 'error',
                'message': f'Failed to create chat: {str(e)}'
            }

    def generate_chat_name(self, db: Session, participant_ids, is_group, custom_name=None):
        if custom_name:
            return custom_name
        if not is_group and len(participant_ids) == 2:
            users = db.query(User).filter(User.id.in_(participant_ids)).all()
            return " & ".join(sorted([u.username for u in users]))
        return "Group Chat"
        
    def start(self):
        print(f"[SERVER] Server is listening on {self.host}:{self.port}")
        try:
            while True:
                conn, addr = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.start()
                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        except KeyboardInterrupt:
            print("[SERVER] Shutting down...")
            self.server.close()

    def get_all_users(self, db: Session, message):
        try:
            # Принудительное обновление статусов, если требуется
            force_update = message.get('force_update', False)
            users = db.query(User).all()
            
            if force_update:
                for user in users:
                    is_online = (datetime.utcnow() - user.last_seen).total_seconds() < 30 \
                        if user.last_seen else False
                    if user.online != is_online:
                        user.online = is_online
                db.commit()
            
            users_data = []
            for user in users:
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'name': user.name if user.name else user.username,
                    'online': user.online
                })
            
            return {
                'status': 'success',
                'users': users_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка получения пользователей: {str(e)}'
            }

    def get_chat_participants(self, db: Session, message):
        chat_id = message.get('chat_id')
        if not chat_id:
            return {'status': 'error', 'message': 'Chat ID required'}
        
        try:
            participants = db.query(User).join(ChatParticipant).filter(
                ChatParticipant.chat_id == chat_id
            ).all()
            
            # Обновляем статусы перед отправкой
            for user in participants:
                is_online = (datetime.utcnow() - user.last_seen).total_seconds() < 30 \
                    if user.last_seen else False
                user.online = is_online
            db.commit()

            participants_data = []
            for user in participants:
                participants_data.append({
                    'id': user.id,
                    'username': user.username,
                    'name': user.name if user.name else user.username,
                    'online': user.online
                })
            
            return {
                'status': 'success',
                'participants': participants_data,
                'chat_id': chat_id
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка получения участников: {str(e)}'
            }

    def update_chat_name(self, db: Session, message):
        chat_id = message.get('chat_id')
        new_name = message.get('new_name')
        user_id = message.get('user_id')
        
        if not all([chat_id, new_name, user_id]):
            return {'status': 'error', 'message': 'Missing parameters'}
        
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return {'status': 'error', 'message': 'Chat not found'}
        
        # Проверяем права пользователя
        participant = db.query(ChatParticipant).filter(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == user_id
        ).first()
        
        if not participant:
            return {'status': 'error', 'message': 'Not a participant'}
        
        old_name = chat.name
        chat.name = new_name
        
        # Добавляем системное сообщение
        user = db.query(User).filter(User.id == user_id).first()
        system_message = Message(
            chat_id=chat_id,
            user_id=user_id,
            text=f"Пользователь {user.username} изменил название чата с '{old_name}' на '{new_name}'",
            is_system=True
        )
        db.add(system_message)
        db.commit()
        
        return {'status': 'success'}

    def remove_chat_participant(self, db: Session, message):
        chat_id = message.get('chat_id')
        user_id = message.get('user_id')  # Кто удаляет
        participant_id = message.get('participant_id')  # Кого удаляют
        
        # Проверяем, что user_id является участником чата
        participant = db.query(ChatParticipant).filter(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == user_id
        ).first()
        
        if not participant:
            return {'status': 'error', 'message': 'Not a participant'}
        
        # Удаляем участника
        db.query(ChatParticipant).filter(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == participant_id
        ).delete()
        
        # Добавляем системное сообщение
        user = db.query(User).filter(User.id == user_id).first()
        removed_user = db.query(User).filter(User.id == participant_id).first()
        
        system_message = Message(
            chat_id=chat_id,
            user_id=user_id,
            text=f"Пользователь {user.username} удалил {removed_user.username} из чата",
            is_system=True
        )
        db.add(system_message)
        db.commit()
        
        return {'status': 'success'}

    def add_chat_participant(self, db: Session, message):
        chat_id = message.get('chat_id')
        user_id = message.get('user_id')  # Кто добавляет
        participant_id = message.get('participant_id')  # Кого добавляют
        
        # Проверяем, что user_id является участником чата
        participant = db.query(ChatParticipant).filter(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == user_id
        ).first()
        
        if not participant:
            return {'status': 'error', 'message': 'Not a participant'}
        
        # Проверяем, что участник ещё не в чате
        existing = db.query(ChatParticipant).filter(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == participant_id
        ).first()
        
        if existing:
            return {'status': 'error', 'message': 'User already in chat'}
        
        # Добавляем участника
        db.add(ChatParticipant(
            user_id=participant_id,
            chat_id=chat_id
        ))
        
        # Добавляем системное сообщение
        user = db.query(User).filter(User.id == user_id).first()
        new_user = db.query(User).filter(User.id == participant_id).first()
        
        system_message = Message(
            chat_id=chat_id,
            user_id=user_id,
            text=f"Пользователь {user.username} добавил {new_user.username} в чат",
            is_system=True
        )
        db.add(system_message)
        db.commit()
        
        return {'status': 'success'}

if __name__ == "__main__":
    server = Server()
    server.start()