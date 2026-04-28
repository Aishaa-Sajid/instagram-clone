from sqlalchemy import ForeignKey, Text, Boolean
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.expression import text
from src.database.models.mixins import TimestampMixin
from src.database.config import Base

if TYPE_CHECKING:
    from src.database.models.post_image import PostImage


class Post(TimestampMixin, Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    owner = relationship("User", back_populates="posts")

    images: Mapped[List["PostImage"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
