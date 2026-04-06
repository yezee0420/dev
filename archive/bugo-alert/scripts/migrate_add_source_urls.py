"""source_urls 컬럼 추가 마이그레이션.

실행: cd bugo-alert && python scripts/migrate_add_source_urls.py
"""

from sqlalchemy import text
from app.database import engine


def migrate():
    conn = engine.connect()
    try:
        result = conn.execute(text("PRAGMA table_info(obituaries)"))
        columns = [row[1] for row in result.fetchall()]
        if "source_urls" not in columns:
            conn.execute(text("ALTER TABLE obituaries ADD COLUMN source_urls TEXT"))
            conn.commit()
            print("source_urls 컬럼 추가 완료")
        else:
            print("source_urls 컬럼 이미 존재")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
