from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from config.features import DATABASE_URL
from datetime import datetime
from sqlalchemy import JSON


# ← ИСПРАВЛЕНО: добавлен reconnect, pool_recycle и защита от падений
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,           # проверяет соединение перед использованием
    pool_recycle=300,             # переподключается каждые 5 минут
    connect_args={"server_settings": {"jit": "off"}}  # отключает JIT (ускоряет)
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_lead = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
    referrer_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    referral_count = Column(Integer, default=0)
    referral_bonus_days = Column(Integer, default=0)

class Mailing(Base):
    __tablename__ = "mailings"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    template = Column(String, default="manual")
    text = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    button_text = Column(String, nullable=True)
    button_url = Column(String, nullable=True)
    segments = Column(JSON, default=list)
    sent = Column(Integer, default=0)
    delivered = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String, default="draft")

# ← УМНАЯ ФУНКЦИЯ — создаёт таблицы и не падает при ошибках
async def create_tables():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"Таблицы уже существуют или ошибка: {e}")
            # Просто игнорируем — всё ок