	
	sentences = [url, sent, 1 for url, sent in sentences]

	url_stats = {"Total":{"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}, "urls":{}}
	w_group_size = 1
	s_group_size = 5
	longest_word, longest_sent = 1

	for url in urls:
		if url not in url_stats:
			url_stats["urls"][url] = {"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}
	
	for url, word, freq in words:
		if real_word(word):
			length = len(word)
			if length > longest_word:
				longest_word = length
	
	for url, sent, freq in sentences:
		length = sentence_length(sent)
		if length > longest_sent:
			longest_sent = length
	
	def get_label_refs(longest, group_size):
		w_group_range = range(1, int(math.ceil(longest/float(group_size))+1))
		label_refs = {}
		for group_no in w_len_range:
			low_end = (int(group_no)-1)*group_size+1
			high_end = int(group_no)*group_size
			label = "{0} - {1}".format(low_end, high_end)
			label_refs[label] = range(low_end,high_end+1)
			labels = [label for label, lengths in sorted(label_refs.iteritems(), key=itemgetter(1))]
		return label_refs, labels
		
	w_label_refs, w_labels = get_label_refs(longest_word, w_group_size)
	s_label_refs, s_labels = get_label_refs(longest_sent, s_group_size)
	
	for url in urls:
	
		for label in w_label_refs:
			url_stats["urls"][url]["length"]["word"]["labels"][label] = {}
			for length in w_label_refs[label]:
				url_stats["urls"][url]["length"]["word"]["labels"][label][length] = {"freq":0, "items":[]}
		
		for label in s_label_refs:
			url_stats["urls"][url]["length"]["sent"]["labels"][label] = {}
			for length in s_label_refs[label]:
				url_stats["urls"][url]["length"]["sent"]["labels"][label][length] = {"freq":0, "items":[]}
	
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
			if validate_func:
				if not validate_func(item):
					break
			
			if length_func:
				length = length_func(item)
			else:
				length = len(item)
			
			for lab, lengths in label_refs.iteritems():
				if length in lengths:
					label = lab
					break
			
			url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"] += freq
			url_stats["urls"][url]["length"][type]["labels"][label][length]["items"].append(item)
			
			url_stats["Total"]["length"][type]["labels"][label][length]["freq"] += freq
			url_stats["Total"]["length"][type]["labels"][label][length]["items"].append(item)
	
	add_freqs_words(words, "word", w_label_refs, validate=real_word)
	add_freqs_words(sentences, "sent", s_label_refs, length=sentence_length)
	
	for type in ["word", "sent"]:
	
		for url in url_stats:
			total, count = 0
			for label, lengths in url_stats["urls"][url]["length"][type]["labels"].iteritems():
				for length in lengths:
					freq = url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"]
					total += length*freq
					count += freq
			if count == 0:
				url_stats["urls"][url]["length"][type]["average"] = 0
			else:
			url_stats["urls"][url]["length"][type]["average"] = total/float(count)
		
		total, count = 0
		for label, lengths in url_stats["Total"]["length"][type]["labels"].iteritems():
			for length in lengths:
				freq = url_stats["Total"]["length"][type]["labels"][length]["freq"]
				total += length*freq
				count += freq
		if count == 0:
			url_stats["Total"]["length"][type]["average"] = 0
		else:
		url_stats["Total"]["length"][type]["average"] = total/float(count)