from contextlib import closing
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import bs4 as bs
import time

phantomjs = r"C:\Users\kayj\AppData\Roaming\npm\node_modules\phantomjs\lib\phantom\phantomjs"
url = "http://www.premierinn.com"

#with closing(webdriver.PhantomJS(phantomjs)) as browser:
with closing(webdriver.Firefox()) as browser:
	#browser.implicitly_wait(20)
	browser.get(url)
	WebDriverWait(browser, timeout=1)
	time.sleep(2)
	#WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "flashAlternativeContent_quickflash.Single")))
	html = browser.page_source.encode("ascii", errors="ignore")
	browser.save_screenshot("screentest.png")

soup = bs.BeautifulSoup(html)
images = soup('img')
flashes = soup(type="application/x-shockwave-flash")
links = soup('a')
pdfs = []
withalt = []
withdims = []

for image in images:
	if image.has_key("alt"):
		withalt.append(image)
	if image.has_key("height") and image.has_key("width"):
		withdims.append(image)

for link in links:
	if link.has_key("href"):
		if ".pdf" in link['href']:
			pdfs.append(link)

print len(images)
print len(withalt)
print len(withdims)
print len(flashes)
print len(pdfs)

for i in images:
	print i

f = open('testhtml.txt', 'w')
f.writelines([str(i) for i in images])
f.close