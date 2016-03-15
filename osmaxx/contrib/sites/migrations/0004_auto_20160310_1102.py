# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-10 10:02
from __future__ import unicode_literals

import django.contrib.sites.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0003_auto_20150602_1340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='domain',
            field=models.CharField(max_length=100, unique=True, validators=[django.contrib.sites.models._simple_domain_name_validator], verbose_name='domain name'),
        ),
    ]