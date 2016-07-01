import random
from contextlib import closing

import pytest
import sqlalchemy
from django.conf import settings
from django.contrib.gis.geos import Point
from sqlalchemy import select, func
from sqlalchemy.engine.url import URL as DBURL

from osmaxx.conversion_api.coordinate_reference_systems import WGS_84
from osmaxx.geodesy.coordinate_reference_system import UniversalTransverseMercatorZone as UTMZone, \
    wrap_longitude_degrees, utm_zones_for_representing
from tests.utils import slow


def test_naive_zone_of_point_amongst_zones_to_represent_the_point(transformable_point, utm_zone):
    assert utm_zone in utm_zones_for_representing(transformable_point)


def test_naive_antipodal_zone_of_point_not_amongst_zones_to_represent_the_point(untransformable_point, utm_zone):
    assert utm_zone not in utm_zones_for_representing(untransformable_point)


def test_utm_zone_treats_transformable_point_as_representable(transformable_point, utm_zone):
    assert utm_zone.can_represent(transformable_point)


def test_utm_zone_treats_untransformable_point_as_unrepresentable(untransformable_point, utm_zone):
    assert not utm_zone.can_represent(untransformable_point)


def test_transformation_to_utm_with_geodjango_geos(transformable_point, utm_zone):
    transformable_point.transform(utm_zone.srid)


@slow
def test_transformation_to_utm_with_geoalchemy2(transformable_point, utm_zone):
    django_db_config = settings.DATABASES['default']
    db_config = dict(
        username=django_db_config['USER'],
        password=django_db_config['PASSWORD'],
        database=django_db_config['NAME'],
        host=django_db_config['HOST'],
        port=django_db_config['PORT'],
    )
    engine = sqlalchemy.create_engine(DBURL('postgres', **db_config))

    query = select([func.ST_Transform(func.ST_GeomFromText(transformable_point.ewkt), utm_zone.srid)])
    with closing(engine.execute(query)) as result:
        assert result.rowcount == 1


@pytest.fixture
def untransformable_point(transformable_point):
    # antipodal point of a transformable point
    return Point(
        x=wrap_longitude_degrees(transformable_point.x + 180),
        y=-transformable_point.y,
        srid=WGS_84,
    )


@pytest.fixture
def transformable_point(transformable_point_longitude_degrees, transformable_point_latitude_degrees):
    return Point(transformable_point_longitude_degrees, transformable_point_latitude_degrees, srid=WGS_84)


@pytest.fixture(params=[-UTMZone.MAX_LONGITUDE_OFFSET, -23.0, 0, UTMZone.MAX_LONGITUDE_OFFSET])
def transformable_point_longitude_degrees(request, utm_zone):
    return wrap_longitude_degrees(utm_zone.central_meridian_longitude_degrees + request.param)


@pytest.fixture(params=[-90, -5, 0, 90])
def transformable_point_latitude_degrees(request):
    return request.param


@pytest.fixture
def utm_zone(hemisphere, utm_zone_number):
    return UTMZone(hemisphere=hemisphere, utm_zone_number=utm_zone_number)


@pytest.fixture(params=UTMZone.HEMISPHERE_PREFIXES.keys())
def hemisphere(request):
    return request.param

utm_zone_numbers = range(1, 60 + 1)
if not pytest.config.getoption("--all-utm-zones"):
    utm_zone_numbers = random.sample(utm_zone_numbers, 3)


@pytest.fixture(params=utm_zone_numbers)
def utm_zone_number(request):
    return request.param
