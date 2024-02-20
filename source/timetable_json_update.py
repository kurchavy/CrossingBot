from datetime import datetime, timedelta
from pytz import timezone, UTC
import json
from crossing import IntervalCreatorTuTuRu

# export to json
ic = IntervalCreatorTuTuRu()
tt = ic.get_timetable(datetime(2024, 2, 23))
ltimes = list(map(lambda t: [t[0].time(), t[1].time()], tt))
with open('weekend.json', 'w', encoding='utf-8') as f:
    json.dump(ltimes, f, indent=4, sort_keys=True, default=str)

tt = ic.get_timetable(datetime(2024, 2, 21))
ltimes = list(map(lambda t: [t[0].time(), t[1].time()], tt))
with open('workday.json', 'w', encoding='utf-8') as f:
    json.dump(ltimes, f, indent=4, sort_keys=True, default=str)