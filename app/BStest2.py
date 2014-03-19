from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen

url = "http://www.premierinn.com"

html = urlopen(url).read()
soup = BeautifulSoup(html)
images = soup('img')

withalt = []
withdims = []

for image in images:
	if image.has_key("alt"):
		withalt.append(image)
	if image.has_key("height") and image.has_key("width"):
		withdims.append(image)

print len(images)
print len(withalt)
print len(withdims)


flashes = soup.findAll('object')

print flashes

f = open('testhtml.txt', 'w')
f.write(html)
f.close