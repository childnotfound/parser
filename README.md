Parser
======
```
usage: scrapy crawl cnf
setting: edit cnf/spiders/cnf_spider.py, ID_START(default: 1) and ID_END(default: 200).
```

Uploader
======
```
usage: uploader.py [-h] [-f FOLER_ID] -t {ss,csv,ft} csv_file

File uploader for childnotfound project

positional arguments:
  csv_file              The source file in CSV format

optional arguments:
  -h, --help            show this help message and exit
  -f FOLER_ID, --foler_id FOLER_ID
                        the target folder ID on the Google drive
  -t {ss,csv,ft}, --to_file {ss,csv,ft}
                        convert the source format(csv) to target format on the Google drive.                    
                        csv: simply upload the source file                    
                        ft: to fusion table                    
                        ss: to spreadsheet

example: uploader.py -t ss ~/cnf.csv   # the cnf.csv file will be uploadded to Google drive of this application's account.
```

Parsed data
======
- The data will be saved under ~/cnf.csv(sorted, better for uploading) and ~/cnf_raw.csv(raw parsed file)

Requirements
======
- Python 2.7.3 (recommended)
- python-dev, libxml2-dev, libxslt-dev (sudo apt-get install python-dev libxml2-dev libxslt-dev)
- scrapy 1.6, (sudo pip install scrapy)
- Google API client for Python (sudo pip install google-api-python-client)
- OAuth2 client secret file for account application.2132s@gmail.com, get it from API console, save the file in ~/.uploader.secrets
