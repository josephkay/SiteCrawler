import BeautifulSoup
import urllib2
import re
from nltk.tokenize import sent_tokenize
from nltk.corpus import cmudict
from nltk.tokenize import RegexpTokenizer

html = urllib2.urlopen('http://www.premierinn.com/en/business.html').read()
soup = BeautifulSoup.BeautifulSoup(html)
texts = soup.findAll(text=True)

def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True

def sentence(element):
	sentence_chars = [".","!","?"]
	for char in sentence_chars:
		if char in str(element):
			return True
	return False

def length(element):
	if len(str(element).split()) < 5:
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
			

visible_texts = filters([visible,sentence,length], texts)

sentences = sentence_split(visible_texts)

print len(sentences)
print sentences
print syllables(sentences)