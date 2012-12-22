from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector

from cnf.items import CnfItem
import cnf.settings as settings

import copy
import re

class CnfSpider(BaseSpider):
    name = "cnf"
    allowed_domains = ["www.missingkids.org.tw"]
    start_urls = ["http://www.missingkids.org.tw/chinese/focus.php"]

    BASE_URL = "http://www.missingkids.org.tw/chinese/focus.php"
    ID_PARAMS = "?mode=show&temp=0&id="
    
    start_urls = []
    id = None

    for x in range(settings.ID_START,settings.ID_END+1):
        id = str(x)
        start_urls.append(BASE_URL+ID_PARAMS+id)
 
    def parse(self, response):
        hxs = HtmlXPathSelector(response)

        data = hxs.\
        select('//table//td[@width="70%"][@align="left"]//text()').\
        re('\s*(.+[^\s])\s*')

        avatar_url = hxs.\
                select('//img[@width=135][@height=180]/@src').\
                extract()

        item = CnfItem()

        m = re.match(r".+id=(\d+)",response.url)

        item['id'] = m.group(1)
        
        item['name'] = data[0]
        item['sex'] = data[1]
        item['currentAge'] = data[2]
        item['missingAge'] = data[3]
        item['missingDate'] = data[4]
        item['character'] = data[5]
        item['missingRegion'] = data[6]
        item['missingLocation'] = data[7]
        item['missingCause'] = data[8]

        item['avatar'] = avatar_url

        return copy.deepcopy([item])
