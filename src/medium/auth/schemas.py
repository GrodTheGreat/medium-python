from medium.schemas import BaseSchema
from medium.users.schemas import UserSchema


class AuthPayload(BaseSchema):
    user: UserSchema
    access: str


class SignInForm(BaseSchema):
    email: str
    password: str


class SignInPayload(BaseSchema):
    email: str
    password: str


class SignUpForm(BaseSchema):
    email: str
    username: str
    password: str
    confirm: str


class SignUpPayload(BaseSchema):
    email: str
    username: str
    password: str
    confirm: str
