import json
import sqlite3

def get_children(connection, parent):
	dict = {}
	connection.execute("SELECT child FROM parents WHERE parent = ?", (parent,))
	children = c.fetchall()
	for (child) in children:
		dict["name"] = child
		dict["children"] = []
		dict["children"].append(get_children(c, child))
	return dict

conn = sqlite3.connect('sitecrawler.db')
c = self.conn.cursor()

dict = {}
dict["name"] = "root_page"
dict["children"] = []

dict["children"].append(get_children(c, "root_page"))

with open('sitemap.json', 'w') as outfile:
  json.dump(dict, outfile)