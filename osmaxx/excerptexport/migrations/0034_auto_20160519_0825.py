# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-19 06:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('excerptexport', '0033_add_countries_as_public_excerpts_20160518_1401'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='excerpt',
            name='country',
        ),
    ]
