from sqlalchemy import text
from .database import engine  # Изменено с server.database

def run_migrations():
    print("Начало применения миграций...")
    with engine.connect() as conn:
        try:
            # Проверка наличия столбца online
            conn.execute(text("SELECT online, last_seen FROM users LIMIT 1"))
            print("Поля online и last_seen уже существуют")
        except Exception:
            conn.execute(text("ALTER TABLE users ADD COLUMN online BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE users ADD COLUMN last_seen DATETIME"))
            conn.commit()
            print("Поля online и last_seen добавлены")
 
        try:
            # Проверка наличия столбца is_system
            conn.execute(text("SELECT is_system FROM messages LIMIT 1"))
            print("Поле is_system уже существует")
        except Exception:
            conn.execute(text("ALTER TABLE messages ADD COLUMN is_system BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("Поле is_system добавлено в messages")

if __name__ == "__main__":
    run_migrations()