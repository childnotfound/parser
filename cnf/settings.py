# Scrapy settings for cnf project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'cnf'

SPIDER_MODULES = ['cnf.spiders']
NEWSPIDER_MODULE = 'cnf.spiders'

ID_START = 1
ID_END = 200

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'cnf (+http://www.yourdomain.com)'
