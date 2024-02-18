from datetime import datetime, timedelta
from pytz import timezone

def _timeFromStr(str):
    return datetime.combine(datetime.min, datetime.strptime(str, "%H:%M").time())

def _getMinutes(t):
    return round((t - datetime.min).total_seconds() / 60)

class Interval:
    def __init__(self, st, et):
        self.startTime = st
        self.endTime = et

        self.startMinutes = _getMinutes(self.startTime)
        self.endMinutes = _getMinutes(self.endTime)

        self.length = self.endMinutes - self.startMinutes

    def __str__(self) -> str:
        return f"{self.length} min [{self.startTime:'%H:%M'} - {self.endTime:'%H:%M'}] ({self.startMinutes} - {self.endMinutes})"

    def positionInInterval(self, minutes):
        if minutes < self.startMinutes:
            return (-1, self.startMinutes - minutes)
        if minutes > self.endMinutes:
            return (1, 0)
        return (0, self.endMinutes - minutes)


class Crossing:
    def __init__(self, date = None, intervals = None, tz='Europe/Moscow'):
        self.timezone = tz
        self.clear_intervals()
        if intervals != None:
            self.update_intervals(date, intervals)

    def clear_intervals(self):
        self.intervals = []
        self.date = None

    def update_intervals(self, date, intervals):
        lt = datetime.min
        temp_intervals = []
        for (s, e) in intervals:
            st = _timeFromStr(s)
            et = _timeFromStr(e)

            if lt > st and st.hour <= 3:
                st += timedelta(days=1)
                et += timedelta(days=1)

            if st > et and st.hour >= 23 and et.hour <= 3:
                et += timedelta(days=1)

            if et <= st:
                raise ValueError(f"EndTime [{et:'%H:%M'}] should be later then StartTime [{st:'%H:%M'}]")

            if st <= lt:
                raise ValueError(f"StartTime [{st:'%H:%M'}] should be later then prev EndTime [{lt:'%H:%M'}]")

            temp_intervals.append(Interval(st, et))
            lt = et
        self.intervals = temp_intervals
        self.date = date

    def convertTime(self, curTime):
        return datetime.combine(datetime.min, curTime.astimezone(timezone(self.timezone)).time())

    def getState(self, curTime, period = 60):
        temp_intervals = self.intervals.copy()

        if len(temp_intervals) == 0:
            return ['Не найдено расписание работы переезда']
        res = []
        value = self.convertTime(curTime)
        val = value
        if value.hour < 3:
            val += timedelta(days=1)

        for interval in temp_intervals:
            (r, t) = interval.positionInInterval(_getMinutes(val))
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
            (r, t) = temp_intervals[0].positionInInterval(_getMinutes(value))
            res.append(f"Переезд открыт. Закроется в {temp_intervals[0].startTime:%H:%M} (через {t} мин) на {temp_intervals[0].length} мин")
        return res