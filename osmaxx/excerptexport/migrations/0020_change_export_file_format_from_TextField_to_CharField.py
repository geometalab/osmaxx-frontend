# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-20 20:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excerptexport', '0019_one_export_per_file_format'),
    ]

    operations = [
        migrations.AlterField(
            model_name='export',
            name='file_format',
            field=models.CharField(choices=[('fgdb', 'ESRI File Geodatabase'), ('shapefile', 'ESRI Shapefile'), ('gpkg', 'GeoPackage'), ('spatialite', 'SpatiaLite'), ('garmin', 'Garmin navigation & map data')], max_length=10, verbose_name='file format / data format'),
        ),
    ]
