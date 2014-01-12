#!flask/bin/python
from initiator import app
from scrapy.utils.project import get_project_settings as Settings
app.run(debug = True, port = 8000)
