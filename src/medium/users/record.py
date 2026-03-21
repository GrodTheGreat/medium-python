from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from medium.auth.records import RefreshTokenRecord, UserSessionRecord


class UserRecord(SQLModel, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    password_hash: str

    refresh_tokens:list['RefreshTokenRecord']= Relationship(back_populates="user")
    sessions: list["UserSessionRecord"] = Relationship(back_populates="user")
