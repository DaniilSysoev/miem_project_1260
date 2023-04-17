import logging
from collections import namedtuple
from functools import lru_cache
from os import getenv

import regex
import requests

from printer import Ultimaker as UL
from ui_3d_app.models import Logs, Printers, Users

logging.basicConfig(level=logging.DEBUG)


MenuItem = namedtuple('MenuItem', ['id', 'name'])

ABOUT_TEXT = """
<p><b>Последнее обновление:</b> 2023-04-18<br></p>
<p><b>Контакты:</b><br>
• <a href="https://t.me/ekkkkkkkkkkka" style="color:blue">Екатерина Чебоксарова</a> — датасет<br>
• <a href="https://t.me/l_johany_l" style="color:blue">Михаил Маликов</a> — компьютерное зрение<br>
• <a href="https://t.me/sweet6s" style="color:blue">Роман Приходько</a> — нейросеть<br>
• <a href="https://t.me/chekanov_ivan" style="color:blue">Иван Чеканов</a> — бэкенд<br>
• <a href="https://t.me/dmsysoev" style="color:blue">Даниил Сысоев</a> — фронтенд<br>
• <a href="https://t.me/fortis_30" style="color:blue">Андрей Боярчуков</a> — дизайн<br></p>
"""

STATES = {
    'printing': 'Печать',
    'paused': 'Пауза',
    'pausing': 'Приостановка',
    'pre_print': 'Подготовка',
    'resuming': 'Возобновление',
    'post_print': 'Остановка',
    'wait_cleanup': 'Стол занят',
    'wait_user_action': 'Ожидание действия',
}

@lru_cache(maxsize=1)
def get_printer(db_printer: Printers) -> UL | None:
    """
    Creates instance of Ultimaker printer based on database info

    Args:
        db_printer (models.Printers): printer info from database
    
    Returns:
        printer.Ultimaker: instance of Ultimaker printer
    """
    try:
        return UL(ip=db_printer.address, credentials=db_printer.get_credentials(), timeout=5)
    except Exception as exc:
        logging.error(f'Failed to connect to printer: {exc}')
        Logs(printer_id=db_printer,
             message=f'Ошибка при работе с принтером: {exc}', type='error').save()
        return None


# todo: запуск логирования
# todo: остановка логирования при удалении принтера
def log_error(error: str, printer_id: str) -> None:
    """
    Logs error to database

    Args:
        error (str): error message
        metadata (str): additional info
    """
    printer = Printers.objects.get(id=printer_id)
    msg = f'Ошибка печати: {error}'
    Logs(printer_id=printer, message=msg, type='error').save()


def get_joke() -> str:
    """
    Gets a random joke from rzhunemogu.ru

    Returns:
        str: joke
    """
    joke = ''
    counter = 0
    while not joke and counter < 3:
        try:
            req = requests.get('http://rzhunemogu.ru/RandJSON.aspx?CType=1')
            logging.debug(f'Got joke: {req.text}')
            joke = req.json(strict=False)['content'].replace(
                '\r\n', '\n').replace('\n', ' ').replace('  ', ' ').strip()
            joke = regex.sub(r'([:.!?]) ([-–—])', r'\1<br>—', joke)
            return joke
        except Exception as exc:
            logging.error(f'Failed to get anekdot: {exc}')
            counter += 1
    return f'Колобок повесился<br><br>Произошла какая-то ошибка…'


