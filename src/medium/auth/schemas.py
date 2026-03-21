from medium.schemas import BaseSchema


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
