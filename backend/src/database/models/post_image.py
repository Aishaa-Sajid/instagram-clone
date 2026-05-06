from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models.mixins import TimestampMixin
from src.database.config import Base
if TYPE_CHECKING:
    from src.database.models.post import Post


class PostImage(TimestampMixin, Base):
    __tablename__ = "post_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    public_id: Mapped[str] = mapped_column(String, nullable=False)

    post: Mapped["Post"] = relationship("Post", back_populates="images")
