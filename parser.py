# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser
import urllib, urllib2
import sys


#keys_utf8 and keys should be synced.
keys_utf8 = ["姓名","性別","現在年齡","失蹤年齡","失蹤日期","特徵","失蹤地區","失蹤地點","失蹤原因"]
keys_big5 = []

keys = ["name","sex","age","lost_age","lost_date","character","area","spot","reason","id","photo_url"]
kid = {}
kids = []

baseurl = "http://www.missingkids.org.tw/chinese/focus.php"
parameter = "?mode=show&temp=0&id="
photo_baseurl="http://www.missingkids.org.tw/miss_focusimages/"

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
	current_key=None
	tags_to_data=None
	stag_count=0
	etag_count=0

	def handle_starttag(self, tag, attrs):
		# the photo_url in html source, 4 elements, get the value of the first one.
		# <img src="http://www.missingkids.org.tw/miss_focusimages/12527_s.jpg" width=75 height=100 border=0>
		if len(attrs) == 4:
			if "miss_focusimages" in attrs[0][1]:
				kid["photo_url"]=attrs[0][1]
			self.stag_count=0

	def handle_endtag(self, tag):
		""
			
	def handle_data(self, data):
		data = unicode(data,'Big5','ignore').encode('utf-8','ignore')

		# the key and value pairs for kid's name,sex,age,etc
		# the value is 3 tags after key
		if self.current_key == None:

			for key in keys_utf8:
				if key in data:
					self.current_key = key
					self.tags_to_data = 3
		else:
			self.tags_to_data = self.tags_to_data-1

		if self.tags_to_data == 0:
			i = keys_utf8.index(self.current_key)
			i = keys[i]
			kid[i] = data.strip()
			self.tags_to_data = None
			self.current_key = None

if __name__ == '__main__':

	if len(sys.argv) != 3:
		print "usage: %s start_id count" % sys.argv[0]
		sys.exit()

	parser = MyHTMLParser()
	http_handler = urllib2.HTTPHandler(debuglevel=0)
	opener = urllib2.build_opener(http_handler)
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]

	for i,v in enumerate(keys_utf8):
		keys_big5.insert(i,unicode(keys_utf8[i],'utf-8','ignore').encode('Big5','ignore'))

	for i in range(int(sys.argv[2])):
		id = i+int(sys.argv[1])
		response = opener.open(baseurl+parameter+str(id))
		
		html=response.read()
		if keys_big5[3] not in html:
			continue
		
		kid = {}
		kid["id"] = id
		parser.feed(html)

		print "=" * 20
		for k,v in kid.iteritems():
			print str(k)+"="+str(v)

		kids.append(kid.copy())

#	for i in kids:
#		print "=" * 20
#		for k,v in i.iteritems():
#			print str(k)+"="+str(v)
