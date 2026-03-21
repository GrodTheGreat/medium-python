from medium.schemas import BaseSchema


class UserSchema(BaseSchema):
    id: int
    username: str
