from datetime import datetime, timedelta

class Interval:
    def __init__(self, st: datetime, et: datetime):
        self.startTime = st
        self.endTime = et
        self.length = self.get_minutes(et - st)

    def __str__(self) -> str:
        return f"{self.length} min [{self.startTime:'%H:%M'} - {self.endTime:'%H:%M'}]"

    def get_minutes(self, td: timedelta):
        return round((td.seconds) / 60)

    def position_in_interval(self, time_to_check: datetime):
        if time_to_check < self.startTime:
            return (-1, self.get_minutes(self.startTime - time_to_check))
        if time_to_check > self.endTime:
            return (1, 0)
        return (0, self.get_minutes(self.endTime, time_to_check))
