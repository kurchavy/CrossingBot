from datetime import datetime, timedelta
from dateutil import tz
import asyncio
import logging
from interval_creators import IntervalCreatorTuTuRu, IntervalCreatorJson
from crossing_model import Crossing

class CrossingUpdaterFactory:
    def create_updater(self, crs: Crossing):
        return CrossingUpdater(crs, [IntervalCreatorTuTuRu(), IntervalCreatorJson()])

class CrossingUpdaterTestFactory:
    def create_updater(self, crs: Crossing):
        return CrossingUpdater(crs, [IntervalCreatorJson()])

class CrossingUpdater:
    def __init__(self, crs: Crossing, i_creators):
        self.crs = crs
        self.i_creators = i_creators
        self.list_tom = []

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

    def update_cycle(self):
        date_now = datetime.now(tz.gettz("Europe/Moscow"))

        # нужно очистить расписание, если > 03:00 и расписание старое (или его нет)
        if date_now.hour >= 3 and self.crs.date != date_now.date():
            self.crs.clear_intervals()

        # нет расписания
        if self.crs.date == None:
            if len(self.list_tom) != 0:
                # если есть расписание на завтра, загрузить его и стереть
                self.crs.update_intervals(date_now.date(), self.list_tom)
                self.list_tom = []
            else:
                # нет никакого расписания
                self.crs.update_intervals(date_now.date(), self.get_timetable())

        # нужно подгрузить расписание на завтра (еще не загружено)
        if date_now.hour >= 22 and len(self.list_tom) == 0:
            tom = date_now + timedelta(days=1)
            self.list_tom = self.get_timetable(tom)

    async def update_task(self):
        while True:
            self.update_cycle()
            await asyncio.sleep(30)

