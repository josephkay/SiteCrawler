from flask import render_template, flash, redirect, url_for
from initiator import app
import runspider
from forms import TextBox
from SiteCrawler.spiders.myfuncs import test_url

# index view function suppressed for brevity

@app.route('/', methods = ['GET', 'POST'])
def start():
    form = TextBox()
    if form.validate_on_submit():
        if test_url(form.url.data):
			return redirect(url_for('runspider', route = form.url.data))
    return render_template('start.html', form = form)