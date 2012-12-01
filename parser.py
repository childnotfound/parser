# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser
import urllib, urllib2
import sys


#keys_utf8 and kid_keys should be synced.
keys_utf8 = ["姓名","性別","現在年齡","失蹤年齡","失蹤日期","特徵","失蹤地區","失蹤地點","失蹤原因"]
keys_big5 = []
for i,v in enumerate(keys_utf8):
	keys_big5.insert(i,unicode(keys_utf8[i],'utf-8','ignore').encode('Big5','ignore'))

kid_keys = ["name","sex","age","lost_age","lost_date","character","area","spot","reason","id","photo_url"]
kid = {}
kids = []

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
	current_key=None
	tags_to_data=None
	stag_count=0
	etag_count=0

	def handle_starttag(self, tag, attrs):
		if self.stag_count == 204:
			kid["photo_url"]=attrs[0][1]
		self.stag_count=self.stag_count+1

	def handle_endtag(self, tag):
		""
			
	def handle_data(self, data):
		data = unicode(data,'Big5','ignore').encode('utf-8','ignore')

		if self.current_key == None:
			for key in keys_utf8:
				if key in data:
					self.current_key = key
					self.tags_to_data = 3
		else:
			self.tags_to_data = self.tags_to_data-1

		if self.tags_to_data == 0:
			i = keys_utf8.index(self.current_key)
			i = kid_keys[i]
			kid[i] = data.strip()
			self.tags_to_data = None
			self.current_key = None

if __name__ == '__main__':

	if len(sys.argv) != 3:
		print "usage: parser.py start_id count"
		sys.exit()

	# instantiate the parser and fed it some HTML
	parser = MyHTMLParser()

	http_handler = urllib2.HTTPHandler(debuglevel=0)
	redirect_handler = urllib2.HTTPRedirectHandler()

	handlers = [http_handler,redirect_handler]

	opener = urllib2.build_opener(http_handler,redirect_handler)
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]

	baseurl = "http://www.missingkids.org.tw/chinese/focus.php"
	parameter = "?mode=show&temp=0&id="

	photo_baseurl="http://www.missingkids.org.tw/miss_focusimages/"

	for i in range(int(sys.argv[2])):
		id = i+int(sys.argv[1])
		response = opener.open(baseurl+parameter+str(id))
		
		html=response.read()
		if keys_big5[3] not in html:
			continue
		
		kid = {}
		kid["id"] = id
		parser.feed(html)
		kids.append(kid.copy())

	for i in kids:
		print "=" * 20
		for k,v in i.iteritems():
			print str(k)+"="+str(v)
