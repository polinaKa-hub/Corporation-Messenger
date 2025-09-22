import threading
import socket
import json
from PyQt6.QtCore import QObject, pyqtSignal

class ClientCommunication(QObject):
    message_received = pyqtSignal(dict)
    connection_error = pyqtSignal(str)
    
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.lock = threading.Lock()
        self.connection_timeout = 10  # секунд
        self.operation_timeout = 30   # секунд
        
    def connect_to_server(self):
        try:
            with self.lock:
                if self.socket:
                    self.socket.close()
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.connection_timeout)
                self.socket.connect((self.host, self.port))
                self.connected = True
                return True
                
        except Exception as e:
            self.connection_error.emit(f"Ошибка подключения: {str(e)}")
            self.connected = False
            return False
            
    def send_message(self, message):
        if not self.connected and not self.connect_to_server():
            return {'status': 'error', 'message': 'Connection failed'}
        
        try:
            with self.lock:
                # Добавляем таймаут для операций
                self.socket.settimeout(self.operation_timeout)
                
                data = json.dumps(message).encode('utf-8')
                header = len(data).to_bytes(4, byteorder='big')
                
                # Отправка с проверкой
                try:
                    self.socket.sendall(header + data)
                except (ConnectionResetError, BrokenPipeError):
                    self.connected = False
                    if not self.connect_to_server():
                        return {'status': 'error', 'message': 'Reconnection failed'}
                    self.socket.sendall(header + data)
                
                # Получение ответа
                try:
                    header = self.socket.recv(4)
                    if not header:
                        raise ConnectionError("Server closed connection")
                        
                    response_size = int.from_bytes(header, byteorder='big')
                    received = 0
                    chunks = []
                    
                    while received < response_size:
                        chunk = self.socket.recv(min(response_size - received, 4096))
                        if not chunk:
                            raise ConnectionError("Incomplete response")
                        chunks.append(chunk)
                        received += len(chunk)

                    response = json.loads(b''.join(chunks).decode('utf-8'))
                    return response
                
                except (socket.timeout, ConnectionResetError, BrokenPipeError):
                    self.connected = False
                    return {'status': 'error', 'message': 'Server closed connection'}
                
        except socket.timeout:
            self.connected = False
            return {'status': 'error', 'message': 'Timeout'}
        except ConnectionResetError:
            self.connected = False
            return {'status': 'error', 'message': 'Connection reset by server'}
        except json.JSONDecodeError:
            self.connected = False
            return {'status': 'error', 'message': 'Invalid server response'}
        except Exception as e:
            self.connected = False
            return {'status': 'error', 'message': f'Communication error: {str(e)}'}
            
    def close_connection(self):
        with self.lock:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            self.connected = False
