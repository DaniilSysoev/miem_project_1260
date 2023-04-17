# WEB часть проекта

## Доступ к изображению с камеры

Адрес камеры: http://192.168.1.75:8080/?action=stream  
(возможно, принтер сменит свой адрес или отключится от сети; тогда надо снова подключить его к WiFi и заменить адрес в ссылке)

## Работа с принтером по REST API

Библиотека, реализующая API принтера: [GitHub](https://github.com/vanderbilt-design-studio/python-ultimaker-printer-api)  

### Получение данных для входа

```python
import requests

auth_data = requests.post(url='http://192.168.1.75/api/v1/auth/request', data={"application": "Test", "user": "Booba"}).json()
```

В результате `auth_data` аналогична такому словарю: `{"id": "0fab614c7397aa31887500654d623d1f", "key": "eff03ec38963647ca858e5eae08f83e4f3d5a772c1bfeafb3db67b136f41a773"}`.

**ToDo:** протестировать изменение имени пользователя и влияние новой регистрации на уже авторизованных пользователей.

### Авторизация и выполнение запросов

> Примем, что auth_data — словарь, полученный в предыдущем пункте.

```python
import requests
from requests.auth import HTTPDigestAuth as DA

requests.put(url="http://192.168.1.75/api/v1/printer/led", auth=DA(*auth_data), json={"brightness": 100.0,"saturation": 100.0,"hue": 50})
```

Полный список запросов и их параметров можно посмотреть в файле `ultimaker_api.mhtml` в корне проекта или в документации, доступной по адресу http://192.168.1.75.

### Интерфейс

Разработанный интерфейс : https://www.figma.com/file/ecjWpHxxJQkrlqQz69oV2n/Final?node-id=0%3A1&t=bqoiuGLNgEyzmtd7-1
