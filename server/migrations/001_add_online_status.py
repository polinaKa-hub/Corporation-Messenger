from sqlalchemy import text
from server.database import engine

def upgrade():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN online BOOLEAN DEFAULT FALSE"))
        conn.execute(text("ALTER TABLE users ADD COLUMN last_seen DATETIME"))
        conn.commit()

def downgrade():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users DROP COLUMN online"))
        conn.execute(text("ALTER TABLE users DROP COLUMN last_seen"))
        conn.commit()