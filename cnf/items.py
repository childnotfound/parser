# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class CnfItem(Item):
    # define the fields for your item here like:
    id = Field()
    name = Field()
    sex = Field()
    currentAge = Field()
    missingAge = Field()
    missingDate = Field()
    character = Field()
    missingRegion = Field()
    missingLocation = Field()
    missingCause = Field()
    avatar = Field()
