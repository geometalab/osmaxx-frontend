# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-18 12:01
from __future__ import unicode_literals

import os

from django.db import migrations


def get_polyfile_name_to_file_mapping():
    from osmaxx.excerptexport._settings import POLYFILE_LOCATION
    from osmaxx.utils.polyfile_helpers import _is_polyfile
    filenames = os.listdir(POLYFILE_LOCATION)
    return {
        _extract_country_name_from_polyfile_name(filename): filename
        for filename in filenames if _is_polyfile(filename)
    }


def _extract_country_name_from_polyfile_name(filename):
    from osmaxx.utils.polyfile_helpers import POLYFILE_FILENAME_EXTENSION
    name, _ = filename.split(POLYFILE_FILENAME_EXTENSION)
    return name


def merge_countries(apps, schema_editor):  # noqa
    Excerpt = apps.get_model("excerptexport", "Excerpt")  # noqa
    countries = Excerpt.objects.filter(country__isnull=False).order_by('name')
    import itertools
    for key, group in itertools.groupby(countries, lambda x: x.name):
        group_list = list(group)
        if len(group_list) > 1:
            country_excerpt = group_list[0]
            for duplicate_country_excerpt in group_list[1:]:
                for extraction_order in duplicate_country_excerpt.extraction_orders.all():
                    extraction_order.excerpt = country_excerpt
                    extraction_order.save()
                    duplicate_country_excerpt.delete()


def unmerge_countries(apps, schema_editor):  # noqa
    # this is still correct, no need to undo any changes
    pass


def import_countries(apps, schema_editor):  # noqa
    from osmaxx.utils.polyfile_helpers import polyfile_to_geos_geometry
    Excerpt = apps.get_model("excerptexport", "Excerpt")  # noqa
    ExtractionOrder = apps.get_model("excerptexport", "ExtractionOrder")  # noqa
    for name, polyfile_path in get_polyfile_name_to_file_mapping().items():
        geometry = polyfile_to_geos_geometry(polyfile_path)
        excerpt = Excerpt.objects.create(
            is_public=True,
            name=name,
            bounding_geometry=geometry,
            excerpt_type='country',
        )
        for extraction_order in ExtractionOrder.objects.filter(excerpt__name=name):
            extraction_order.excerpt = excerpt
            extraction_order.save()


def remove_countries(apps, schema_editor):  # noqa
    Excerpt = apps.get_model("excerptexport", "Excerpt")  # noqa
    ExtractionOrder = apps.get_model("excerptexport", "ExtractionOrder")  # noqa
    existing_extraction_orders = ExtractionOrder.objects.all()
    Excerpt.objects.exclude(extraction_orders__in=existing_extraction_orders).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('excerptexport', '0032_allow_user_None'),
    ]

    operations = [
        migrations.RunPython(merge_countries, unmerge_countries),
        migrations.RunPython(import_countries, remove_countries),
    ]
