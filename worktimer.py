#!/bin/python3

import argparse
from datetime import date, timedelta

import arrow

from helpers.notifier import Notify
from worker import worker, WORKDAY
from db.models import Tick, Wifi, States

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Working time tracker')
    parser.add_argument('--show', '--today', action='store_true', dest='show', help='Show today status')
    parser.add_argument('--mouth', action='store_true', help='Show mouth statistic')
    parser.add_argument('--set', choices=['work', 'home'], help='Set current wifi as...')
    parser.add_argument('--track', metavar='DATE', help='Track this date as working day')
    args = parser.parse_args()

    if args.show:
        tw = Tick.today()
        worktime = Tick.work_time(tw)
        if tw and tw[-1].wifi.state == States.WORK:
            Notify.show(f'Work in progress: {tw[-1].wifi.essid}', f'Spent: {worktime}')
        else:
            Notify.show(f'Rest: {tw[-1].wifi.essid}', f'Spent: {worktime}')
    elif args.mouth:
        from itertools import groupby

        d = Tick.days(date.today() - timedelta(days=30), date.today())

        weeks = [
            [(i[0], Tick.work_time(i[1])) for i in v]
            for k, v in groupby(d, lambda x: x[0].isocalendar()[1])
        ]

        week_reports = []
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
    elif args.set:
        wifi = Tick.today()[-1].wifi
        state = args.set.upper()
        if wifi.id == 0:
            print(f'Wifi disconnected!')
        elif state in (States.WORK, States.HOME):
            wifi.state = state
            wifi.save()
            print(f'{state}: {wifi.essid}')
        else:
            print(f'Unknown state: {state}')
    elif args.track:
        tm = arrow.get(args.track).datetime.replace(tzinfo=None)
        tm = tm.replace(hour=10)

        w = Wifi.session.query(Wifi).filter(
            Wifi.state == States.WORK
        ).first()

        for i in Tick.day(tm.date()):
            i.delete()

        t = Tick.create(
            wifi=w,
            start=tm,
            end=tm + WORKDAY
        )
        print(f"Tracked {t}")
    else:
        print("Starting service...")
        worker()
