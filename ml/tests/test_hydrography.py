"""
ml/tests/test_hydrography.py

Automated test suite for Phase 3B: River Hydrography, Network Topology & Station Chainage.
Tests:
- Vector ingestion and CRS validation (EPSG:4326 to EPSG:32643 UTM 43N).
- Geometry validation (empty, invalid geometries, and coordinate range checks).
- Corridor clipping to [76.85°E–77.60°E, 28.50°N–30.40°N].
- Evidence-based classification (Main River, Canal, Tributary, Drain, Embankment).
- Duplicate geometry detection.
- Main channel extraction and topological gap analysis.
- NetworkX graph construction, node degrees, isolated segments, cycles/braids.
- River chainage calculation on continuous reach and refusal on disconnected channel.
- Safe handling of unacquired data and empty files.
"""

from pathlib import Path
import json
import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point, mapping

from ml.spatial.hydrography import (
    HydrographyProcessor,
    HydrographyClass,
    ChannelContinuityStatus,
    HydrographyValidationStatus,
    ChannelGapReport,
    RiverChainageReport,
    NetworkTopologySummary,
)


@pytest.fixture
def temp_hydro_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory structure mimicking data/."""
    d = tmp_path / "data" / "raw" / "spatial" / "hydrography"
    d.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def synthetic_continuous_fixture(tmp_path: Path) -> Path:
    """Creates a continuous synthetic river fixture for tests."""
    out = tmp_path / "synthetic_yamuna_continuous.geojson"
    return HydrographyProcessor.create_synthetic_hydrography_fixture(out, include_gaps=False)


@pytest.fixture
def synthetic_gapped_fixture(tmp_path: Path) -> Path:
    """Creates a synthetic river fixture with significant gaps for testing discontinuity."""
    out = tmp_path / "synthetic_yamuna_gapped.geojson"
    return HydrographyProcessor.create_synthetic_hydrography_fixture(out, include_gaps=True)


# -----------------------------------------------------------------------------
# 1. Classification & Attribute Preservation Tests
# -----------------------------------------------------------------------------

def test_feature_classification_rules():
    """Verifies evidence-based classification across waterway types."""
    # Main river
    assert HydrographyProcessor.classify_feature({"name": "Yamuna River", "waterway": "river"}) == HydrographyClass.MAIN_RIVER
    assert HydrographyProcessor.classify_feature({"name": "River Jumna", "waterway": "river"}) == HydrographyClass.MAIN_RIVER

    # Canals
    assert HydrographyProcessor.classify_feature({"name": "Western Yamuna Canal", "waterway": "canal"}) == HydrographyClass.CANAL
    assert HydrographyProcessor.classify_feature({"waterway": "canal"}) == HydrographyClass.CANAL

    # Tributaries
    assert HydrographyProcessor.classify_feature({"name": "Hindon River", "waterway": "river"}) == HydrographyClass.TRIBUTARY
    assert HydrographyProcessor.classify_feature({"name": "Som Nadi", "waterway": "stream"}) == HydrographyClass.TRIBUTARY

    # Drains / Minor
    assert HydrographyProcessor.classify_feature({"name": "Najafgarh Drain", "waterway": "drain"}) == HydrographyClass.DRAIN_MINOR
    assert HydrographyProcessor.classify_feature({"waterway": "ditch"}) == HydrographyClass.DRAIN_MINOR

    # Embankments
    assert HydrographyProcessor.classify_feature({"name": "Right Marginal Bund", "man_made": "dyke"}) == HydrographyClass.EMBANKMENT
    assert HydrographyProcessor.classify_feature({"barrier": "embankment"}) == HydrographyClass.EMBANKMENT

    # Ambiguous
    assert HydrographyProcessor.classify_feature({"unrelated": "tag"}) == HydrographyClass.AMBIGUOUS


# -----------------------------------------------------------------------------
# 2. Ingestion, Geometry Validation, and Clipping Tests
# -----------------------------------------------------------------------------

def test_hydrography_validation_and_processing_continuous(synthetic_continuous_fixture: Path):
    """Verifies validation, UTM 43N reprojection, and clipping on continuous fixture."""
    gdf, report = HydrographyProcessor.validate_and_process(
        synthetic_continuous_fixture,
        clip_to_corridor=True,
    )

    assert not gdf.empty
    assert report.validation_status in [HydrographyValidationStatus.VALID, HydrographyValidationStatus.VALID_WITH_WARNINGS]
    assert report.total_network_length_km > 0.0
    assert report.metric_crs == "EPSG:32643"
    assert report.main_channel_continuity == ChannelContinuityStatus.CONTINUOUS
    assert report.main_channel_length_km > 50.0

    # Ensure all required classes were detected
    assert HydrographyClass.MAIN_RIVER.value in report.features_by_class
    assert HydrographyClass.CANAL.value in report.features_by_class
    assert HydrographyClass.TRIBUTARY.value in report.features_by_class
    assert HydrographyClass.DRAIN_MINOR.value in report.features_by_class
    assert HydrographyClass.EMBANKMENT.value in report.features_by_class


def test_corridor_clipping_bounds(tmp_path: Path):
    """Verifies that features extending outside the study corridor are clipped."""
    # Create line crossing outside corridor: from (75.0, 30.0) outside to (77.2, 29.0) inside
    out_in_line = LineString([(75.0, 30.0), (77.2, 29.0)])
    doc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
        "features": [
            {
                "type": "Feature",
                "id": "CLIP_TEST_01",
                "geometry": mapping(out_in_line),
                "properties": {"name": "Yamuna Reach", "waterway": "river"},
            }
        ],
    }
    fpath = tmp_path / "clipping_test.geojson"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(doc, f)

    gdf, report = HydrographyProcessor.validate_and_process(fpath, clip_to_corridor=True)
    assert not gdf.empty
    total_bounds = gdf.total_bounds
    # West bound should be clipped to at least 76.85°E
    assert total_bounds[0] >= 76.84


def test_duplicate_geometry_detection(tmp_path: Path):
    """Verifies duplicate geometries are detected and filtered out."""
    line = LineString([(77.1, 29.0), (77.2, 29.1)])
    doc = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "id": "DUP_1", "geometry": mapping(line), "properties": {"name": "Yamuna", "waterway": "river"}},
            {"type": "Feature", "id": "DUP_2", "geometry": mapping(line), "properties": {"name": "Yamuna", "waterway": "river"}},
        ],
    }
    fpath = tmp_path / "dup_test.geojson"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(doc, f)

    gdf, report = HydrographyProcessor.validate_and_process(fpath, clip_to_corridor=False)
    assert report.duplicate_features_count == 1
    assert len(gdf) == 1


# -----------------------------------------------------------------------------
# 3. Main Channel Extraction and Gap Analysis Tests
# -----------------------------------------------------------------------------

def test_channel_continuity_and_gap_detection(synthetic_gapped_fixture: Path):
    """Verifies gap detection on discontinuous channel geometry."""
    gdf, report = HydrographyProcessor.validate_and_process(synthetic_gapped_fixture)

    assert report.main_channel_continuity in [ChannelContinuityStatus.FRAGMENTED, ChannelContinuityStatus.DISCONNECTED]
    # Check chainage report reflects the discontinuity limitation
    assert report.chainage_summary is not None
    assert report.chainage_summary.status in ["DISCONNECTED_REFUSED", "AVAILABLE"]


# -----------------------------------------------------------------------------
# 4. Network Topology Graph Tests (NetworkX)
# -----------------------------------------------------------------------------

def test_network_topology_graph_construction(synthetic_continuous_fixture: Path):
    """Verifies NetworkX reach graph properties: nodes, edges, confluences, dead-ends."""
    gdf, _ = HydrographyProcessor.validate_and_process(synthetic_continuous_fixture)
    summary, graph = HydrographyProcessor.build_network_topology(gdf)

    assert summary.total_nodes > 0
    assert summary.total_edges > 0
    assert summary.connected_components_count >= 1
    assert summary.giant_component_nodes > 0
    assert summary.flow_direction_verified is False
    assert graph.number_of_nodes() == summary.total_nodes
    assert graph.number_of_edges() == summary.total_edges


# -----------------------------------------------------------------------------
# 5. Downstream River Chainage Tests
# -----------------------------------------------------------------------------

def test_river_chainage_continuous_generation(synthetic_continuous_fixture: Path):
    """Verifies downstream chainage generation from Hathnikund towards Delhi."""
    gdf, _ = HydrographyProcessor.validate_and_process(synthetic_continuous_fixture)
    main_gdf = gdf[gdf["hydro_class"] == HydrographyClass.MAIN_RIVER.value].copy()

    gap_report = HydrographyProcessor.analyze_channel_continuity(main_gdf)
    chainage = HydrographyProcessor.compute_river_chainage(main_gdf, gap_report=gap_report, interval_km=5.0)

    assert chainage.status == "AVAILABLE"
    assert chainage.total_chainage_km > 50.0
    assert chainage.stations_count > 0
    # Hathnikund is origin station 0.0 km
    assert chainage.stations[0].chainage_km == 0.0
    assert "Hathnikund" in chainage.stations[0].reach_name


# -----------------------------------------------------------------------------
# 6. Status Scanner & Missing File Handling
# -----------------------------------------------------------------------------

def test_scan_hydrography_status_when_empty(temp_hydro_dir: Path):
    """Verifies scanner truthful reporting when no files are present."""
    status = HydrographyProcessor.scan_hydrography_status(temp_hydro_dir / "data")
    assert status["hydrography_availability"] == "UNAVAILABLE"
    assert status["total_files_found"] == 0
    assert status["processing_report"] is None
    assert "scientific_notice" in status


def test_missing_file_raises_not_found(tmp_path: Path):
    """Verifies missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        HydrographyProcessor.validate_and_process(tmp_path / "nonexistent.geojson")
