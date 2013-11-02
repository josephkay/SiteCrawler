import BeautifulSoup
import urllib2
import re
from nltk.tokenize import sent_tokenize
from nltk.corpus import cmudict
from nltk.tokenize import RegexpTokenizer
from HTMLParser import HTMLParser

html = urllib2.urlopen('http://www.premierinn.com/en/norwich-hotels.html').read()

#html = re.sub('<!--.*-->', '', html)
def remove_comments(html):
	while True:
		start = html.find("<!--")
		if start == -1:
			break
		end = html.find("-->", start)
		html = html[:start] + html[end+3:]
	return html

html = remove_comments(html)

h = open("newhtml.txt", "w")
h.write(html)
h.close()

soup = BeautifulSoup.BeautifulSoup(html)
texts = soup.findAll(text=True)

def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    return True

def sentence(element):
	sentence_chars = [".","!","?"]
	for char in sentence_chars:
		if char in element:
			return True
	return False

def length(element):
	if len(element.split()) < 5:
		return False
	return True

def filters(filter_list, texts):
	for f in filter_list:
		texts = filter(f, texts)
	return texts

def sentence_split(text_list):
	new_list = []
	for text in text_list:
		sents = sent_tokenize(text)
		for sent in sents:
			new_list.append(sent)
	return new_list

def syllables(text_list):
	d = cmudict.dict()
	tokenizer = RegexpTokenizer(r'\w+')
	new_set = set()
	error_count = 0
	s_list = []
	for text in text_list:
		for word in tokenizer.tokenize(text):
			try:
				syllables = [len(list(y for y in x if y[-1].isdigit())) for x in d[word.lower()]] 
				s_list.append(float(syllables[0]))
			except:
				syllables = (-1,)
				error_count += 1
			new_set.add((word, syllables[0]))
	return list(new_set), error_count, sum(s_list)/len(s_list)
			
def word_split(text_list):
	tokenizer = RegexpTokenizer(r'\w+')
	new_dict = {}
	for text in text_list:
		for word in tokenizer.tokenize(text):
			word = word.lower()
			if word in new_dict:
				new_dict[word] += 1
			else:
				new_dict[word] = 1
	return new_dict

def replace_breaks(texts):
	return [re.sub(r"\s+", " ", text) for text in texts]

class MLStripper(HTMLParser):
	def __init__(self):
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		self.fed, output = [], self.fed
		return ''.join(output)

def strip_tags(texts):
	s = MLStripper()
	new_list = []
	for text in texts:
		s.feed(text)
		new_list.append(s.get_data())
	return new_list

def convert_entities(texts):
	h = HTMLParser()
	return [h.unescape(text) for text in texts]

visible_texts = filters([visible], texts)
#stripped = replace_breaks(strip_tags(convert_entities(visible_texts)))
#sentences = filters([sentence,length], stripped)


f_list = []
for text in texts:
	text = text.replace('\n', '')
	text = text.replace('\t', ' ')
	if text:
		f_list.append(text+"\n")
		f_list.append("-----------------------------------\n")

f = open("bstestfile.txt", "w")
f.writelines(f_list)
f.close()

stripped = [item.encode("utf-8").strip() for item in replace_breaks(convert_entities(visible_texts))]

st = open("bstestfile2.txt", "w")
st.writelines([strip + "\n" for strip in stripped])
st.close()

sentences = filters([sentence,length], stripped)

s = open("bstestfile3.txt", "w")
s.writelines([sent + "\n\n" for sent in sentences])
s.close()


#print len(sentences)
#print sentences
#print syllables(sentences)