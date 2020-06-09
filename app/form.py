from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length


class LoginForm(FlaskForm):
    login = StringField('mail', validators=[InputRequired(), Email()])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8)])


class RegisterForm(FlaskForm):
    login = StringField('mail', validators=[InputRequired(), Email()])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8)])


class CartForm(FlaskForm):
    email = StringField('mail', validators=[InputRequired(), Email()])
    name = StringField('password', validators=[InputRequired(), Length(min=8)])
    phone = StringField('password', validators=[InputRequired(), Length(min=8)])
    address = StringField('password', validators=[InputRequired(), Length(min=8)])
