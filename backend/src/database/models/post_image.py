from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime,TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.config import Base
if TYPE_CHECKING:
    from .post import Post

#  print("abc") 

class PostImage(Base):
    __tablename__ = "post_images"

    image_id: Mapped[int] = mapped_column(primary_key=True, index=True)

    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.post_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    image_url: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    post: Mapped["Post"] = relationship(
        back_populates="images"
    )