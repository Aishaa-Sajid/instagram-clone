from datetime import datetime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.expression import text
from sqlalchemy import Boolean
from src.database.config import Base
from sqlalchemy import TIMESTAMP, func, text
from src.database.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)

    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)

    password: Mapped[str] = mapped_column(nullable=False)

    bio: Mapped[str | None] = mapped_column(nullable=True)
    profile_picture: Mapped[str | None] = mapped_column(nullable=True)

    is_private: Mapped[bool] = mapped_column(Boolean, default=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str | None] = mapped_column(nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )
    
    posts = relationship("Post", back_populates="owner", cascade="all, delete-orphan")
    # comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    # likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")

    # stories = relationship("Story", back_populates="user", cascade="all, delete-orphan")

    # followers = relationship(
    #     "Follow",
    #     foreign_keys="[Follow.following_id]",
    #     back_populates="following",
    #     cascade="all, delete-orphan"
    # )

    # following = relationship(
    #     "Follow",
    #     foreign_keys="[Follow.follower_id]",
    #     back_populates="follower",
    #     cascade="all, delete-orphan"
    # )
