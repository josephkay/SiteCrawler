from BeautifulSoup import BeautifulSoup

ht = "<div id='abc'>some long text goes <a href='/'></a> and hopefully it will get picked up by the parser as content</div>"

soup = BeautifulSoup(ht)


def ignore_tags(soup, tags_list)
for tag in tags_list
	tags = soup.findAll(tag)
	for t in tags:
		if t.string:
			t.replaceWith(t.string)
		else:
			t.replaceWith("")
		print soup