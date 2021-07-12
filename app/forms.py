from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired
from datetime import date, timedelta


class TaskForm(FlaskForm):
    submit = SubmitField(label='Получить данные с deezer.com')


class SearchForm(FlaskForm):
    title = StringField('Поиск по названию: ', validators=[DataRequired(),])
    submit = SubmitField(label='Поиск')
