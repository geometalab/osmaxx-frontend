# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-04 18:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('excerptexport', '0025_move_bounding_geometry_20160503_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='excerpt',
            name='bounding_geometry_old',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='excerptexport.BoundingGeometry', verbose_name='bounding geometry'),
        ),
    ]