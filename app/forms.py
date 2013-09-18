from flask.ext.wtf import Form, TextField, BooleanField, SubmitField, RadioField
from flask.ext.wtf import Required

class TextBox(Form):
    url = TextField('url', validators = [Required()])

class BoolForm(Form):
	answer = BooleanField('answer', validators = [Required()])

class ButtonForm(Form):
	answer = SubmitField('answer', validators = [Required()])

class RadioForm(Form):
	answer = RadioField('answer', validators = [Required()], choices = [], coerce = unicode)