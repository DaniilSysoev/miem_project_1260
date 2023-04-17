import logging
from os import getenv

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from printer import Ultimaker as UL
from ui_3d_app.models import Logs, Printers, Users
from  ui_3d_app import utils

logging.basicConfig(level=logging.DEBUG)


def check_db_printer(view):
    def wrapper(request, printer_id: int | None = None):
        logging.debug(
            f'"{view.__name__}" view called with {printer_id=}, {request=}')
        if Printers.objects.count() == 0:
            if not getenv('DEBUG', False):
                return new_printer(request)
            logging.debug('Debug mode is on, creating test printer')
            Printers(name='Test printer', address='123',
                     api_id='123', api_key='123').save()
        if not printer_id:
            printer_id = Printers.objects.order_by('id').first().id
            logging.debug(f'Assigned {printer_id=} to "{view.__name__}" view')
        try:
            Printers.objects.get(id=printer_id)
        except Printers.DoesNotExist:
            return HttpResponse('Printer not found', status=404)
        return view(request, printer_id)
    return wrapper


@csrf_exempt
@check_db_printer
def index(request, printer_id: int):
    db_printer = Printers.objects.get(id=printer_id)
    logs = Logs.objects.filter(
        printer_id=printer_id).order_by('-created_at')[:100]
    params = {
        'selected_printer': {
            'id': db_printer.id,
            'name': db_printer.name,
            'logs': logs,
            'status': utils.get_printer_status(db_printer),
            'state': utils.get_printer_state(db_printer),
        },
        'printers': utils.get_menu_items(),
    }
    current_parameters = utils.get_printer_parameters(db_printer)
    params = {**params, **current_parameters}
    if request.method != 'POST':
        return render(request, 'ui_3d_app/index.html', params)
    api_printer = utils.get_printer(db_printer)
    if not api_printer:
        params['status'] = 'Принтер не подключён'
        return render(request, 'ui_3d_app/index.html', params)
    # todo: добавление лога действий пользователя
    if 'temp_nozzle' in request.POST:
        logging.debug(f'{request.POST=}')
        temperature = int(request.POST.get('temp_nozzle', None))
        request.POST = {}
        api_printer.put_printer_heads_extruders_hotend_temperature(
            0, 0, temperature)
    if 'temp_bed' in request.POST:
        logging.debug(f'{request.POST=}')
        temperature = float(request.POST.get('temp_bed', None))
        request.POST = {}
        api_printer.set_bed_temperature(temperature)
    if 'pause' in request.POST:
        logging.debug(f'{request.POST=}')
        api_printer.set_print_job_state('pause')
        api_printer.put_printer_led(100, 100, 60)
        request.POST = {}
    if 'resume' in request.POST:
        logging.debug(f'{request.POST=}')
        api_printer.set_print_job_state('print')
        api_printer.put_printer_led(100, 100, 120)
        request.POST = {}
    if 'abort' in request.POST:
        logging.debug(f'{request.POST=}')
        api_printer.set_print_job_state('abort')
        api_printer.put_printer_led(100, 100, 0)
        request.POST = {}
    params['status'] = utils.get_printer_status(db_printer)
    return render(request, 'ui_3d_app/index.html', params)


@csrf_exempt
@check_db_printer
def control(request, printer_id: int | None = None):
    db_printer = Printers.objects.get(id=printer_id)
    if 'delete' in request.POST:
        db_printer.delete()
        request.POST = {}
        return control(request)
    if 'save_name' in request.POST:
        db_printer.name = request.POST.get('name', 'My favorite printer')
        request.POST = {}
        db_printer.save()
    if 'auto_stop' in request.POST:
        # todo: вкл/выкл автоматической остановки печати
        pass
    # todo: добавить отображение ip
    params = {
        'selected_printer': {
            'id': db_printer.id,
            'name': db_printer.name,
            'ip': db_printer.address,
        },
        'printers': utils.get_menu_items(),
        'data': utils.get_printer_info(db_printer),
    }
    return render(request, 'ui_3d_app/control.html', params)


@csrf_exempt
@check_db_printer
def camera(request, printer_id: int | None = None):
    db_printer = Printers.objects.get(id=printer_id)
    api_printer = utils.get_printer(db_printer)
    if api_printer:
        url = api_printer.get_camera_feed().get('url', '/static/ui_3d_app/404_camera.jpeg')
    else:
        url = '/static/ui_3d_app/404_camera.jpeg'
    params = {
        'selected_printer': {
            'id': db_printer.id,
            'name': db_printer.name,
        },
        'printers': utils.get_menu_items(),
        'url': url,
    }
    logging.debug(f'{params=}')
    return render(request, 'ui_3d_app/camera.html', params)


@csrf_exempt
def about(request):
    params = {
        'about': utils.ABOUT_TEXT,
        'joke': utils.get_joke(),
    }
    return render(request, 'ui_3d_app/about.html', params)


@csrf_exempt
def new_printer(request):
    if 'create' in request.POST:
        name = request.POST.get('name')
        address = request.POST.get('address')
        logging.debug(f'New printer: {name}; {address}')
        api_printer = UL(ip=address)
        credentials = api_printer.get_credentials()
        db_printer = Printers(name=name, address=address,
                              api_id=credentials['id'],
                              api_key=credentials['key'])
        db_printer.save()
        return index(request, db_printer.id)
    params = {
        'printers': Printers.objects.all().order_by('id')
    }
    return render(request, 'ui_3d_app/new_printer.html', params)
