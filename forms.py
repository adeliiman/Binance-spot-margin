from flask_wtf import FlaskForm
from wtforms import  SubmitField, StringField, SelectField


class UserSettingForm(FlaskForm):
    risk = StringField()
    spot = SelectField(default="spot", choices=['spot', 'margin3X', 'margin10X'] )
    submit = SubmitField()


