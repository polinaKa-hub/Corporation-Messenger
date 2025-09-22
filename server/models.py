from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    name = Column(String)
    online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("Message", back_populates="user")
    chat_participants = relationship("ChatParticipant", back_populates="user")

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    is_group = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    participants = relationship("ChatParticipant", back_populates="chat")
    messages = relationship("Message", back_populates="chat")

class ChatParticipant(Base):
    __tablename__ = 'chat_participants'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    chat_id = Column(Integer, ForeignKey('chats.id'))
    
    user = relationship("User", back_populates="chat_participants")
    chat = relationship("Chat", back_populates="participants")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    chat_id = Column(Integer, ForeignKey('chats.id'))
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_system = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")