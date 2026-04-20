from sqlalchemy import ForeignKey,Text,Boolean
from typing import List,TYPE_CHECKING
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from datetime import datetime
from src.database.config import Base
if TYPE_CHECKING:
    from .post_image import PostImage

#  
class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    
    created_at: Mapped[datetime] = mapped_column(
    TIMESTAMP(timezone=True),
    nullable=False,
    server_default=text("now()")
)

    updated_at: Mapped[datetime] = mapped_column(
    TIMESTAMP(timezone=True),
    nullable=False,
    server_default=text("now()"),
    onupdate=text("now()")
)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    owner = relationship("User", back_populates="posts")

    images: Mapped[List["PostImage"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan"
    )
    # images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")
    # comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    # likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
