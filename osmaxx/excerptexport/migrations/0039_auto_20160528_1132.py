# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-28 09:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('excerptexport', '0038_remove_outputfile_file_old'),
    ]

    operations = [
        migrations.AlterField(
            model_name='export',
            name='created_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, verbose_name='created at'),
        ),
    ]
