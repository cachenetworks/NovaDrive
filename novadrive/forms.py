from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=32)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=255)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password")],
    )


class LoginForm(FlaskForm):
    login = StringField(
        "Username or email",
        validators=[DataRequired(), Length(min=3, max=255)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    remember = BooleanField("Remember me")


class ShareLinkForm(FlaskForm):
    expires_at = DateTimeLocalField("Expires at", validators=[Optional()], format="%Y-%m-%dT%H:%M")


class MoveItemForm(FlaskForm):
    destination_folder_id = SelectField("Destination folder", coerce=int, validators=[DataRequired()])

