import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )

    # Relacje (SQLAlchemy, a nie fizyczne klucze w bazie)
    users: Mapped[list["User"]] = relationship(
        back_populates="organization", 
        cascade="all, delete-orphan"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="organization", 
        cascade="all, delete-orphan"
    )