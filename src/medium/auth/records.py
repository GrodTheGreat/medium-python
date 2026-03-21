from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from medium.users.record import UserRecord


class RefreshTokenRecord(SQLModel, table=True):
    __tablename__ = "refresh_token"

    token_hash: str = Field(primary_key=True)
    user_id: int | None = Field(
        default=None,
        primary_key=True,
        foreign_key="user.id",
        index=True,
    )
    expires_at: datetime
    revoked_at: datetime | None = Field(default=None, nullable=True, index=True)

    user: Optional["UserRecord"] = Relationship(back_populates="refresh_tokens")


class UserSessionRecord(SQLModel, table=True):
    __tablename__ = "session"

    session_hash: str = Field(primary_key=True)
    user_id: int | None = Field(
        default=None,
        primary_key=True,
        foreign_key="user.id",
        index=True,
    )
    expires_at: datetime = Field(index=True)
    revoked_at: datetime | None = Field(default=None, nullable=True, index=True)

    user: Optional["UserRecord"] = Relationship(back_populates="sessions")