def get_printer_status(db_printer: Printers) -> str:
    """
    Gets printer system status from Ultimaker API

    Args:
        db_printer (models.Printers): printer info from database

    Returns:
        str: formatted printer status
    """
    api_printer = get_printer(db_printer)
    if not api_printer:
        return '<p>Принтер не подключён</p>'
    params = api_printer.get_printer()
    print_job = api_printer.get_print_job()
    if 'state' not in print_job or print_job['state'] not in STATES:
        return '<p>Принтер в режиме ожидания</p>'
    elapsed = f'{print_job["time_elapsed"] // 3600:02d}:' \
        f'{print_job["time_elapsed"] % 3600 // 60:02d}:' \
        f'{print_job["time_elapsed"] % 60:02d}'
    left = f'{(print_job["time_total"] - print_job["time_elapsed"]) // 3600:02d}:' \
        f'{(print_job["time_total"] - print_job["time_elapsed"]) % 3600 // 60:02d}:' \
        f'{(print_job["time_total"] - print_job["time_elapsed"]) % 60:02d}'
    status = f'<p>Название: {print_job["name"]}</p>' \
        f'<p>Статус: {STATES[print_job["state"]]}</p>' \
        f'<p>Прогресс: {round(print_job["progress"]*100, 2)}%</p>' \
        f'<p>Запущена: {print_job["datetime_started"]}</p>' \
        f'<p>Прошло времени: {elapsed}</p>' \
        f'<p>Осталось времени: {left}</p>' \
        f'<p>Температура сопла: {params["heads"][0]["extruders"][0]["hotend"]["temperature"]["current"]}</p>' \
        f'<p>Температура стола: {params["bed"]["temperature"]["current"]}</p>' \
        f'<p>Скорость вентилятора: {params["heads"][0]["fan"]}</p>' \
        f'<p>Источник: {print_job["source"]}</p>'
    return status


def get_printer_state(db_printer: Printers) -> str:
    """
    Gets name of printer system status based on Ultimaker API

    Args:
        db_printer (models.Printers): printer info from database

    Returns:
        str: printer status name
    """
    api_printer = get_printer(db_printer)
    if not api_printer:
        return 'Принтер не подключён'
    print_job = api_printer.get_print_job()
    if 'state' not in print_job:
        return 'Ожидание'
    return STATES.get(print_job['state'], 'Не подключён')


def get_printer_parameters(db_printer: Printers) -> dict:
    """
    Gets printer temperatures, head position and extruder parameters from Ultimaker API

    Args:
        db_printer (models.Printers): printer info from database

    Returns:
        dict: actual printer parameters
    """
    data = {
            'current_temp_nozzle': '',
            'current_temp_bed': '',
            'current_head_max_speed': '',
            'current_head_target_acceleration': '',
            'current_head_target_speed_jerk': '',
            'current_head_x_value': '',
            'current_head_y_value': '',
            'current_head_z_value': '',
            'current_extruder_max_speed': '',
            'current_extruder_target_acceleration': '',
            'current_extruder_target_jerk': '',
        }
    api_printer = get_printer(db_printer)
    if not api_printer:
        return data
    params = api_printer.get_printer()
    data['current_temp_nozzle'] = params['heads'][0]['extruders'][0]['hotend']['temperature']['target']
    data['current_temp_bed'] = params['bed']['temperature']['target']
    data['current_head_max_speed'] = params['heads'][0]['max_speed']['x']
    data['current_head_target_acceleration'] = params['heads'][0]['acceleration']
    data['current_head_target_speed_jerk'] = params['heads'][0]['jerk']['x']
    data['current_head_x_value'] = params['heads'][0]['position']['x']
    data['current_head_y_value'] = params['heads'][0]['position']['y']
    data['current_head_z_value'] = params['heads'][0]['position']['z']
    data['current_extruder_max_speed'] = params['heads'][0]['extruders'][0]['feeder']['max_speed']
    data['current_extruder_target_acceleration'] = params['heads'][0]['extruders'][0]['feeder']['acceleration']
    data['current_extruder_target_jerk'] = params['heads'][0]['extruders'][0]['feeder']['jerk']
    for key, value in data.items():
        data[key] = str(value)
    return data


def get_printer_info(db_printer: Printers) -> str:
    """
    Gets printer current status from Ultimaker API (job name, progress, etc.)

    Args:
        db_printer (models.Printers): printer info from database

    Returns:
        str: formatted printer info
    """
    api_printer = get_printer(db_printer)
    if not api_printer:
        return 'Принтер не подключён'
    data = api_printer.get_system()
    data.pop('log', None)
    info = ''
    for key, value in data.items():
        info += f'<p>{key}: {value}</p>'
    return info

def get_menu_items() -> list[MenuItem]:
    items = []
    for printer in Printers.objects.all().order_by('id'):
        state = get_printer_state(printer)
        if state:
            name = f'{printer.name} — {state}'
        else:
            name = printer.name
        items.append(MenuItem(printer.id, name))
    return items
