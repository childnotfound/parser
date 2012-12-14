# -*- coding: utf-8 -*-
# crawler for childnotfound project 

from HTMLParser import HTMLParser
import urllib
import urllib2
import sys
import re
import datetime 
import csv
import argparse
import os
import json

import pprint
import httplib2
import apiclient.errors
import apiclient.http
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run
from apiclient.http import MediaFileUpload


APP = "parser"

# The keys in keys_utf8[] and keys[] should be synced in the same order.
# Only the first 11 keys in keys[] are retrieved from html crawling.
keys_big5 = []
keys_utf8 = [
	"","姓名","性別","現在年齡","失蹤年齡","失蹤日期","特徵","失蹤地區",\
	"失蹤地點","失蹤原因"]
# keys is in csv header order
keys = [
	"id","name","sex","currentAge","missingAge","missingDate","character",\
	"missingRegion",
	"missingLocation",
	"missingCause",
	"avatar", 
	"missingAgeInDays", # computed from missingAge
	"missingDateInDatetime", # convert missingDate to Datetime
	"currentAgeInDays", # computed from missingAgeInDays and missingDateInDatetime
	"missingTotalDays" # total missing days
	]

kid = {}
kids = []

BASEURL = "http://www.missingkids.org.tw/chinese/focus.php"
PARAMETER = "?mode=show&temp=0&id="
CSVFILE = os.path.expanduser('~/kid.csv')
DRIVE_SHARE="http://goo.gl/RPpGh"

DAYS_IN_YEAR = 365.25
DAYS_IN_MONTH = 30.4375 # DAYS_IN_YEAR/12

# missingAge=3 歲 0 月
# return: days in timedelta, days in integer
def missingAge_to_days(s):
	p=re.compile(r'\s*(\d+)\s*歲\s*(\d+)\s*月\s*')
	m=p.match(s)
	if m:
		d = DAYS_IN_YEAR*int(m.group(1)) + DAYS_IN_MONTH*int(m.group(2))
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
		return datetime.datetime(
				year=1911+int(m.group(1)),
				month=int(m.group(2)),
				day=1)
	else: 
		return None

# current age by computing
# return: (year,month),days
def compute_currentAge(missingDateInDatetime,missingAgeInDays):
	if missingDateInDatetime and missingAgeInDays:
		d = datetime.datetime.now() - missingDateInDatetime + missingAgeInDays
		d = d.days
		y = int(d / DAYS_IN_YEAR)
		m = round((d % DAYS_IN_YEAR) / DAYS_IN_MONTH)
		return (y,m),d
	else: 
		return None

def getCredentials():
	storage_file = os.path.expanduser('~/.%s.creds' % APP)
	storage = Storage(storage_file)
	credentials = storage.get()
	if credentials is None or credentials.invalid == True:
		flow = flow_from_clientsecrets(
			os.path.expanduser('~/.%s.secrets' % APP),
			scope=[
				'https://www.googleapis.com/auth/drive.file',
				'https://www.googleapis.com/auth/fusiontables'
				])
		credentials = run(flow, storage)
	return credentials

def getAuthorizedHttp():
	creds = getCredentials()
	http =  httplib2.Http()
	creds.authorize(http)
	#wrapped_request = http.request

	def _Wrapper(uri, method="GET", body=None, headers=None, **kw):
		print('Req: %s %s' % (uri, method))
		print('Req headers:\n%s' % pprint.pformat(headers))
		print('Req body:\n%s' % body)
		resp, content = wrapped_request(uri, method, body, headers, **kw)
		print('Rsp: %s len=%s %s' % (resp.status, len(content),
			resp['content-type']))
		print('Rsp headers:\n%s' % pprint.pformat(resp))
		print('Rsp body:\n%s' % content)
		print "content type=%s" % type(content)
		return resp, content

	#http.request = _Wrapper
	return http

