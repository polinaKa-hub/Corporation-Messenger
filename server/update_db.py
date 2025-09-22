from sqlalchemy import text
from server.database import engine, SessionLocal
from server.models import User

def add_name_column():
    """Добавляет столбец name в таблицу users"""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR"))
            conn.commit()
            print("[✓] Столбец 'name' успешно добавлен в таблицу users")
        except Exception as e:
            print(f"[!] Ошибка при добавлении столбца: {e}")

def update_existing_users():
    """Обновляет существующих пользователей, устанавливая name = username"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        updated_count = 0
        
        for user in users:
            if not user.name:
                user.name = user.username
                updated_count += 1
        
        db.commit()
        print(f"[✓] Обновлено {updated_count} пользователей")
    except Exception as e:
        print(f"[!] Ошибка при обновлении пользователей: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Начало обновления базы данных...")
    add_name_column()
    update_existing_users()
    print("Обновление завершено")