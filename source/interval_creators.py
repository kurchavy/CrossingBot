from datetime import datetime, timedelta
from dateutil import tz
from bs4 import BeautifulSoup
import requests
import logging
import json

class IntervalCreatorJson:
    """
    Default Interval creator (using pre-created json files for work-days and weekends)  

    """
    def __init__(self):
        pass

    def get_timetable(self, date = None):
        if date == None:
            date = datetime.now(tz.gettz("Europe/Moscow")).date()
        fname = "workday.json"
        if date.weekday() > 4:
            fname = "weekend.json"

        with open(fname, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tt = list(
            map(
                lambda t: [
                    datetime.combine(
                        date,
                        datetime.strptime(t[0], "%H:%M:%S").time(),
                        tzinfo=tz.gettz("Europe/Moscow")
                    ),
                    datetime.combine(
                        date,
                        datetime.strptime(t[1], "%H:%M:%S").time(),
                        tzinfo=tz.gettz("Europe/Moscow")
                    ),
                ],
                data,
            )
        )
        return tt

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
        urladd = "" if date == None else f"&date={date:%d.%m.%y}"
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
        tod = datetime.now(tz.gettz("Europe/Moscow")).date()
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

            lst.append(
                [
                    datetime.combine(datedep, timedep, tzinfo=tz.gettz("Europe/Moscow")) + timedelta(minutes=depcorr),
                    datetime.combine(datearr, timearr, tzinfo=tz.gettz("Europe/Moscow")) + timedelta(minutes=arrcorr),
                ]
            )

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
