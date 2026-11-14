"""
ml/tests/test_downstream_hydrography.py

Automated test suite for PRAVAAH Phase 3E.3 Downstream Yamuna Hydrography:
- Verifies raw and processed river geometry files exist and are valid GeoJSON.
- Verifies resolution of missing Palla-Delhi reach (Way 24943999).
- Verifies strict topological continuity (zero gaps along the mainstem).
- Verifies station proximity (Hathnikund, Delhi ORB, Okhla Barrage).
- Verifies geodesic length calculation in EPSG:32643 UTM Zone 43N.
"""

from pathlib import Path
import json
import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point

from ml.spatial.river import RiverNetworkValidator, RiverValidationStatus
from ml.spatial.hydrography import HydrographyProcessor, HydrographyClass


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_GEOJSON = REPO_ROOT / "data" / "raw" / "spatial" / "hydrography" / "osm_yamuna_downstream_raw.geojson"
PROCESSED_MAINSTEM = REPO_ROOT / "data" / "processed" / "spatial" / "hydrography" / "yamuna_downstream_mainstem.geojson"
OSM_DIR = REPO_ROOT / "data" / "raw" / "spatial" / "hydrography" / "osm"


def test_osm_raw_way_files_exist():
    """Verify all 6 constituent OSM way full JSON files exist in data/raw/spatial/hydrography/osm/."""
    expected_ways = [132610023, 204980194, 648975828, 267825123, 24943999, 24944222]
    for wid in expected_ways:
        way_file = OSM_DIR / f"way_{wid}_full.json"
        assert way_file.exists(), f"Missing OSM raw way artifact: {way_file}"
        with open(way_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "elements" in data
            assert len(data["elements"]) > 0


def test_missing_palla_delhi_segment_resolved():
    """Verify Way 24943999 connects Sonipat/Palla to Delhi Old Railway Bridge."""
    palla_delhi_file = OSM_DIR / "way_24943999_full.json"
    assert palla_delhi_file.exists()

    with open(palla_delhi_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        way_el = next((e for e in data["elements"] if e.get("type") == "way"), None)
        assert way_el is not None
        node_ids = way_el["nodes"]
        # Starts at Palla border node 271078113 and ends at Delhi ORB node 271078156
        assert node_ids[0] == 271078113
        assert node_ids[-1] == 271078156
        assert len(node_ids) == 131


def test_raw_hydrography_geojson_validity():
    """Verify RiverNetworkValidator validates osm_yamuna_downstream_raw.geojson."""
    assert RAW_GEOJSON.exists()
    report = RiverNetworkValidator.validate_file(RAW_GEOJSON, clip_to_study_corridor=False)

    assert report.validation_status == RiverValidationStatus.VALID
    assert report.total_features == 6
    assert report.valid_features_count == 6
    assert report.invalid_features_count == 0
    assert report.empty_features_count == 0
    assert report.total_length_km > 250.0
    assert report.native_crs == "EPSG:4326"


def test_processed_mainstem_continuity_and_length():
    """Verify processed mainstem is continuous and measures >240 km from Hathnikund to Delhi."""
    assert PROCESSED_MAINSTEM.exists()
    gdf = gpd.read_file(PROCESSED_MAINSTEM)

    assert len(gdf) == 1
    geom = gdf.geometry.iloc[0]
    assert isinstance(geom, LineString)
    assert len(geom.coords) >= 2000

    # Project to EPSG:32643
    gdf_utm = gdf.to_crs("EPSG:32643")
    length_km = gdf_utm.geometry.iloc[0].length / 1000.0

    # Total Hathnikund to Okhla length is ~268 km
    assert 260.0 <= length_km <= 275.0

    props = gdf.iloc[0]
    assert props["continuity_status"] == "CONTINUOUS"
    assert "OpenStreetMap" in props["provenance"]
    assert "ODbL" in props["attribution"]


def test_station_proximity_to_centerline():
    """Verify key corridor monitoring stations align with the mainstem centerline."""
    gdf = gpd.read_file(PROCESSED_MAINSTEM).to_crs("EPSG:32643")
    line = gdf.geometry.iloc[0]

    stations = [
        ("Hathnikund Barrage", 30.317, 77.585, 1000.0),    # within 1 km
        ("Delhi ORB", 28.665, 77.240, 200.0),              # within 200 m
        ("Okhla Barrage", 28.545, 77.315, 200.0),          # within 200 m
    ]

    for name, lat, lon, max_dist_m in stations:
        pt_gdf = gpd.GeoDataFrame([{"geometry": Point(lon, lat)}], crs="EPSG:4326").to_crs("EPSG:32643")
        dist = pt_gdf.geometry.iloc[0].distance(line)
        assert dist <= max_dist_m, f"Station {name} is {dist:.1f} m from centerline, exceeding {max_dist_m} m"

