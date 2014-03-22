# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html
from os import getcwd
import sqlite3
import json
from scrapy.exceptions import DropItem
from scrapy import signals
from scrapy.contrib.exporter import CsvItemExporter
from spiders.myfuncs import *
from scrapy import log
import math
from operator import itemgetter
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import bs4 as bs

class DuplicatesPipeline(object):
    
    def __init__(self):
        self.urls_seen = set()
    
    def process_item(self, item, spider):
        
        if item['url_obj'].full in self.urls_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.urls_seen.add(item['url_obj'].full)
            return item

class HTMLPipeline(object):
        
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline
    
    def spider_opened(self, spider):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.scrapeid = spider.scrapeid
    
    def spider_closed(self, spider):
        self.conn.commit()
        self.conn.close()
    
    def process_item(self, item, spider):
        log.msg("content")
        
        html = get_HTML(item['url_obj'].full)
        soup = bs.BeautifulSoup(html)
        fresh_soup = bs.BeautifulSoup(urlopen(item['url_obj'].full).read())
        
        images = [i for i in soup('img')]
        image_rows = []
        flashes = [f for f in soup(type="application/x-shockwave-flash")]
        links = [l for l in soup('a')]
        pdfs = []
        h1s = [h for h in soup('h1')]
        h2s = [h for h in soup('h2')]
        h3s = [h for h in soup('h3')]
        h4s = [h for h in soup('h4')]
        h5s = [h for h in soup('h5')]
        h6s = [h for h in soup('h6')]
        forms = [f for f in soup('form')]
        scripts = [s for s in fresh_soup('script')]

        for image in images:
            row = [self.scrapeid, item['url_obj'].full]
            
            for attribute in ["src","alt","height","width"]:
                if image.has_key(attribute):
                    row.append(image[attribute])
                else:
                    row.append(None)
            
            image_rows.append(row)

        for link in links:
            if link.has_key("href"):
                if ".pdf" in link['href']:
                    pdfs.append(link)
        
        content_counts = [self.scrapeid, item['url_obj'].full, len(images), len(links), len(pdfs), len(flashes), len(forms), len(scripts), len(h1s), len(h2s), len(h3s), len(h4s), len(h5s), len(h6s)]
        
        insert_rows(self.c, "INSERT INTO images (scrapeid, url, src, alt, height, width) VALUES (?, ?, ?, ?, ?, ?)", image_rows)
        insert_row(self.c, "INSERT INTO content (scrapeid, url, images, links, pdfs, flashes, forms, scripts, h1s, h2s, h3s, h4s, h5s, h6s) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", content_counts)

class ScreenshotPipeline(object):
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline
    
    def spider_opened(self, spider):
        self.date = spider.unix_date
        self.domain = spider.scrape_domain
        self.driver = webdriver.PhantomJS(executable_path=r'C:\Users\kayj\AppData\Roaming\npm\node_modules\phantomjs\lib\phantom\phantomjs')
        self.driver.set_page_load_timeout(15)
    
    def process_item(self, item, spider):
        log.msg("screenshot")
        #driver.set_window_size(1024, 768) # optional
        #  Hopefully this try/except will save things if the screenshooter crashes...
        try:
            self.driver.get(item['url_obj'].full)
        except:
            self.driver = webdriver.PhantomJS(executable_path=r'C:\Users\kayj\AppData\Roaming\npm\node_modules\phantomjs\lib\phantom\phantomjs')
            self.driver.set_page_load_timeout(15)
            self.driver.get(item['url_obj'].full)
        WebDriverWait(self.driver, timeout=2)
        self.driver.save_screenshot(r"{0}\initiator\static\scrapes\{1}\{2}\{3}.png".format(getcwd(), self.domain, self.date, item['url_obj'].name))
        return item
    
    def spider_closed(self, spider):
        pass

