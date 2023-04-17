import logging

from django.db import models


class Users(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    email = models.CharField(max_length=64)
    password = models.CharField(max_length=128)
    registered_at = models.DateTimeField(auto_now_add=True)
    # is_approved = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    logger = logging.getLogger(__name__)

    def __str__(self):
        return f'Id: {self.id}, Name: {self.name}, Email: {self.email}, ' \
            f'Registered at: {self.registered_at}, Is blocked: {self.is_blocked}'

    def save(self, *args, **kwargs):
        self.logger.debug(f'User {self.id=}, {self.name=} saved')
        super().save(*args, **kwargs)


class Printers(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=64)
    api_id = models.CharField(max_length=32)
    api_key = models.CharField(max_length=64)
    registered_at = models.DateTimeField(auto_now_add=True)
    logger = logging.getLogger(__name__)

    def __str__(self):
        return f'Id: {self.id}, Name: {self.name}, Address: {self.address}, ' \
            f'Registered at: {self.registered_at}'

    def save(self, *args, **kwargs):
        self.logger.debug(f'Printer {self.name=}, {self.address=} saved')
        super().save(*args, **kwargs)

    def get_credentials(self):
        return {"id": self.api_id, "key": self.api_key}

    def update_credentials(self, api_id: str, api_key: str):
        if self.api_id == api_id and self.api_key == api_key:
            self.logger.debug(
                f'Printer {self.address} credentials not changed')
            return
        self.api_id = api_id
        self.api_key = api_key
        self.save()
        self.logger.debug(f'Printer {self.address} credentials updated')


class Logs(models.Model):
    id = models.AutoField(primary_key=True)
    printer_id = models.ForeignKey(
        Printers, on_delete=models.CASCADE, db_column='printer_id')
    user_id = models.ForeignKey(
        Users, on_delete=models.CASCADE, db_column='user_id', null=True)
    message = models.TextField()
    type = models.CharField(max_length=16, default='info')
    created_at = models.DateTimeField(auto_now_add=True)
    logger = logging.getLogger(__name__)

    def __str__(self):
        return f'Id: {self.id}, Printer id: {self.printer_id}, Message: {self.message}'

    def save(self, *args, **kwargs):
        self.logger.debug(
            f'Log {self.id} for printer {self.printer_id.address} saved')
        super().save(*args, **kwargs)

    def to_str(self):
        return f'Printer: {self.printer_id} | {self.message}'
