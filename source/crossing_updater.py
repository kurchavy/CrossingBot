from crossing import Crossing
from datetime import datetime, timedelta
from pytz import timezone
import asyncio
from bs4 import BeautifulSoup
import requests
import logging

def _get_current_date(tz='Europe/Moscow'):
    return datetime.now().astimezone(timezone(tz))

class CrossingUpdaterFactory:
    def create_updater(self, crs: Crossing):
        return CrossingUpdater(crs, [IntervalCreatorTuTuRu(), IntervalCreatorJson()])

class CrossingUpdater:
    def __init__(self, crs: Crossing, i_creators):
        self.crs = crs
        self.i_creators = i_creators

    def get_timetable(self, date = None):
        for crt in self.i_creators:
            try: 
                logging.debug(f"Trying to get timetable from {crt.__class__.__name__}...")
                tt = crt.get_timetable(date) 
                logging.info(f"Got timetable from {crt.__class__.__name__}")
                return tt
            except:
                logging.exception(f"Fail to get timetable from {crt.__class__.__name__}") 
        logging.error("Unable to get crossing timetable")
        raise ValueError("Fail to get crossing timetable") 

    def update_task(self):
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

            #await asyncio.sleep(30)
     
class IntervalCreatorJson:
    """
    Default Interval creator (using pre-created json files for work-days and weekends)  

    """
    def __init__(self):
        pass

    def get_timetable(self, date = None):
        return []    
            
class IntervalCreatorTuTuRu:
    """
    tutu.ru Interval creator (using BeautifulSoup to parse html)  
    
    """
    def __init__(self):
        pass

    def get_timetable(self, date = None):
        html = self.get_html(45607, 45707, date)
        lst = self.get_oneway_intervals(html, -1, 0)

        html = self.get_html(45707, 45607, date)
        lst += self.get_oneway_intervals(html, 0, 1)

        return self.adjust_intervals(sorted(lst, key=lambda l: l[0]), 7)
    
    def get_html(self, st1 = 45707, st2 = 45607, date = None):
        urladd = "" if date == None else f"&date={date:%d:%m:%y}"
        url = f"https://www.tutu.ru/rasp.php?st1={st1}&st2={st2}" + urladd
        response = requests.get(url)
        logging.debug(f'Got html from {url}')
        return response.text
    
    def get_oneway_intervals(self, html, depcorr = 0, arrcorr = 0):
        soup = BeautifulSoup(html, 'html.parser')
        dep_links = soup.find_all('a', class_= lambda v: v and v.startswith("g-link desktop__depTimeLink"))
        arr_links = soup.find_all('a', class_= lambda v: v and v.startswith("g-link desktop__arrTimeLink"))
        logging.debug(f'Got {len(dep_links)} departures and {len(arr_links)} arrivals from html')
        lst = []
        tod = _get_current_date().date()
        timelast = datetime.strptime("00:00", "%H:%M").time()
        for (d, a) in zip(dep_links, arr_links):
            timedep = datetime.strptime(d.text, "%H:%M").time()
            timearr = datetime.strptime(a.text, "%H:%M").time()

            datedep = tod
            datearr = tod

            if timearr < timedep:
                datearr += timedelta(days=1)
                tod += timedelta(days=1)

            if timedep < timelast:
                datedep += timedelta(days=1)
                datearr += timedelta(days=1)
                tod += timedelta(days=1)

            timelast = timearr

            lst.append([datetime.combine(datedep, timedep) + timedelta(minutes=depcorr), 
                        datetime.combine(datearr, timearr) + timedelta(minutes=arrcorr)])
        
        logging.debug(f'Got {len(lst)} intervals from html')
        return lst
    
    def adjust_intervals(self, ilist, maxgap):
        res = []
        skip = False
        logging.debug(f"Total intervals before adjusting ({maxgap} min): {len(ilist)}")
        for i in range(0, len(ilist) - 1, 1):
            if skip == True:
                skip = False
                continue
            first = ilist[i]
            second = ilist[i + 1]
            if second[0] - first[1] > timedelta(minutes=maxgap):
                res.append(first)
            else:
                res.append([first[0], second[1]])
                skip = True
        logging.debug(f"Total intervals after adjusting: {len(res)}")
        return res

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    crs = Crossing()
    cu = CrossingUpdaterFactory().create_updater(crs)
    cu.update_task()
