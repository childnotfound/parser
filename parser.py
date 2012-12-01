# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser
import urllib, urllib2

#keys_utf8 and kid_keys should be synced.
keys_utf8 = ["姓名","性別","現在年齡","失蹤年齡","失蹤日期","特徵","失蹤地區","失蹤地點","失蹤原因"]
kid_keys = ["name","sex","age","lost_age","lost_date","character","area","spot","reason","id","photo_url"]
kid = {}
kids = []

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
	current_key=None
	tags_to_data=None

	def handle_starttag(self, tag, attrs):
		""
			
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

# instantiate the parser and fed it some HTML
parser = MyHTMLParser()

http_handler = urllib2.HTTPHandler(debuglevel=0)
redirect_handler = urllib2.HTTPRedirectHandler()

handlers = [http_handler,redirect_handler]

opener = urllib2.build_opener(http_handler,redirect_handler)
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

baseurl = "http://www.missingkids.org.tw/chinese/focus.php"
parameter = "?mode=show&temp=0&id="

for i in range(10):
	id = i+90
	kid["id"] = id
	response = opener.open(baseurl+parameter+str(id))
	
	print response.code

	html=response.read()

	parser.feed(html)

	for k,v in kid.iteritems():
		print str(k)+"="+str(v)

	kids.append(kid)