class TextAnalysisPipeline(object):
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline
    
    def spider_opened(self, spider):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.sentences = []
        self.words = []
        self.scrapeid = spider.scrapeid
        self.date = spider.unix_date
        self.domain = spider.scrape_domain
    
    def spider_closed(self, spider):
        insert_rows(self.c, "INSERT INTO words (scrapeid, url, word, freq) VALUES (?, ?, ?, ?)", self.words)
        insert_rows(self.c, "INSERT INTO sentences (scrapeid, url, sentence) VALUES (?, ?, ?)", self.sentences)
        
        
        
        #urls = select_from(self.c, "SELECT url FROM nodes WHERE scrapeid = ?", self.scrapeid)
        url_names = select_from(self.c, "SELECT url, name FROM nodes WHERE scrapeid = ?", self.scrapeid)
        #words = select_from(self.c, "SELECT url, word, freq FROM words WHERE scrapeid = ?", self.scrapeid)
        #sentences = select_from(self.c, "SELECT url, sentence FROM sentences WHERE scrapeid = ?", self.scrapeid)
        words = [[url, word, freq] for [scrapeid, url, word, freq] in self.words]
        sentences = [[url, sentence] for [scrapeid, url, sentence] in self.sentences]
        url_word_count = select_from(self.c, "SELECT url, SUM(freq) FROM words WHERE scrapeid = ? GROUP BY url", self.scrapeid)
        url_sentence_count = select_from(self.c, "SELECT url, COUNT(*) FROM sentences WHERE scrapeid = ? GROUP BY url", self.scrapeid)
            
        sentences = [[url, sent, 1] for [url, sent] in sentences]

        url_stats = {"Total":{"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}, "urls":{}}
        w_group_size = 1
        s_group_size = 5
        longest_word = 1
        longest_sent = 1
        

        for [url, name] in url_names:
            if url not in url_stats["urls"]:
                url_stats["urls"][url] = {"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}

        for url, word, freq in words:
            if real_word(word):
                length = len(word)
                if length > longest_word:
                    longest_word = length
                    actual_longest_word = word
                    actual_longest_word_loc = url
        
        for url, sent, freq in sentences:
            length = sentence_length(sent)
            if length > longest_sent:
                longest_sent = length
                actual_longest_sent = sent
                actual_longest_sent_loc = url

        def get_label_refs(longest, group_size):
            group_range = range(1, int(math.ceil(longest/float(group_size))+1))
            label_refs = {}
            for group_no in group_range:
                low_end = (int(group_no)-1)*group_size+1
                high_end = int(group_no)*group_size
                if low_end == high_end:
                    label = "{0}".format(low_end)
                else:
                    label = "{0} - {1}".format(low_end, high_end)
                label_refs[label] = range(low_end,high_end+1)
                labels = [label for label, lengths in sorted(label_refs.iteritems(), key=itemgetter(1))]
            return label_refs, labels
            
        w_label_refs, w_labels = get_label_refs(longest_word, w_group_size)
        s_label_refs, s_labels = get_label_refs(longest_sent, s_group_size)
        
        #These four things could all be put into one function
        def add_labels_lengths(label_refs, type, url):
            for label in label_refs:
                url_stats["urls"][url]["length"][type]["labels"][label] = {}
                for length in label_refs[label]:
                    url_stats["urls"][url]["length"][type]["labels"][label][length] = {"freq":0, "items":[]}

        for [url, name] in url_names:
            add_labels_lengths(w_label_refs, "word", url)
            add_labels_lengths(s_label_refs, "sent", url)

        for label in w_label_refs:
            url_stats["Total"]["length"]["word"]["labels"][label] = {}
            for length in w_label_refs[label]:
                url_stats["Total"]["length"]["word"]["labels"][label][length] = {"freq":0, "items":[]}
                
        for label in s_label_refs:
            url_stats["Total"]["length"]["sent"]["labels"][label] = {}
            for length in s_label_refs[label]:
                url_stats["Total"]["length"]["sent"]["labels"][label][length] = {"freq":0, "items":[]}

        def add_freqs_words(items_list, type, label_refs, length_func=None, validate_func=None):
            for url, item, freq in items_list:
                #print "{0}: {1} - {2}".format(url, item.encode("ascii", errors="ignore"), freq)
                # Remove this and put sentence filter in to remove "." further upstream
                if type == "sent" and len(item) <= 1:
                    continue
                if validate_func:
                    if not validate_func(item):
                        continue
                
                if length_func:
                    length = length_func(item)
                else:
                    length = len(item)
                if length == 0:
                    continue
                
                for lab, lengths in label_refs.iteritems():
                    if length in lengths:
                        label = lab
                        continue
                
                url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"] += freq
                url_stats["urls"][url]["length"][type]["labels"][label][length]["items"].append(item)
                
                url_stats["Total"]["length"][type]["labels"][label][length]["freq"] += freq
                if item not in url_stats["Total"]["length"][type]["labels"][label][length]["items"]:
                    url_stats["Total"]["length"][type]["labels"][label][length]["items"].append(item)

        add_freqs_words(words, "word", w_label_refs, validate_func=real_word)
        add_freqs_words(sentences, "sent", s_label_refs, length_func=sentence_length)
        
        key_db_data = []
        
        for type in ["word", "sent"]:

            for url in url_stats["urls"]:
                total = 0
                count = 0
                for label, lengths in url_stats["urls"][url]["length"][type]["labels"].iteritems():
                    for length in lengths:
                        freq = url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"]
                        total += length*freq
                        count += freq
                        #print "length: {0}, freq: {1}".format(length, freq)
                    
                url_stats["urls"][url]["length"][type]["count"] = count
                    
                if count == 0:
                    url_stats["urls"][url]["length"][type]["average"] = 0
                else:
                    url_stats["urls"][url]["length"][type]["average"] = total/float(count)
            
            total = 0
            count = 0
            for label, lengths in url_stats["Total"]["length"][type]["labels"].iteritems():
                for length in lengths:
                    freq = url_stats["Total"]["length"][type]["labels"][label][length]["freq"]
                    total += length*freq
                    count += freq
            
            url_stats["Total"]["length"][type]["count"] = count
            
            if count == 0:
                url_stats["Total"]["length"][type]["average"] = 0
            else:
                url_stats["Total"]["length"][type]["average"] = total/float(count)
        
        for url in url_stats["urls"]:
            key_db_data.append((self.scrapeid, url, url_stats["urls"][url]["length"]["word"]["average"], url_stats["urls"][url]["length"]["sent"]["average"], url_stats["urls"][url]["length"]["word"]["count"], url_stats["urls"][url]["length"]["sent"]["count"]))
        key_db_data.append((self.scrapeid, "total", url_stats["Total"]["length"]["word"]["average"], url_stats["Total"]["length"]["sent"]["average"], url_stats["Total"]["length"]["word"]["count"], url_stats["Total"]["length"]["sent"]["count"]))
        
        insert_rows(self.c, "INSERT INTO text_data (scrapeid, url, av_word_len, av_sent_len, word_count, sent_count) VALUES (?, ?, ?, ?, ?, ?)", key_db_data)
        
        
        url_name_dict = {}
        long_count = 0
        
        #for url in url_stats["urls"]:
        for [url, name] in url_names:
            #name, long_count = filename_safe(url, long_count)
            with open(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), self.domain, self.date, name), 'w') as outfile:
                json.dump(url_stats["urls"][url], outfile)
            url_name_dict[url] = name
            
        with open(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), self.domain, self.date, "total"), 'w') as outfile:
            json.dump(url_stats["Total"], outfile)
        
        extra_data = {'url_name_dict':url_name_dict, 'w_labels':w_labels, 's_labels':s_labels}
        
        save_json(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), self.domain, self.date, "extra_data"), extra_data)
        
        self.conn.commit()
        self.conn.close()
    
    def process_item(self, item, spider):
        log.msg("text analysis")
        for sentence in item['sentences']:
            self.sentences.append((self.scrapeid, item['url_obj'].full, sentence))
            
        for word, freq in item['words'].iteritems():
            self.words.append((self.scrapeid, item['url_obj'].full, word, freq))
        
        return item

