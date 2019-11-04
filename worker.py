from datetime import datetime, timedelta

WORKDAY = timedelta(hours=8)
UTC_FIX = timedelta(hours=3)


def worker():
    from time import sleep
    from helpers.iwconfig import IwConfig
    from helpers.lock_detect import is_locked
    from helpers.notifier import Notify
    from db.models import Tick, Wifi, States

    workday_end = False

    while True:
        today = Tick.today()
        stats = IwConfig().interfaces
        wifi = Wifi.from_conf(stats.popitem()[1])
        locked = is_locked()

        if len(today) == 0:
            Tick.create(wifi=wifi)
            today = Tick.today()

        work_today = [i for i in today if i.wifi.state is States.WORK]
        if not work_today and wifi.state == States.WORK:
            work_start = datetime.now().replace(microsecond=0) + UTC_FIX
            Notify.show('WORK', f'Рабочий день начался {work_start}', 'emoticon')
            workday_end = False

        last = today[-1] if len(today) else None
        if last.wifi_id != wifi.id or locked != (last.wifi.state == States.REST):
            if last.wifi_id != wifi.id:
                if wifi.id == 1:
                    Notify.show('WORK', 'Wifi disconnected')
                else:
                    Notify.show('WORK', f'Changed to {wifi.essid}')

                if last.wifi.state == States.WORK and wifi.state == States.HOME:
                    Notify.show('WORK', 'Welcome home')
                    worktime = Tick.work_time(today)
                    Notify.show(
                        'Добро пожаловать',
                        f'\nЗа сегодня: {worktime}',
                        'kmousetool_off'
                    )
            Tick.create(
                wifi=wifi,
                locked=locked
            )
        else:
            last.end = datetime.now()
            last.session.add(last)
            last.session.commit()

        worktime = Tick.work_time(today)
        if worktime >= WORKDAY and not workday_end:
            Notify.show('Рабочий день окончен', f'Потрачено: {worktime}', 'kmousetool_off')
            workday_end = True

        sleep(5)
