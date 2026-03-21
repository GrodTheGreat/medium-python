from typing import Annotated

from fastapi import Form

from .schemas import SignInForm, SignUpForm

SignInFormData = Annotated[SignInForm, Form()]
SignUpFormData = Annotated[SignUpForm, Form()]
