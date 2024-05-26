from datetime import datetime

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

engine = create_engine("sqlite:///so.sqlite", echo=False)


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creation_timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_update_timestamp: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r})"
