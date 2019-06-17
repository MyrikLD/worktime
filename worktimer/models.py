from datetime import datetime, timedelta, date
from typing import Tuple, List

from django.db import models
from django.db.models import QuerySet


class Wifi(models.Model):
    class State:
        UNKNOWN = 0
        WORK = 1
        HOME = 2

        CHOICES = [
            (UNKNOWN, 'Unknown'),
            (WORK, 'Work'),
            (HOME, 'Home'),
        ]

    essid = models.CharField(max_length=40)
    bssid = models.CharField(max_length=17)
    state = models.IntegerField(choices=State.CHOICES, default=State.WORK)

    @classmethod
    def from_conf(cls, conf: dict) -> 'Wifi':
        if conf['access_point'] == 'Not-Associated':
            itm, created = Wifi.objects.get_or_create(essid='')
            return itm
        w, created = Wifi.objects.get_or_create(
            essid=conf['essid'],
            bssid=conf['access_point'],
            defaults={
                'state': Wifi.State.UNKNOWN
            }
        )
        return w


class Tick(models.Model):
    class State(Wifi.State):
        REST = 3

        CHOICES = Wifi.State.CHOICES+[
            (REST, 'Rest'),
        ]

    wifi = models.ForeignKey(Wifi, on_delete=models.CASCADE)
    start = models.DateTimeField(default=datetime.now)
    end = models.DateTimeField(default=datetime.now)
    state = models.IntegerField(choices=State.CHOICES, default=State.WORK)

    @classmethod
    def create(cls, wifi: Wifi, state=None, **kwargs):
        if state is None:
            state = wifi.state

        kwargs.update({
            'state': state,
            'wifi': wifi
        })

        print(kwargs)
        return cls.objects.create(**kwargs)

    @classmethod
    def today(cls) -> QuerySet:
        return cls.day(date.today())

    @classmethod
    def day(cls, day: date) -> QuerySet:
        # day = day.replace(hour=0, minute=0, second=0)
        return cls.objects.filter(
            start__gte=day,
            start__lt=day + timedelta(days=1)
        )

    @classmethod
    def days(cls, end: date, start: date) -> List[Tuple[date, QuerySet]]:
        items = list()

        day = start
        while day >= end:
            r = cls.day(day)
            items.append((day, r))
            day -= timedelta(days=1)
        return list(reversed(items))

    @classmethod
    def work_time(cls, data: QuerySet) -> timedelta:
        rez = timedelta()
        if data.exists():
            for i in data.filter(state=cls.State.WORK):
                rez += i.timedelta()
            return rez - timedelta(microseconds=rez.microseconds)
        else:
            return timedelta()

    def timedelta(self):
        return self.end - self.start

    def __str__(self):
        return f'{self.wifi.essid or None}[{self.start.replace(microsecond=0)},{self.end.replace(microsecond=0)}]'
