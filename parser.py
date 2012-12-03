# -*- coding: utf-8 -*-
# crawler for childnotfound project 

from HTMLParser import HTMLParser
import urllib2
import sys
import re
import datetime 
import csv

# The keys in keys_utf8[] and keys[] should be synced in the same order.
# Only the first 10 keys in keys[] are retrieved from html crawling.
keys_big5 = []
keys_utf8 = ["","姓名","性別","現在年齡","失蹤年齡","失蹤日期","特徵","失蹤地區","失蹤地點","失蹤原因"]
# keys is in csv header order
keys = [
	"id","name","sex","currentAge","missingAge","missingDate","character","missingRegion","missingLocation",
	"missingCause",
	"avatar", 
	"missingAgeInDays", # computed from missingAge
	"missingDateInDatetime", # convert missingAge to Datetime
	"currentAgeInDays" # computed from missingAgeInDays and missingDateInDatetime
	]

kid = {}
kids = []

baseurl = "http://www.missingkids.org.tw/chinese/focus.php"
parameter = "?mode=show&temp=0&id="
avatar_baseurl="http://www.missingkids.org.tw/miss_focusimages/"

days_in_year = 365.25
days_in_month = 30.4375 # days_in_year/12

# missingAge=3 歲 0 月
# return: days in timedelta, days in integer
def missingAge_to_days(s):
	p=re.compile(r'\s*(\d+)\s*歲\s*(\d+)\s*月\s*')
	m=p.match(s)
	if m:
		d = days_in_year*int(m.group(1)) + days_in_month*int(m.group(2))
		return datetime.timedelta(days=d), int(d)
	else:
		return None

# missingDate=民國89年6月
# return: date in datetime 
def missingDate_to_datetime(s):
	p=re.compile(r'\s*民國\s*(\d+)\s*年\s*(\d+)\s*月\s*')
	m=p.match(s)
	if m:
		# the day is 1 for datetime, should be discard when printing out.
		return datetime.datetime(year=1911+int(m.group(1)),month=int(m.group(2)),day=1)
	else: 
		return None

# current age by computing
# return: (year,month),days
def compute_currentAge(missingDateInDatetime,missingAgeInDays):
	if missingDateInDatetime and missingAgeInDays:
		d = datetime.datetime.now() - missingDateInDatetime + missingAgeInDays
		d = d.days
		y = int(d / days_in_year)
		m = round((d % days_in_year) / days_in_month)
		return (y,m),d
	else: 
		return None

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
	current_key=None
	tags_to_value=None
	stag_count=0
	etag_count=0
	d_timedelta=None

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
				if key and key in data:
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
				self.d_timedelta, kid["missingAgeInDays"] = missingAge_to_days(kid[i])
			
			if i == "missingDate":
				kid["missingDateInDatetime"] = missingDate_to_datetime(kid[i])
			
			if not kid.has_key("currentAgeInDays"):
				if ("missingAgeInDays" in kid) \
					and ("missingDateInDatetime" in kid) \
					and ("currentAgeInDays" not in kid):
					_,kid["currentAgeInDays"] = compute_currentAge(kid["missingDateInDatetime"], self.d_timedelta)
					d_timedelta = None

			self.tags_to_value = None
			self.current_key = None

if __name__ == '__main__':

	v = (2,7,3)
	if sys.version_info < v:
		print "error: this script has to run with python version %s.%s.%s" % v
		sys.exit()

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

	with open('kids.csv', 'wb') as csvfile:
		writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writerow(keys)

		for i in range(int(sys.argv[2])):
			id = i+int(sys.argv[1])

			try:
				response = opener.open(baseurl+parameter+str(id))
			except:
				print "http error, can't access %s" % baseurl
				continue

			html=response.read()
			print "=" * 20
		
			# if the id we're looking for doesn't exist, then the page will be replaced with a list of missing kids.
			# so I detect if 失蹤年齡 in the html to make sure there's only one kid information in the page.
			if keys_big5[3] not in html:
				print "error: failed to get page for id %s, page format not matched!" % id
				continue
			
			kid = {}
			kid["id"] = id

			parser.feed(html)

			# now we have the data by id in kid{}

			kid_csv = []

			# FIXME:
			# There should be a better way to sort a dict by key's order in another list.
			for i in keys:
				for k,v in kid.iteritems():
					#print str(k)+"="+str(v)
					if k == i:
						print v
						kid_csv.append(v)

			writer.writerow(kid_csv)

			# chain kid{} to kids[]
			kids.append(kid.copy())

"""
# to print out all data after crawling
	for i in kids:
		print "=" * 20
		for k,v in i.iteritems():
			print str(k)+"="+str(v)
"""			
