# Scrapy settings for cnf project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
import os

BOT_NAME = 'cnf'

SPIDER_MODULES = ['cnf.spiders']
NEWSPIDER_MODULE = 'cnf.spiders'

ID_START = 1
ID_END = 200

RAW_CSV = os.path.expanduser('~/%s_raw.csv' % BOT_NAME) 
SORTED_CSV = os.path.expanduser('~/%s.csv' % BOT_NAME)

FEED_URI = RAW_CSV
FEED_FORMAT = "CSV"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'cnf (+http://www.yourdomain.com)'
