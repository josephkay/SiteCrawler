from flask.ext.wtf import Form, TextField, BooleanField
from flask.ext.wtf import Required

class TextBox(Form):
    url = TextField('url', validators = [Required()])

class BoolForm(Form):
	answer = BooleanField('answer', validators = [Required()])