# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-11 12:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conversion', '0011_remove_falsely_zeroed_unzipped_result_size_values_20160718_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parametrization',
            name='out_format',
            field=models.CharField(choices=[('fgdb', 'Esri File Geodatabase'), ('shapefile', 'Esri Shapefile'), ('gpkg', 'GeoPackage'), ('spatialite', 'SpatiaLite'), ('garmin', 'Garmin navigation & map data'), ('pbf', 'OSM Protocolbuffer Binary Format')], max_length=100, verbose_name='out format'),
        ),
    ]