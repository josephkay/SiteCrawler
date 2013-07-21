from flask import render_template, flash, redirect
from initiator import app
import runspider
from forms import TextBox

# index view function suppressed for brevity

@app.route('/', methods = ['GET', 'POST'])
def start():
    form = TextBox()
    if form.validate_on_submit():
        #flash('Login requested for OpenID="' + form.openid.data + '", remember_me=' + str(form.remember_me.data))
        return redirect('/runspider')
    return render_template('start.html', form = form)