class NodesPipeline(object):
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline
    
    def spider_opened(self, spider):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.node_tups = set()
        self.scrapeid = spider.scrapeid
        self.date = spider.unix_date
        self.domain = spider.scrape_domain
    
    def process_item(self, item, spider):
        self.node_tups.add((None, self.scrapeid, item['url_obj'].full, item['url_obj'].name, item['social']))
        
        return item
    
    def spider_closed(self, spider):
        insert_rows(self.c, "INSERT INTO nodes (id, scrapeid, url, name, social) VALUES (?, ?, ?, ?, ?)", list(self.node_tups))
        
        self.conn.commit()
        self.conn.close()

class EdgesPipeline(object):
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.edge_tups = set()
        self.scrapeid = spider.scrapeid
        self.date = spider.unix_date
        self.domain = spider.scrape_domain
        self.depth = -1
        self.holding = []
        self.completed_depth = []
    
    def process_item(self, item, spider):
        
        log.msg("The item:  {0}".format(item))
        
        if self.depth == -1:
            self.depth = 0
        elif item['depth'] != self.depth:
            self.depth = item['depth']
            for link in self.holding:
                self.completed_depth.append(link)
            self.holding = []
        
        for link in item['links']:
            self.holding.append(link.full)
            if link.full in self.completed_depth:
                level = 2
            else:
                level = 1
            self.edge_tups.add((self.scrapeid, item['url_obj'].full, link.full, level))
        
        return item
    
    def spider_closed(self, spider):
        # This seems inefficient. Better to get the ids all at once and match them up using a dictionary.
        new_edge_tups = []
        nlen = len(self.edge_tups)
        n = 0
        for [scrapeid, source_url, target_url, level] in self.edge_tups:
            try:
                sourceid = select_from_and(self.c, "SELECT id FROM nodes WHERE url = ? AND scrapeid = ?", source_url, scrapeid)[0][0]
                targetid = select_from_and(self.c, "SELECT id FROM nodes WHERE url = ? AND scrapeid = ?", target_url, scrapeid)[0][0]
                new_edge_tups.append((scrapeid, sourceid, targetid, level))
            except Exception, e:
                n += 1
                log.msg('-------------------------   SELECT FAILED   --------------------------')
                log.msg("Select failed: {0} --- failure: {1}/{2}".format(e, n, nlen))
        
        insert_rows(self.c, "INSERT INTO edges (scrapeid, sourceid, targetid, level) VALUES (?, ?, ?, ?)", new_edge_tups)
        
        self.conn.commit()
        self.conn.close()


