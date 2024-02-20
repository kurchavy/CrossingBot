from datetime import datetime, timedelta
from pytz import timezone, UTC
import asyncio
import logging
from interval_creators import IntervalCreatorTuTuRu, IntervalCreatorJson

def _get_current_date(tz='Europe/Moscow'):
    return datetime.now().astimezone(timezone(tz))

class Interval:
    def __init__(self, st: datetime, et: datetime):
        self.startTime = st
        self.endTime = et
        self.length = self.get_minutes(et, st)

    def __str__(self) -> str:
        return f"{self.length} min [{self.startTime:'%H:%M'} - {self.endTime:'%H:%M'}]"
    
    def get_minutes(self, t1: datetime, t2: datetime):
        return round(((t1.replace(tzinfo=UTC) - t2.replace(tzinfo=UTC)).seconds) / 60)

    def position_in_interval(self, tm: datetime):
        if tm.replace(tzinfo=UTC) < self.startTime.replace(tzinfo=UTC):
            return (-1, self.get_minutes(self.startTime, tm))
        if tm.replace(tzinfo=UTC) > self.endTime.replace(tzinfo=UTC):
            return (1, 0)
        return (0, self.get_minutes(self.endTime, tm))
    
class Crossing:
    def __init__(self, date = None, intervals = None, tz='Europe/Moscow'):
        self.timezone = tz
        self.clear_intervals()
        if intervals != None:
            self.update_intervals(date, intervals)

    def clear_intervals(self):
        self.intervals = []
        self.date = None
        logging.debug(f'Cleared Crossing interval data')

    def update_intervals(self, date, intervals):
        logging.debug(f'Updating Crossing interval data for {date:%d.%m.%y}')
        lt = datetime.min
        temp_intervals = []
        for (s, e) in intervals:
            temp_intervals.append(Interval(s, e))
            lt = e
        self.intervals = temp_intervals
        self.date = date
        logging.info(f'Updated Crossing interval data for {self.date:%d.%m.%y}: added {len(self.intervals)} intervals')

    def get_state(self, loc_time : datetime, period = 60):
        curTime = loc_time.astimezone(timezone(self.timezone))
        logging.debug(f'Requested Crossing state for {curTime}')
        temp_intervals = self.intervals.copy()

        if len(temp_intervals) == 0:
            return ['Не найдено расписание работы переезда']
        res = []

        for interval in temp_intervals:
            (r, t) = interval.position_in_interval(curTime)
            if r == -1:
                if t > period and len(res) != 0:
                    break
                if len(res) == 0:
                    res.append(f"Переезд открыт. Закроется в {interval.startTime:%H:%M} (через {t} мин) на {interval.length} мин")
                else:
                    res.append(f"Затем закроется в {interval.startTime:%H:%M} (через {t} мин) на {interval.length} мин")
            if r == 0:
                res.append(f"Переезд закрыт. Откроется в {interval.endTime:'%H:%M'} (через {t} мин)")
            if r == 1:
                continue
        if len(res) == 0:
            (r, t) = temp_intervals[0].position_in_interval(curTime)
            res.append(f"Переезд открыт. Закроется в {temp_intervals[0].startTime:%H:%M} (через {t} мин) на {temp_intervals[0].length} мин")
        return res

class CrossingUpdaterFactory:
    def create_updater(self, crs: Crossing):
        return CrossingUpdater(crs, [IntervalCreatorTuTuRu(), IntervalCreatorJson()])

class CrossingUpdater:
    def __init__(self, crs: Crossing, i_creators):
        self.crs = crs
        self.i_creators = i_creators

    def get_timetable(self, date = None):
        for crt in self.i_creators:
            name = crt.__class__.__name__
            try: 
                logging.debug(f"Trying to get timetable from {name}...")
                tt = crt.get_timetable(date) 
                logging.info(f"Got timetable from {name}")
                return tt
            except:
                logging.exception(f"Fail to get timetable from {name}") 
        logging.error("Unable to get crossing timetable")
        raise ValueError("Fail to get crossing timetable") 

    async def update_task(self):
        list_tom = []
        while True:
            date_now = _get_current_date()

            # нужно очистить расписание, если > 03:00 и расписание старое (или его нет) 
            if date_now.hour >= 3 and self.crs.date != date_now.date():
                self.crs.clear_intervals()

            # нет расписания
            if self.crs.date == None:
                if len(list_tom) != 0:
                    # если есть расписание на завтра, загрузить его и стереть
                    self.crs.update_intervals(date_now.date(), list_tom)
                    list_tom = []
                else:
                    # нет никакого расписания
                    self.crs.update_intervals(date_now.date(), self.get_timetable())

            # нужно подгрузить расписание на завтра (еще не загружено)
            if date_now.hour >= 22 and len(list_tom) == 0:
                tom = date_now + timedelta(days=1)
                list_tom = self.get_timetable(tom)
            
            #return
            await asyncio.sleep(30)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
       
    crs = Crossing()
    cu = CrossingUpdaterFactory().create_updater(crs)
    cu.update_task()
    print(crs.get_state(_get_current_date()))
