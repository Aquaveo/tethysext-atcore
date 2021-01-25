import datetime
import json
import uuid

from geoalchemy2 import func

from tethysext.atcore.exceptions import InvalidSpatialResourceExtentTypeError
from tethysext.atcore.models.app_users import SpatialResource
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialResourceTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.name = "A Spatial Resource"
        self.description = "Bad Description"
        self.status = "Processing"
        self.creation_date = datetime.datetime.utcnow()
        self.extent_dict = {
            'type': 'Polygon',
            'coordinates': [[
                [-109.557466506958, 40.4626541436629],
                [-109.557123184204, 40.4481880854746],
                [-109.528369903564, 40.4484166930046],
                [-109.528756141663, 40.4629153531036],
                [-109.557466506958, 40.4626541436629]
            ]]
        }
        self.extent_geojson = json.dumps(self.extent_dict)
        self.extent_wkt = 'SRID=4326;POLYGON((-109.557466506958 40.4626541436629,-109.557123184204 40.4481880854746,' \
                          '-109.528369903564 40.4484166930046,-109.528756141663 40.4629153531036,-109.557466506958 ' \
                          '40.4626541436629))'

        qry = self.session.query(func.ST_GeomFromEWKT(self.extent_wkt).label('geom'))
        self.expected_geometry = qry.first().geom

    def compare_geometries(self, geom_a, geom_b):
        text_a = self.session.query(func.ST_AsText(geom_a).label('text'))
        text_b = self.session.query(func.ST_AsText(geom_b).label('text'))
        self.assertEqual(text_a.first().text, text_b.first().text)

    def create_resource(self):
        resource = SpatialResource(
            name=self.name,
            description=self.description,
            status=self.status,
            date_created=self.creation_date
        )
        return resource

    def create_resource_in_session(self):
        resource = self.create_resource()
        self.session.add(resource)
        self.session.commit()
        return resource

    def test_create_resource(self):
        """Test SpatialResource round trip."""
        resource = SpatialResource(
            name=self.name,
            description=self.description,
            status=self.status,
            date_created=self.creation_date
        )

        self.session.add(resource)
        self.session.commit()

        all_resources_count = self.session.query(SpatialResource).count()
        all_resources = self.session.query(SpatialResource).all()

        self.assertEqual(all_resources_count, 1)
        for resource in all_resources:
            self.assertEqual(resource.name, self.name)
            self.assertEqual(resource.description, self.description)
            self.assertEqual(resource.date_created, self.creation_date)
            self.assertEqual(resource.status, self.status)
            self.assertFalse(resource.public)
            self.assertEqual(resource.type, SpatialResource.TYPE)
            self.assertIsInstance(resource.id, uuid.UUID)
            self.assertEqual(resource.extent, None)

    def test_set_extent_dict(self):
        """Test setting an extent from a dict."""
        resource = self.create_resource_in_session()
        self.assertTrue(resource.extent is None)
        resource.set_extent(self.extent_dict, 'dict')
        self.compare_geometries(resource.extent, self.expected_geometry)

    def test_set_extent_goejson(self):
        """Test setting an extent from a geojson."""
        resource = self.create_resource_in_session()
        self.assertTrue(resource.extent is None)
        resource.set_extent(self.extent_geojson, 'geojson')
        self.compare_geometries(resource.extent, self.expected_geometry)

    def test_set_extent_wkt(self):
        """Test setting an extent from a wkt."""
        resource = self.create_resource_in_session()
        self.assertTrue(resource.extent is None)
        resource.set_extent(self.extent_wkt, 'wkt')
        self.compare_geometries(resource.extent, self.expected_geometry)

    def test_set_extent_invalid_type(self):
        """Test trying to set an extent with an invalid type throws the correct error."""
        resource = self.create_resource_in_session()
        self.assertTrue(resource.extent is None)
        with self.assertRaises(InvalidSpatialResourceExtentTypeError) as exc:
            resource.set_extent(self.extent_wkt, 'bad_type')
        self.assertTrue('"bad_type" is not a valid type for a SpatialResource '
                        'extent. Must be one of "wkt", "geojson", or "dict"' in str(exc.exception))

    def test_get_extent_dict(self):
        """Test getting a dict from the extent."""
        resource = self.create_resource_in_session()
        resource.extent = self.expected_geometry
        extent = resource.get_extent('dict')
        self.assertDictEqual(extent, self.extent_dict)

    def test_get_extent_geojson(self):
        """Test getting a geojson from the extent."""
        resource = self.create_resource_in_session()
        resource.extent = self.expected_geometry
        extent = resource.get_extent('geojson')
        extent_dict = json.loads(extent)
        expected_dict = json.loads(self.extent_geojson)
        self.assertDictEqual(extent_dict, expected_dict)

    def test_get_extent_wkt(self):
        """Test getting a wkt from the extent."""
        resource = self.create_resource_in_session()
        resource.extent = self.expected_geometry
        extent = resource.get_extent('wkt')
        self.assertEqual(extent, self.extent_wkt)

    def test_get_extent_none(self):
        """Test getting an extent that hasn't been set before."""
        resource = self.create_resource_in_session()
        extent = resource.get_extent('wkt')
        self.assertEqual(extent, None)

    def test_get_extent_invalid_type(self):
        """Test trying to get an extent of an invalid type throws the correct error."""
        resource = self.create_resource_in_session()
        resource.extent = self.expected_geometry
        with self.assertRaises(InvalidSpatialResourceExtentTypeError) as exc:
            resource.get_extent('bad_type')
        self.assertTrue('"bad_type" is not a valid type for a SpatialResource '
                        'extent. Must be one of "wkt", "geojson", or "dict"' in str(exc.exception))

    def test_update_extent_srid(self):
        """Test trying to get an extent of an invalid type throws the correct error."""
        resource = self.create_resource_in_session()
        resource.extent = self.expected_geometry

        wkt_extent_query_before = self.session.query(func.ST_AsEWKT(resource.extent)).first()
        ret_before = wkt_extent_query_before[0]
        self.assertNotIn('SRID=3857', ret_before)

        resource.update_extent_srid(3857)

        wkt_extent_query_after = self.session.query(func.ST_AsEWKT(resource.extent)).first()
        ret_after = wkt_extent_query_after[0]
        self.assertIn('SRID=3857', ret_after)
