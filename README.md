Parser
======
```
usage: parser.py [-h] --start START --count COUNT [--toss] [--toft]

HTML parser for childnotfound project, Taiwan.

optional arguments:
  -h, --help     show this help message and exit
  --start START  the start id
  --count COUNT  total ids to get
  --toss         if upload parsed data to this application's Google drive
                 share in spreadsheet format at http://goo.gl/RPpGh
  --toft         if upload parsed data to this application's Google drive
                 share in fusion table at http://goo.gl/RPpGh
```

Parsed data
======
```
keys = [
   "id",                # 1~198 for now
   "name",              # in Chinese
   "sex",               # 男生 or 女生
   "currentAge",        # x 歲 x 月 
   "missingAge",        # xx 歲 x 月
   "missingDate",       # 民國xx年x月
   "character",         # 失蹤前約90公分高、單眼皮....
   "missingRegion",     # 苗栗縣竹南鎮
   "missingLocation",   # 巷口
   "missingCause",      # 迷途走失
   "avatar",            # http://www.missingkids.org.tw/miss_focusimages/xxxxx.jpg
   "missingAgeInDays",      # computed from missingAge
   "missingDateInDatetime", # convert missingDate to Datetime
   "currentAgeInDays",      # computed from missingAgeInDays and missingDateInDatetime
   "missingTotalDays"       # total missing days
   ]
```

Requirements
======
- Python 2.7.3
- Google API Python Client (sudo pip install --upgrade google-api-python-client)
- OAuth2 client secret file for account application.2132s@gmail.com, get it from API console, save the file in ~/.parser.secrets
