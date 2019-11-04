import os
from datetime import date, timedelta, datetime
from typing import List, Tuple

from sqlalchemy import Column, DateTime, ForeignKey, Boolean
from sqlalchemy import Integer, Unicode, Enum
from sqlalchemy import and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload, relationship

from db.base import Base, States


def strip_time(x):
    return x - timedelta(microseconds=x.microseconds)


class Wifi(Base):
    essid = Column(Unicode(40))
    bssid = Column(Unicode(17))
    state = Column(Enum(*States.keys()), server_default=States.WORK)
    ticks = relationship("Tick", back_populates="wifi")

    @classmethod
    def from_conf(cls, conf: dict) -> 'Wifi':
        if conf['access_point'] == 'Not-Associated':
            itm, created = Wifi.get_or_create(essid='')
            return itm
        w, created = Wifi.get_or_create(
            essid=conf['essid'],
            bssid=conf['access_point'],
            defaults={
                'state': States.UNKNOWN
            }
        )
        return w

    def __repr__(self):
        return f'WiFi[{self.essid}]'


class Tick(Base):
    wifi_id = Column(Integer, ForeignKey('wifi.id'))
    start = Column(DateTime, default=datetime.now)
    end = Column(DateTime, default=datetime.now)
    wifi = relationship(Wifi, back_populates="ticks")
    locked = Column(Boolean, default=False, server_default='false')

    @classmethod
    def create(cls, wifi: Wifi, **kwargs):
        kwargs.update({'wifi_id': wifi.id})

        instance = cls(**kwargs)
        cls.session.add(instance)
        cls.session.commit()

        return instance

    @classmethod
    def today(cls) -> List['Tick']:
        return cls.day(date.today())

    @classmethod
    def day(cls, day: date) -> List['Tick']:
        q = cls.session.query(Tick).options(
            joinedload(Tick.wifi)
        ).filter(
            and_(
                cls.wifi_id == Wifi.id,
                cls.start >= day,
                cls.start < day + timedelta(days=1)
            )
        )

        return q.all()

    @classmethod
    def days(cls, end: date, start: date) -> List[Tuple[date, List['Tick']]]:
        items = list()

        day = start
        while day >= end:
            r = cls.day(day)
            items.append((day, r))
            day -= timedelta(days=1)
        return list(reversed(items))

    @classmethod
    def work_time(cls, data: List['Tick']) -> timedelta:
        rez = timedelta()
        if data:
            for i in (i for i in data if i.wifi.state == States.WORK):
                rez += i.timedelta()
            return strip_time(rez)
        else:
            return timedelta()

    def timedelta(self):
        return self.end - self.start

    def __repr__(self):
        return f'Tick[{self.wifi.essid}]({strip_time(self.timedelta())})'


os.chdir(os.path.dirname(os.path.abspath(__file__)))

engine = create_engine('sqlite:///db.sqlite')

session = sessionmaker(autocommit=False, autoflush=False)
session.configure(bind=engine)
Base.metadata.create_all(engine)
Base.session = session()
