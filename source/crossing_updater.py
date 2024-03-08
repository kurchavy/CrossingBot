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

    async def get_timetable(self, date = None):
        for crt in self.i_creators:
            name = crt.__class__.__name__
            try: 
                logging.debug(f"Trying to get timetable from {name}...")
                tt = await crt.get_timetable(date) 
                logging.info(f"Got timetable from {name}")
                return tt
            except:
                logging.exception(f"Fail to get timetable from {name}") 
        logging.error("Unable to get crossing timetable")
        raise ValueError("Fail to get crossing timetable") 

    async def update_cycle(self):
        date_now = datetime.now(tz.gettz("Europe/Moscow"))

        # Расписание на сегодня не загружено
        if self.crs.date == None:
            logging.debug("No today timetable. Trying to acquire")
            rsp = await self.get_timetable()
            self.crs.update_intervals(date_now.date(), rsp)
            logging.debug("Today timetable uploded to crossing model")

        # Сменилась дата и время > 03:00
        if (date_now.date() - self.crs.date).days > 0 and date_now.hour >= 3:
            logging.debug("Time to upload new timetable. Trying to acquire")
            rsp = await self.get_timetable()
            self.crs.clear_intervals()
            self.crs.update_intervals(date_now.date(), rsp)
            logging.debug("New timetable uploded to crossing model")
        

    async def update_task(self):
        while True:
            await self.update_cycle()
            await asyncio.sleep(300)

