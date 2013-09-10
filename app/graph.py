import json
import sqlite3

def get_children(connection, parent):
	dict_list = []
	connection.execute("SELECT child FROM parents WHERE parent = ?", (parent,))
	children = c.fetchall()
	for tup in children:
		child = tup[0]
		dict = {}
		dict["name"] = child
		children_list = get_children(c, child)
		if children_list:
			dict["children"] = children_list
		dict_list.append(dict)
	return dict_list

conn = sqlite3.connect('sitecrawler.db')
c = conn.cursor()

dict = {}
dict["name"] = "root_page"
dict["children"] = get_children(c, "root_page")

with open('sitemap.json', 'w') as outfile:
  json.dump(dict, outfile)

print dict