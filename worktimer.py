#!/bin/python3

import sys
from datetime import date, datetime, timedelta

import arrow

import django_init
from helpers.notifier import Notify
from worktimer.models import Tick, Wifi

_ = django_init.application

WORKDAY = timedelta(hours=8, minutes=30)
UTC_FIX = timedelta(hours=3)


def main():
    from time import sleep
    from helpers.iwconfig import IwConfig

    WORKDAY_END = False

    while 1:
        today = Tick.today()
        stats = IwConfig().interfaces
        wifi = Wifi.from_conf(stats.popitem()[1])

        if today.count() == 0:
            Tick.objects.create(wifi=wifi)

        if today.filter(wifi__state=Wifi.State.WORK).count() == 0 and wifi.state == Wifi.State.WORK:
            work_start = datetime.now().replace(microsecond=0) + UTC_FIX
            Notify.show('WORK', f'Рабочий день начался {work_start}', 'emoticon')
            WORKDAY_END = False

        last = today.last()
        if last.wifi_id != wifi.id:
            if wifi.id == 1:
                Notify.show('WORK', f'Wifi disconnected')
            else:
                Notify.show('WORK', f'Changed to {wifi.essid}')

            if last.wifi.state == Wifi.State.WORK and wifi.state == Wifi.State.HOME:
                Notify.show('WORK', 'Welcome home')
                worktime = Tick.work_time(today)
                Notify.show('Добро пожаловать', f'\nЗа сегодня: {worktime}', 'kmousetool_off')

            Tick.objects.create(wifi=wifi)
        else:
            last.end = datetime.now()
            last.save()

        worktime = Tick.work_time(today)
        if worktime >= WORKDAY and not WORKDAY_END:
            Notify.show('Рабочий день окончен', f'Потрачено: {worktime}', 'kmousetool_off')
            WORKDAY_END = True

        sleep(5)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()

    if len(sys.argv) == 2:
        if sys.argv[1] in ['show', 'today']:
            tw = Tick.today()
            worktime = Tick.work_time(tw)
            tw_last = tw.last()
            if tw_last and tw_last.wifi.state == Wifi.State.WORK:
                Notify.show('Рабочий день в процессе', f'Потрачено: {worktime}')
            else:
                Notify.show('Отдых', f'Потрачено: {worktime}')
        elif sys.argv[1] == 'mouth':
            from itertools import groupby

            d = Tick.days(date.today() - timedelta(days=30), date.today())

            weeks = [
                [(i[0], Tick.work_time(i[1])) for i in v]
                for k, v in groupby(d, lambda x: x[0].isocalendar()[1])
            ]

            week_reports = list()
            for week in weeks:
                weektime = timedelta(seconds=sum([i[1].seconds for i in week]))
                if not weektime:
                    continue

                week_report = [f'{d} {t or "-"}' for d, t in week]

                week_need = WORKDAY * min(len(week), 5)
                if weektime > week_need:
                    week_report += [f'Overtime: {weektime - week_need}']
                else:
                    week_report += [f'Overtime: -{week_need - weektime}']

                week_reports.append('\n'.join(week_report))
            print('\n'.join(week_reports))
    elif len(sys.argv) == 3:
        if sys.argv[1] == 'set':
            wifi = Tick.today().last().wifi
            state = sys.argv[2].lower()
            if wifi.id == 1:
                print(f'Wifi disconnected!')
            elif state == 'work':
                wifi.state = Wifi.State.WORK
                wifi.save()
                print(f'{state}: {wifi.essid}')
            elif state == 'home':
                wifi.state = Wifi.State.HOME
                wifi.save()
                print(f'{state}: {wifi.essid}')
            else:
                print(f'Unknown status: {state}')
        elif sys.argv[1] == '+':
            tm = arrow.get(sys.argv[2].lower()).datetime.replace(tzinfo=None)
            tm = tm.replace(hour=10)

            w = Wifi.objects.filter(state=Wifi.State.WORK).first()

            Tick.day(tm.date()).delete()

            t = Tick.objects.create(
                wifi=w,
                start=tm,
                end=tm + WORKDAY
            )
            print(f"Create {t}")
    else:
        print(f'Unknown args: {sys.argv[1:]}')