class ParentsPipeline(object):
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.parent_tups = []
        self.scrapeid = spider.scrapeid
        self.date = spider.unix_date
        self.domain = spider.scrape_domain
    
    def process_item(self, item, spider):
        if not item['social']:
            for tup in item['url_obj'].parents:
                if tup not in self.parent_tups:
                    self.parent_tups.append(tup)
        
        return item
    
    def spider_closed(self, spider):
        insert_rows(self.c, "INSERT INTO parents (scrapeid, parent, child) VALUES (?, ?, ?)", self.parent_tups)
        
        url_names_dict = {url[url.find("//")+2:]: name for [url, name] in select_from(self.c, "SELECT url, name FROM nodes WHERE scrapeid = ?", self.scrapeid)}
        
        log.msg("url_names_dict:")
        
        for url, name in url_names_dict.iteritems():
            log.msg("{0} --- {1}".format(url, name))
        
        parents_dict = {}
        parents_dict["url"] = self.domain
        parents_dict["name"] = self.domain.replace("/", "-")
        parents_dict["children"] = get_children(self.c, self.domain, self.scrapeid, url_names_dict)

        with open(r'{0}\initiator\static\scrapes\{1}\{2}\sitemap.json'.format(getcwd(), self.domain, self.date), 'w') as outfile:
            json.dump(parents_dict, outfile)
        
        self.conn.commit()
        self.conn.close()
