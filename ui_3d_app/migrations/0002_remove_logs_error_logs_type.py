# Generated by Django 4.2 on 2023-04-12 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui_3d_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='logs',
            name='error',
        ),
        migrations.AddField(
            model_name='logs',
            name='type',
            field=models.CharField(default='info', max_length=16),
        ),
    ]
