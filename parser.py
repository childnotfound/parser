# -*- coding: utf-8 -*-
# crawler for childnotfound project 

from HTMLParser import HTMLParser
import urllib, urllib2
import sys
import re
import datetime 

# the first 9 keys in keys_utf8 and keys should be synced in the same order.
# CurrentAge can be computed from missingAge and missingDate
keys_big5 = []
keys_utf8 = ["姓名","性別","現在年齡","失蹤年齡","失蹤日期","特徵","失蹤地區","失蹤地點","失蹤原因"]
keys = [
	"name","sex","currentAge","missingAge","missingDate","character","missingRegion","missingLocation",
	"missingCause","avatar","id","missingAgeInDays","missingDateInDatetime","currentAgeByComputing"
	]

kid = {}
kids = []

baseurl = "http://www.missingkids.org.tw/chinese/focus.php"
parameter = "?mode=show&temp=0&id="
photo_baseurl="http://www.missingkids.org.tw/miss_focusimages/"

# missingAge=3 歲 0 月, index=3
def missingAge_to_days(s):
	print s
	days_in_year = 365.25
	days_in_month = 30.4375 # days_in_year/12
	p=re.compile(r'\s*(\d+)\s*歲\s*(\d+)\s*月\s*')
	m=p.match(s)
	print m
	d = days_in_year*int(m.group(1)) + days_in_month*int(m.group(2))
	return datetime.timedelta(days=d)

# missingDate=民國89年6月, index=4
def missingDate_to_datetime(s):
	p=re.compile(r'\s*民國\s*(\d+)\s*年\s*(\d+)\s*月\s*')
	m=p.match(s)
	# the day is 1 for datetime, should be discard when printing out.
	return datetime.date(year=1911+int(m.group(1)),month=int(m.group(2)),day=1)

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
	current_key=None
	tags_to_value=None
	stag_count=0
	etag_count=0

	def handle_starttag(self, tag, attrs):
		# the avatar in html source contains 4 elements, get the value of the first one.
		# <img src="http://www.missingkids.org.tw/miss_focusimages/12527_s.jpg" width=75 height=100 border=0>
		if len(attrs) == 4:
			if "miss_focusimages" in attrs[0][1]:
				kid["avatar"]=attrs[0][1]

	def handle_endtag(self, tag):
		""
			
	def handle_data(self, data):
		data = unicode(data,'Big5','ignore').encode('utf-8','ignore')

		# the key and value pairs for kid's information
		# the value is 3 tags after key
		if self.current_key == None:
			for key in keys_utf8:
				if key in data:
					self.current_key = key
					self.tags_to_value = 3
		else:
			self.tags_to_value = self.tags_to_value-1

		# the value found
		if self.tags_to_value == 0:
			i = keys_utf8.index(self.current_key)
			i = keys[i]
			kid[i] = data.strip()
			if i == "missingAge":
				kid["missingAgeInDays"] = missingAge_to_days(kid[i])
			
			if i == "missingDate":
				kid["missingDateInDatetime"] = missingDate_to_datetime(kid[i])

			self.tags_to_value = None
			self.current_key = None

if __name__ == '__main__':

	if len(sys.argv) != 3:
		print "usage: %s start_id count" % sys.argv[0]
		sys.exit()

	http_handler = urllib2.HTTPHandler(debuglevel=0)
	opener = urllib2.build_opener(http_handler)
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]

	# the page is in big5, make keys in big5 for comparision.
	for i,v in enumerate(keys_utf8):
		keys_big5.insert(i,unicode(keys_utf8[i],'utf-8','ignore').encode('Big5','ignore'))

	
	parser = MyHTMLParser()

	for i in range(int(sys.argv[2])):
		id = i+int(sys.argv[1])
		response = opener.open(baseurl+parameter+str(id))
		
		html=response.read()
	
		# if the id we're looking for doesn't exist, then the page will be replaced with a list of missing kids.
		# so I detect if 失蹤年齡 in the html to make sure there's only one kid information in the page.
		if keys_big5[3] not in html:
			continue
		
		kid = {}
		kid["id"] = id

		parser.feed(html)

		print "=" * 20
		for k,v in kid.iteritems():
			print str(k)+"="+str(v)

		kids.append(kid.copy())

"""
# to print out all data after crawling
	for i in kids:
		print "=" * 20
		for k,v in i.iteritems():
			print str(k)+"="+str(v)
"""			
