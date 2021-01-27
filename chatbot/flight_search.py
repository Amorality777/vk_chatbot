import datetime
from settings import FLIGHT_CONF

FLIGHTS = 5
departure_list = []


def flight_search(from_, to, when):
    global departure_list
    departure_list = []
    dates = FLIGHT_CONF[from_][to]
    if isinstance(when, str):
        when = datetime.datetime.strptime(when, '%d-%m-%Y').date()
    if dates is None:
        return None
    elif when < datetime.date.today():
        return 'date is not current'
    elif dates['periodicity'] == 'day':
        scan_day(when, dates['datetime'])
    elif dates['periodicity'] == 'week':
        scan_week(when, dates['datetime'])
    elif dates['periodicity'] == 'month':
        scan_month(when, dates['datetime'])
    else:
        raise TypeError(f"I don't know how to work with this info {dates['periodicity']}")
    return departure_list


def append_date(time, when):
    global departure_list
    date = f'{time} {when.strftime("%d-%m-%Y")}'
    departure_list.append(date)


def scan_day(when, dates):
    for time in dates:
        append_date(time, when)


def scan_week(when, dates):
    time = dates['time']
    weekdays = dates['weekdays']
    now = datetime.datetime.isoweekday(when)
    delta = None
    flag = 0
    diff_days = weekdays[1] - weekdays[0], 7 - (weekdays[1] - weekdays[0])
    for flag, weekday in enumerate(weekdays):
        if now <= weekday:
            delta = datetime.timedelta(weekday - now)
            break
    if delta is None:
        delta = datetime.timedelta(now - weekdays[0] - 1)
        flag = 0
    date = when + delta
    for _ in range(FLIGHTS):
        append_date(time, date)
        date = date + datetime.timedelta(diff_days[flag])
        flag = 0 if flag == 1 else 1


def scan_month(when, dates):
    time = dates['time']
    monthdays = dates['monthdays']
    now_day = when.day
    flag = 0
    date = None
    for flag, monthday in enumerate(monthdays):
        if now_day <= monthday:
            date = when + datetime.timedelta(monthday - now_day)
            break
    if date is None:
        date = datetime.date(
            year=when.year,
            month=when.month + 1,
            day=monthdays[0])
        flag = 0
    for _ in range(FLIGHTS):
        append_date(time, date)
        if flag == 1:
            date = datetime.date(
                year=date.year if date.month < 12 else date.year + 1,
                month=date.month + 1 if date.month < 12 else 1,
                day=monthdays[0])
            flag = 0
        else:
            date = datetime.date(
                year=date.year,
                month=date.month,
                day=monthdays[1])
            flag = 1


if __name__ == '__main__':
    fr = 'Париж'
    t = 'Лондон'
    wh = datetime.date(2020, 8, 1)
    inf = flight_search(fr, t, wh)
    print(inf)
    fr = 'Париж'
    t = 'Вашингтон'
    wh = datetime.date(2020, 9, 9)
    inf = flight_search(fr, t, wh)
    print(inf)
    fr = 'Москва'
    t = 'Лондон'
    wh = datetime.date(2020, 1, 1)
    inf = flight_search(fr, t, wh)
    print(inf)
    fr = 'Москва'
    t = 'Париж'
    wh = datetime.date(2020, 1, 1)
    inf = flight_search(fr, t, wh)
    print(inf)
