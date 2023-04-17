import logging
from datetime import datetime
from time import sleep, time

import requests
from requests.auth import HTTPDigestAuth


class Ultimaker():
    """
    Class implements local API of Ultimaker 3 printer.
    """

    def __init__(self, ip: str, username: str = "Test", credentials: dict | HTTPDigestAuth | None = None, auto_register: bool = True, timeout: int = 60):
        self.__ip = ip
        self.__api_url = "http://" + self.__ip + "/api/v1/"
        self.__cluster_url = "http://" + self.__ip + "/cluster-api/v1/"
        self.__username = username
        self.__app_name = "Test"
        self.__timeout = 5
        self.__heads_count = 1
        self.__extruders_count = 2
        self.logger = logging.getLogger(__name__)
        begin = time()
        REG_TIMEOUT = timeout
        if isinstance(credentials, dict):
            self.auth = HTTPDigestAuth(*credentials.values())
        elif isinstance(credentials, HTTPDigestAuth):
            self.auth = credentials
        else:
            self.auth = HTTPDigestAuth(*self.__get_credentials().values())
        while time() - begin < REG_TIMEOUT:
            if self.__check_auth(self.auth.username):
                break
            sleep(1)
        if time() >= begin + REG_TIMEOUT and not auto_register:
            raise TimeoutError("Registration timeout")
        if time() >= begin + REG_TIMEOUT and auto_register:
            self.auth = HTTPDigestAuth(*self.__get_credentials().values())

    def __get_credentials(self):
        return requests.post(
            url=self.__api_url + "auth/request",
            data={"application": self.__app_name, "user": self.__username},
            timeout=self.__timeout
        ).json()

    def __check_auth(self, user_id: int | str):
        if isinstance(user_id, int):
            user_id = str(user_id)
        data = requests.get(
            url=self.__api_url + f"auth/check/{user_id}",
            auth=self.auth,
            timeout=self.__timeout
        ).json()
        if data["message"] == "authorized":
            return True
        return False

    def get_credentials(self) -> dict:
        return {"id": self.auth.username, "key": self.auth.password}

    def put_printer_led(self, brightness: float, saturation: float, hue: float) -> None:
        """
        Sets printer LED color

        Args:
            brightness (float): brightness (value), 0-100
            saturation (float): saturation, 0-100
            hue (float): hue, 0-360

        Raises:
            ValueError: if brightness, saturation or hue is out of range

        Returns:
            None
        """
        if brightness < 0 or brightness > 100:
            raise ValueError("Brightness is out of range")
        if saturation < 0 or saturation > 100:
            raise ValueError("Saturation is out of range")
        if hue < 0 or hue > 360:
            raise ValueError("Hue is out of range")
        data = requests.put(
            url=self.__api_url + "printer/led",
            auth=self.auth,
            json={"brightness": brightness,
                  "saturation": saturation, "hue": hue},
            timeout=self.__timeout
        )
        self.logger.debug('put_printer_led: %d | %s', data.status_code, data.text)
        if data.status_code != 204:
            raise Exception("Error while changing LED color")

    def get_printer(self) -> dict:
        return requests.get(
            url=self.__api_url + "printer",
            auth=self.auth,
            timeout=self.__timeout
        ).json()

    def post_printer_led_blink(self, frequency: float, count: int) -> None:
        if frequency < 0.1 or frequency > 100:
            raise ValueError("Frequency is out of range")
        if count < 1 or count > 1000:
            raise ValueError("Count is out of range")
        data = requests.post(
            url=self.__api_url + "printer/led/blink",
            auth=self.auth,
            json={"frequency": frequency, "count": count},
            timeout=self.__timeout
        )
        if data.status_code != 204:
            raise Exception("Error while blinking LED")

    #!fixme throws "405: Method not allowed"
    def put_printer_heads_position(self, head_id: int, x: float, y: float, z: float) -> None:
        if head_id >= self.__heads_count:
            raise ValueError("head_id is out of range")
        data = requests.put(
            url=self.__api_url + "printer/heads/" + str(head_id) + "/position",
            auth=self.auth,
            json={"x": x, "y": y, "z": z},
            timeout=self.__timeout
        )
        if data.status_code != 204:
            raise Exception("Error while changing position")

    #!fixme throws "405: Method not allowed"
    def put_printer_bed_temperature(self, temperature: float) -> None:
        data = requests.put(
            url=self.__api_url + "printer/bed/temperature",
            auth=self.auth,
            json={"temperature": temperature},
            timeout=self.__timeout
        )
        self.logger.debug('put_printer_bed_temperature: %d | %s', data.status_code, data.json())
        if data.status_code == 405:
            raise Exception("Method not allowed")

    def put_printer_bed_pre_heat(self, temperature: float, timeout: int) -> None:
        if temperature < 0 or temperature > 100:
            raise ValueError("Temperature is out of range")
        if timeout < 60 or timeout > 60*60:
            raise ValueError("Timeout is out of range")
        data = requests.put(
            url=self.__api_url + "printer/bed/pre_heat",
            auth=self.auth,
            json={"temperature": temperature, "timeout": timeout},
            timeout=self.__timeout
        )
        self.logger.debug('put_printer_bed_pre_heat: %d | %s', data.status_code, data.json())
        if data.status_code == 400:
            raise Exception("Error while preheating bed")
    
    def set_bed_temperature(self, temperature: float) -> bool:
        if not self.get_print_jobs():
            self.put_printer_bed_pre_heat(temperature, 60*10)
            self.put_printer_led(50, 100, 30)
            return True
        return False     

    #!fixme throws "405: Method not allowed"
    def put_printer_heads_extruders_hotend_temperature(self, head_id: int, extruder_id: int, temperature: float) -> dict:
        # raise NotImplementedError("405: Method not allowed")
        if head_id >= self.__heads_count:
            raise ValueError("head_id is out of range")
        if extruder_id >= self.__extruders_count:
            raise ValueError("extruder_id is out of range")
        data = requests.put(
            url=self.__api_url + "printer/heads/" +
            str(head_id) + "/extruders/" +
            str(extruder_id) + "/hotend/temperature",
            auth=self.auth,
            json={"temperature": temperature},
            timeout=self.__timeout
        )
        self.logger.debug('put_printer_heads_extruders_hotend_temperature: %d | %s', data.status_code, data.json())

    def post_printer_beep(self, frequency: float, duration: float) -> None:
        if frequency < 0.1 or frequency > 100:
            raise ValueError("Frequency is out of range")
        if duration < 0 or duration > 100:
            raise ValueError("Duration is out of range")
        data = requests.post(
            url=self.__api_url + "printer/beep",
            auth=self.auth,
            json={"frequency": frequency, "duration": duration},
            timeout=self.__timeout
        )
        self.logger.debug('post_printer_beep: %d | %s', data.status_code, data.text)
        if data.status_code == 400:
            raise ValueError("Unable to beep due to missing parameters")
        if data.status_code != 204:
            raise Exception("Error while beeping")

    def get_print_job(self) -> dict:
        data = requests.get(
            url=self.__api_url + "print_job",
            auth=self.auth,
            timeout=self.__timeout
        )
        self.logger.debug('get_print_job: %d | %s', data.status_code, data.json())
        return data.json()

    def post_print_job(self, jobname: str, file: str) -> dict:
        return requests.post(
            url=self.__api_url + "print_job",
            auth=self.auth,
            json={"jobname": jobname},
            files={"file": open(file, "rb")},
            timeout=self.__timeout
        ).json()
    
    def get_print_jobs(self) -> list[dict]:
        data = requests.get(
            url=self.__cluster_url + "print_jobs",
            timeout=self.__timeout
        )
        self.logger.debug('get_print_jobs: %d | %s', data.status_code, data.json())
        return data.json()

    def set_print_job_state(self, state: str) -> bool:
        if state not in ["print", "pause", "abort"]:
            raise ValueError("State must be 'print', 'pause' or 'abort'")
        job = self.get_print_jobs()[0]
        # todo: отслеживание несоответствия текущего состояния и запрошенного
        data = requests.post(
            url=self.__cluster_url + "print_jobs/" + job["uuid"] + "/action",
            auth=self.auth,
            json={"action": state},
            timeout=self.__timeout
        )
        self.logger.debug('set_print_job_state: %d | %s', data.status_code, data.text)
        return True

    def get_system(self) -> dict:
        return requests.get(
            url=self.__api_url + "system",
            auth=self.auth,
            timeout=self.__timeout
        ).json()

    def put_system_display_message(self, message: str, button_caption: str) -> None:
        data = requests.put(
            url=self.__api_url + "system/display_message",
            auth=self.auth,
            json={"message": message, "button_caption": button_caption},
            timeout=self.__timeout
        ).json()
        if data["message"] != "ok":
            raise Exception("Failed to display message")

    def get_camera_feed(self) -> dict:
        return requests.get(
            url=self.__api_url + "camera",
            auth=self.auth,
            timeout=self.__timeout
        ).json()