# read csv and convert to the fusion table
def create_ft(f,name,description="None",isExportable="True"):
    table = {
            "name":name,
            "description":description,
            "isExportable":isExportable,
			"columns":[]
            }

    with open(f, 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        cols = csvreader.next()

        #TODO: sanity check for csv file
        for c in cols:
            d = {"type":"STRING"}
            d["name"] = c
            table["columns"].append(d)

    return table 

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
	current_key=None
	tags_to_value=None
	stag_count=0
	etag_count=0
	d_timedelta=None

	def handle_starttag(self, tag, attrs):
		# the avatar in html source contains 4 elements, 
		# get the value of the first one.
		# <img src="http://www.missingkids.org.tw/miss_focusimages/12527_s.jpg" 
		# width=75 height=100 border=0>
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

			# TODO: 
			# Move the computing stuff after crawling done
			if i == "missingAge":
				self.d_timedelta,kid["missingAgeInDays"] = missingAge_to_days(kid[i])
			
			if i == "missingDate":
				kid["missingDateInDatetime"] = missingDate_to_datetime(kid[i])
			
			if not kid.has_key("currentAgeInDays"):
				if ("missingAgeInDays" in kid) \
					and ("missingDateInDatetime" in kid) \
					and ("currentAgeInDays" not in kid):
					_,kid["currentAgeInDays"] = compute_currentAge(
							kid["missingDateInDatetime"], 
							self.d_timedelta)
					d_timedelta = None

			if not kid.has_key("missingTotalDays"):
				if "missingDateInDatetime" in kid:
					d = datetime.datetime.now() - kid["missingDateInDatetime"]
					d = datetime.timedelta(d.days)
					kid["missingTotalDays"] = int(d.days)

			self.tags_to_value = None
			self.current_key = None

if __name__ == '__main__':

	v = (2,7,3)
	if sys.version_info < v:
		print "error: this script has to run with python version %s.%s.%s" % v
		print "error: 2.7.1 and 2.7.2 are known to fail this script."
		sys.exit(1)


	# argument parsing
	arg_parser = argparse.ArgumentParser(
			description='HTML parser for childnotfound project, Taiwan.')
	arg_parser.add_argument('--start', type=int, required=True,
			help='the start id')
	arg_parser.add_argument('--count', type=int, required=True,
			help='total ids to get')
	arg_parser.add_argument('--toss', action="store_true", default=False, 
			required=False,
			help='if upload parsed data to this application\'s Google drive share \
					in spreadsheet format at %s' % DRIVE_SHARE)
	arg_parser.add_argument('--toft', action="store_true", default=False, 
			required=False,
			help='if upload parsed data to this application\'s Google drive share \
					in fusion table at %s' % DRIVE_SHARE)

	args = arg_parser.parse_args()

	http_handler = urllib2.HTTPHandler(debuglevel=0)
	opener = urllib2.build_opener(http_handler)
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]

	# the page is in big5, make keys in big5 for comparision.
	for i,v in enumerate(keys_utf8):
		keys_big5.insert(
				i,
				unicode(keys_utf8[i],'utf-8','ignore').encode('Big5','ignore'))

	html_parser = MyHTMLParser()

	with open(CSVFILE, 'wb') as csvfile:
		writer = csv.writer(
				csvfile, 
				delimiter=',', 
				quotechar='"', 
				quoting=csv.QUOTE_MINIMAL)

		writer.writerow(keys)

		for i in range(args.count):
			id = i+args.start

			try:
				response = opener.open(BASEURL+PARAMETER+str(id))
			except:
				print "http error, can't access %s" % BASEURL
				continue

			html=response.read()
			print "=" * 20
		
			# if the id we're looking for doesn't exist, 
			# then the page will be replaced with a list of missing kids.
			# so I detect if 失蹤年齡 in the html to make sure 
			# there's only one kid information in the page.
			if keys_big5[3] not in html:
				print "error: failed to get page for id %s," % id,
				print "page format not matched!"
				continue
			
			kid = {}
			kid["id"] = id

			html_parser.feed(html)

			# now we have the data by id in kid{}

			kid_csv = []

			# FIXME:
			# There should be a better way to sort a dict 
			# by key's order in another list.
			for i in keys:
				for k,v in kid.iteritems():
					#print str(k)+"="+str(v)
					if k == i:
						print v
						kid_csv.append(v)

			writer.writerow(kid_csv)

			# chain kid{} to kids[]
			kids.append(kid.copy())

	http = getAuthorizedHttp()

	DISCOVERYURL= \
			'https://www.googleapis.com/discovery/v1/apis/{api}/{apiVersion}/rest'
	ROOT_FOLDER = "0BzpFOxkB8J_zNmU0SktlTFBveHM"
	TITLE = "childnotfound: %d to %d" % (args.start, args.start+args.count-1)

	if args.toss:
		MIME = "text/csv"

		PARENTS=[{
			"kind":"drive#fileLink",
			"id":ROOT_FOLDER}]

		body = {
				'title':TITLE,
				'mimeType':MIME,
				'parents':PARENTS}

		drive = build('drive', 'v2',
				discoveryServiceUrl=DISCOVERYURL, http=http)

		media_body = MediaFileUpload(CSVFILE,mimetype=MIME,resumable=True)

		try:
			ss_file = drive.files().insert(
					body=body,
					media_body=media_body,
					convert=True	# so csv will be converted to spreadsheet
					).execute()

			print "The spreadsheet is located at: %s" % ss_file["alternateLink"]

		except apiclient.errors.HttpError, e:
			print 'http error:',e

	print "=" * 20

	if args.toft:
		ftable = build('fusiontables', 'v1',
				discoveryServiceUrl=DISCOVERYURL, http=http)
		body = create_ft(CSVFILE,TITLE)

        # TODO:
        # move ft to opendata folder
        # table is created, get tableId
		table_id = ftable.table().insert(body=body).execute()["tableId"]
		print "Fusion table id: %s" % table_id

		params = urllib.urlencode({'isStrict': "false"})
		URI = "https://www.googleapis.com/upload/fusiontables/v1/tables/%s/import?%s" % (table_id, params)
		METHOD = "POST"
		
		"""
		with open(CSVFILE, 'rb') as csvfile:
			csvreader = csv.reader(csvfile)
			print csvreader
			print dir(csvreader)
		"""
		with open(CSVFILE) as csvfile:
			# ignore the columns
			csvfile.readline()
			# get the rows
			rows = csvfile.read()
			utf8_body = rows.decode('utf-8').encode('utf-8')
			response, content = http.request(URI.encode('utf-8'), METHOD, body=utf8_body)
			content = json.loads(content)
			print "Imported rows: %s" % content["numRowsReceived"]

		# URL for new look 
		FT_URL = "https://www.google.com/fusiontables/data?docid=%s" % table_id
		print "The fusion table is located at: %s" % FT_URL
