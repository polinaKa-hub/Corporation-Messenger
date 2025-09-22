import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

from server.database import engine
from sqlalchemy import text

def run_migrations():
    print("Начало применения миграций...")
    with engine.connect() as conn:
        try:
            # Проверяем существование столбцов
            conn.execute(text("SELECT online FROM users LIMIT 1"))
            print("Миграции уже применены")
        except Exception:
            # Применяем миграции
            conn.execute(text("ALTER TABLE users ADD COLUMN online BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE users ADD COLUMN last_seen DATETIME"))
            conn.commit()
            print("Миграции успешно применены")

if __name__ == "__main__":
    run_migrations()