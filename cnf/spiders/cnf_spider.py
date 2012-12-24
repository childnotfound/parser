# -*- coding: utf-8 -*-
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item, Field
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

import cnf.settings as settings

import copy
import re
import csv
import datetime 

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

class CnfSpider(BaseSpider):
    name = "cnf"
    allowed_domains = ["www.missingkids.org.tw"]
    start_urls = ["http://www.missingkids.org.tw/chinese/focus.php"]

    BASE_URL = "http://www.missingkids.org.tw/chinese/focus.php"
    ID_PARAMS = "?mode=show&temp=0&id="
    
    start_urls = []

    keys = ["id", "name", "sex", "currentAge", "missingAge", "missingDate",\
            "character", "missingRegion", "missingLocation", "missingCause", "avatar"]

    keys_ext = [
            "missingAgeInDays",         # computed from missingAge
            "missingDateInDatetime",    # convert missingDate to Datetime
            "currentAgeInDays",         # computed from missingAgeInDays and missingDateInDatetime
            "missingTotalDays",         # total missing days
            "icon"                      # sex icon for fusion map
            ]

    DAYS_IN_YEAR = 365.25
    DAYS_IN_MONTH = 30.4375 # DAYS_IN_YEAR/12

    for x in range(settings.ID_START,settings.ID_END+1):
        id = str(x)
        start_urls.append(BASE_URL+ID_PARAMS+id)
 
    def __init__(self):
        dispatcher.connect(self.engine_stopped, signals.engine_stopped)

    def parse(self, response):
        hxs = HtmlXPathSelector(response)

        data = hxs.\
        select('//table//td[@width="70%"][@align="left"]//text()').\
        re('\s*(.+[^\s])\s*')

        avatar_url = hxs.\
                select('//table[@width="500"]//img/@src').\
                extract()

        item = CnfItem()

        m = re.match(r".+id=(\d+)",response.url)

        item['id'] = m.group(1)
 
        # the two keys have parsed
        item['name'] = data[0]
        item['sex'] = data[1]
        
        try:
            item['currentAge'] = data[2]
            item['missingAge'] = data[3]
            item['missingDate'] = data[4]
            item['character'] = data[5]
            item['missingRegion'] = data[6]
            item['missingLocation'] = data[7]
            item['missingCause'] = data[8]
        except:
            pass

        item['avatar'] = avatar_url

        return copy.deepcopy([item])


    # missingAge=3 歲 0 月
    # return: days in timedelta, days in integer
    def missingAge_to_days(self, s):
        p=re.compile(r'\s*(\d+)\s*歲\s*(\d+)\s*月\s*')
        m=p.match(s)
        if m:
            d = self.DAYS_IN_YEAR*int(m.group(1)) + self.DAYS_IN_MONTH*int(m.group(2))
            return datetime.timedelta(days=d), int(d)
        else:
            return None

    # missingDate=民國89年6月
    # return: date in datetime 
    def missingDate_to_datetime(self, s):
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
    def compute_currentAge(self, missingDateInDatetime, missingAgeInDays):
        if missingDateInDatetime and missingAgeInDays:
            d = datetime.datetime.now() - missingDateInDatetime + missingAgeInDays
            d = d.days
            y = int(d / self.DAYS_IN_YEAR)
            m = round((d % self.DAYS_IN_YEAR) / self.DAYS_IN_MONTH)
            return (y,m),d
        else: 
            return None

    def engine_stopped(self):
        # sort csv file in order of self.keys[]
        with open(settings.RAW_CSV, 'rb') as csv_file_r:
            reader = csv.reader(csv_file_r)
            columns = zip(*reader)

            csv_sorted = []

            for k in self.keys:
                for col in columns:
                    if col[0] == k:
                        csv_sorted.append(col)

            rows = zip(*csv_sorted)
            rows_ext = []

            # compute the extra keys
            for r in rows[1:]:
                if self.keys[4] in r:
                    continue
                i_missingAge = self.keys.index("missingAge")
                i_missingDate = self.keys.index("missingDate")
                i_currentAge = self.keys.index("currentAge")
                i_sex = self.keys.index("sex")

                d_timedelta = missingDateInDatetime = missingAgeInDays = None
            
                # must be in the order of keys_ext
                if r[i_missingAge]:
                    r_missingAge_to_days = self.missingAge_to_days(r[i_missingAge])
                    if r_missingAge_to_days:
                        d_timedelta, missingAgeInDays = r_missingAge_to_days
                        r += (missingAgeInDays, )

                if r[i_missingDate]:
                    missingDateInDatetime = self.missingDate_to_datetime(r[i_missingDate])
                    if missingDateInDatetime:
                        r += (missingDateInDatetime, )

                if r[i_currentAge] and missingAgeInDays:
                    r_compute_currentAge = self.compute_currentAge(missingDateInDatetime, d_timedelta)
                    if r_compute_currentAge:
                        _, currentAgeInDays = r_compute_currentAge
                        r += (currentAgeInDays, )

                if missingDateInDatetime:
                    d = datetime.datetime.now() - missingDateInDatetime
                    d = datetime.timedelta(d.days)
                    missingTotalDays = int(d.days)
                    r += (missingTotalDays, )

                if r[i_sex]:
                    if (u"男").encode("utf-8") in r[i_sex]:
                        r += ("man", )
                    else:
                        r += ("woman", )

                rows_ext.append(r)

            with open(settings.SORTED_CSV, 'wb') as csv_file_w:
                writer = csv.writer(csv_file_w)
                writer.writerow(self.keys+self.keys_ext)
                writer.writerows(rows_ext)
