from datetime import datetime, UTC
from sqlalchemy.orm import declarative_mixin, Mapped, mapped_column
from sqlalchemy import TIMESTAMP, func, text


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )
