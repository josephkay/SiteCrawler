from splinter import Browser

url = "http://www.premierinn.com"

browser = Browser('phantomjs')
browser.visit(url)
html = browser.evaluate_script("document.documentElement.outerHTML")

f = open('testhtml.txt', 'w')
f.write(html)
f.close