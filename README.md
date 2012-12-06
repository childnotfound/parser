Parser
======
usage: ./parser.py start_id count


Sample output
======
- keys = [
-	"id",			# 1~198 for now
-	"name",			# in Chinese
-	"sex",			# 男生 or 女生
-	"currentAge",	# x 歲 x 月 
-	"missingAge",	# xx 歲 x 月
-	"missingDate",	# 民國xx年x月
-	"character",	# 失蹤前約90公分高、單眼皮....
-	"missingRegion",	# 苗栗縣竹南鎮
-	"missingLocation",	# 巷口
-	"missingCause",		# 迷途走失
-	"avatar", 			# http://www.missingkids.org.tw/miss_focusimages/xxxxx.jpg
-	"missingAgeInDays", 		# computed from missingAge
-	"missingDateInDatetime", 	# convert missingDate to Datetime
-	"currentAgeInDays", 		# computed from missingAgeInDays and missingDateInDatetime
-	"missingTotalDays" 			# total missing days
-	]

Requirements:
======
Python 2.7.3
