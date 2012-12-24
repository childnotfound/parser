#!/usr/bin/env python
# -*- coding: utf-8 -*-
# crawler for childnotfound project 

import urllib
import sys
import csv
import argparse
from argparse import RawTextHelpFormatter
import os
import json
import pprint

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger( __name__ )

import httplib2
import apiclient.errors
import apiclient.http
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run
from apiclient.http import MediaFileUpload

APP = os.path.splitext(sys.argv[0])[0]

def getCredentials():
    storage_file = os.path.expanduser('~/.%s.creds' % APP)
    storage = Storage(storage_file)
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
        flow = flow_from_clientsecrets(
            os.path.expanduser('~/.%s.secrets' % APP),
            scope=[
                # if using /drive.file instead of /drive,
                # then the fusion table is not seen by drive.files.list()
                # also, drive.parents.insert() fails.
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/fusiontables'
                ])
        credentials = run(flow, storage)
    return credentials

def getAuthorizedHttp():
    creds = getCredentials()
    http =  httplib2.Http()
    creds.authorize(http)
    wrapped_request = http.request

    def _Wrapper(uri, method="GET", body=None, headers=None, **kw):
        logger.debug('Req: %s %s' % (uri, method))
        logger.debug('Req headers:\n%s' % pprint.pformat(headers))
        logger.debug('Req body:\n%s' % pprint.pformat(body))
        resp, content = wrapped_request(uri, method, body, headers, **kw)
        logger.debug('Rsp headers:\n%s' % pprint.pformat(resp))
        logger.debug('Rsp body:\n%s' % pprint.pformat(content))
        return resp, content

    http.request = _Wrapper
    return http

# read csv and convert to the fusion table
def create_csv_cols(f,name,description="None",isExportable="True"):
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
            if c == "missingRegion":
                d = {"type":"LOCATION"}
            else:
                d = {"type":"STRING"}
            d["name"] = c
            table["columns"].append(d)

    return table 


if __name__ == '__main__':
    # argument parsing
    arg_parser = argparse.ArgumentParser(
            description='File uploader for childnotfound project',
            formatter_class=RawTextHelpFormatter)

    arg_parser.add_argument('csv_file', help='The source file in CSV format')

    DEFAULT_GD_FOLDER = "0BzpFOxkB8J_zNmU0SktlTFBveHM"
    arg_parser.add_argument('-f', '--folder_id', default=DEFAULT_GD_FOLDER, help='the target folder ID on the Google drive')

    arg_parser.add_argument('-t', '--to_file', choices={"csv","ft","ss"}, required=True,
            help='convert the source format(csv) to target format on the Google drive.\
                    \rcsv: simply upload the source file\
                    \rft: to fusion table\
                    \rss: to spreadsheet')

    args = arg_parser.parse_args()
 
    logger.debug(args)

    # sanity check on source csv file
    DELIMITER = ','
    with open(os.path.expanduser(args.csv_file), 'rb') as csv_file:
        try:
            dialect = csv.Sniffer().sniff(csv_file.readline())
            if dialect.delimiter != DELIMITER:
                raise csv.Error("The delimiter of the source csv file is not '%s'" % DELIMITER)
            csv_file.seek(0)
        except csv.Error,e:
            logger.error("CSV error: %s" % e)
            raise 


    # http oauth2
    http = getAuthorizedHttp()

    DISCOVERY_URL= \
            'https://www.googleapis.com/discovery/v1/apis/{api}/{apiVersion}/rest'

    # build the service
    drive = build('drive', 'v2',
            discoveryServiceUrl=DISCOVERY_URL, http=http)

    about = drive.about().get().execute()
    root_folder = about['rootFolderId']

    TITLE = "childnotfound"

    if args.to_file == "ss" or args.to_file == "csv":
        MIME = "text/csv"

        PARENTS=[{
            "kind":"drive#fileLink",
            "id":args.folder_id}]

        body = {
                'title':TITLE,
                'mimeType':MIME,
                'parents':PARENTS}

        media_body = MediaFileUpload(args.csv_file, mimetype=MIME, resumable=True)

        try:
            ss_file = drive.files().insert(
                    body=body,
                    media_body=media_body,
                    # so csv will be converted to spreadsheet
                    convert=True if args.to_file == "ss" else False
                    ).execute()

            logger.info("The spreadsheet is located at: %s" % ss_file["alternateLink"])

        except apiclient.errors.HttpError, e:
            logger.error('http error:', e)

    if args.to_file == 'ft':
        ftable = build('fusiontables', 'v1',
                discoveryServiceUrl=DISCOVERY_URL, http=http)
        body = create_csv_cols(args.csv_file, TITLE)
        logger.debug(body)

        # table columns are created, get tableId
        response = ftable.table().insert(body=body).execute()
        table_id = response["tableId"]
        logger.debug(response)

        # move to target folder
        new_parent = {'id': args.folder_id}

        try:
            drive.parents().insert(fileId=table_id, body=new_parent).execute()
        except apiclient.errors.HttpError, error:
            logger.error('An error occurred: %s' % error)

        # remove from root folder
        try:
            drive.parents().delete(fileId=table_id, parentId=root_folder).execute()
        except apiclient.errors.HttpError, error:
            logger.error('http error: %s' % error)


        # export csv rows to the fusion table
        params = urllib.urlencode({'isStrict': "false"})
        URI = "https://www.googleapis.com/upload/fusiontables/v1/tables/%s/import?%s" % (table_id, params)
        METHOD = "POST"
        
        with open(args.csv_file) as csvfile:
            # ignore the columns
            csvfile.readline()
            # get the rows
            rows = csvfile.read()
            # weird issue here: the URI should be encoded with UTF-8 if body is UTF-8 too.
            utf8_body = rows.decode('utf-8').encode('utf-8')
            response, content = http.request(URI.encode('utf-8'), METHOD, body=utf8_body)
            content = json.loads(content)
            logger.debug(response)
            logger.debug(content)

        # URL for new look 
        FT_URL = "https://www.google.com/fusiontables/data?docid=%s" % table_id
        logger.info("The fusion table is located at: %s" % FT_URL)
