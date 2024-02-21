import logging
from datetime import datetime
from dateutil import tz
from interval import Interval

class Crossing:
    def __init__(self, date=None, intervals=None, tzm="Europe/Moscow"):
        self.timezone = tz.gettz(tzm)
        self.clear_intervals()
        if intervals != None:
            self.update_intervals(date, intervals)

    def clear_intervals(self):
        self.intervals = []
        self.date = None
        logging.debug(f"Cleared crossing interval data")

    def update_intervals(self, date, intervals):
        logging.debug(f"Updating crossing interval data for {date:%d.%m.%y}")
        temp_intervals = []
        for s, e in intervals:
            temp_intervals.append(Interval(s, e))
        self.intervals = temp_intervals
        self.date = date
        logging.info(f"Updated crossing intervals for {self.date:%d.%m.%y}: added {len(self.intervals)} intervals")

    def _compute_state(self, time_to_check: datetime, period=60):
        logging.debug(f"Requested Crossing state for {time_to_check} (period = {period})")
        temp_intervals = self.intervals.copy()

        res = []
        if len(temp_intervals) == 0:
            return ["Не найдено расписание работы переезда"]

        for iv in temp_intervals:
            (r, t) = iv.position_in_interval(time_to_check)
            if r == -1:
                if t > period and len(res) != 0:
                    break
                if len(res) == 0:
                    res.append(f"Переезд открыт. Закроется в {iv.startTime:%H:%M} (через {self._min_to_str(t)}) на {iv.length} мин")
                else:
                    res.append(f"Затем закроется в {iv.startTime:%H:%M} (через {self._min_to_str(t)}) на {iv.length} мин")
            if r == 0:
                res.append(f"Переезд закрыт. Откроется в {iv.endTime:'%H:%M'} (через {self._min_to_str(t)})")
            if r == 1:
                continue
        if len(res) == 0:
            (r, t) = temp_intervals[0].position_in_interval(time_to_check)
            res.append(f"Переезд открыт. Закроется в {temp_intervals[0].startTime:%H:%M} (через {self._min_to_str(t)}) на {temp_intervals[0].length} мин")
        return res

    def _min_to_str(self, t):
        if t < 60:
            return f"{t} мин"
        return f"{t // 60} ч {t % 60} мин"

    def get_current_state(self, period=60):
        return self._compute_state(datetime.now(self.timezone), period)

    def get_state(self, time_str: str, period=60):
        tod = datetime.now(self.timezone)
        time = datetime.combine(tod.date(), datetime.strptime(time_str, "%H:%M").time(), tzinfo=self.timezone)
        return self._compute_state(time, period)
