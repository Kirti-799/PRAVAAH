"""
ml/spatial/inventory.py

Spatial Data Inventory and Local Repository Scanning Engine for PRAVAAH.
Catalogs candidate geospatial datasets (DEM, hydrography, administrative bounds)
with rigorous provenance tracking, acquisition status, and scientific limitations.

SCIENTIFIC INTEGRITY ENFORCEMENT:
- Strictly documents whether a dataset is physically present in the repository
  or unacquired.
- Never claims an elevation tile or boundary is available unless verified.
- Documents exact access blockers (open portal authentication, transboundary restriction, etc.).
"""

from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class SpatialDatasetCategory(str, Enum):
    ELEVATION_DEM = "ELEVATION_DEM"
    HYDROGRAPHY_RIVER = "HYDROGRAPHY_RIVER"
    ADMINISTRATIVE_BOUNDARY = "ADMINISTRATIVE_BOUNDARY"
    SATELLITE_INUNDATION = "SATELLITE_INUNDATION"
    EXPOSURE_INFRASTRUCTURE = "EXPOSURE_INFRASTRUCTURE"


class SpatialDataStatus(str, Enum):
    UNAVAILABLE_IN_REPOSITORY = "UNAVAILABLE_IN_REPOSITORY"
    CANDIDATE_UNACQUIRED = "CANDIDATE_UNACQUIRED"
    LOCAL_PRESENT_UNVALIDATED = "LOCAL_PRESENT_UNVALIDATED"
    LOCAL_PRESENT_VALIDATED = "LOCAL_PRESENT_VALIDATED"


@dataclass
class SpatialDatasetEntry:
    dataset_id: str
    name: str
    category: SpatialDatasetCategory
    source_agency: str
    source_url: str
    license_terms: str
    geographic_coverage: str
    coordinate_reference_system: str
    spatial_resolution: str
    vertical_units: str
    nodata_representation: str
    current_status: SpatialDataStatus
    expected_local_path: str
    actual_local_path: Optional[str]
    acquisition_blockers: str
    scientific_limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "category": self.category.value,
            "source_agency": self.source_agency,
            "source_url": self.source_url,
            "license_terms": self.license_terms,
            "geographic_coverage": self.geographic_coverage,
            "coordinate_reference_system": self.coordinate_reference_system,
            "spatial_resolution": self.spatial_resolution,
            "vertical_units": self.vertical_units,
            "nodata_representation": self.nodata_representation,
            "current_status": self.current_status.value,
            "expected_local_path": self.expected_local_path,
            "actual_local_path": self.actual_local_path,
            "acquisition_blockers": self.acquisition_blockers,
            "scientific_limitations": self.scientific_limitations,
        }


class SpatialInventoryCatalog:
    """Authoritative registry of spatial datasets for the Yamuna River corridor."""

    @classmethod
    def get_catalog(cls) -> List[SpatialDatasetEntry]:
        return [
            SpatialDatasetEntry(
                dataset_id="SRTM_30M_GLOBAL",
                name="NASA SRTM 1 Arc-Second Global Elevation (SRTMGL1 v003)",
                category=SpatialDatasetCategory.ELEVATION_DEM,
                source_agency="NASA / USGS Land Processes Distributed Active Archive Center (LP DAAC)",
                source_url="https://lpdaac.usgs.gov/products/srtmgl1v003/",
                license_terms="Public Domain (NASA Open Data Policy)",
                geographic_coverage="Tiles N28E077, N29E077, N30E077 (Upper-Middle Yamuna Plain)",
                coordinate_reference_system="EPSG:4326 (WGS 84, EGM96 Geoid vertical datum)",
                spatial_resolution="1 arc-second (~30 meters)",
                vertical_units="meters (m) above EGM96 geoid",
                nodata_representation="-32768",
                current_status=SpatialDataStatus.UNAVAILABLE_IN_REPOSITORY,
                expected_local_path="data/raw/spatial/dem/srtm_yamuna_30m.tif",
                actual_local_path=None,
                acquisition_blockers=(
                    "Requires Earthdata Login account and credentialed automated download script or manual tile retrieval. "
                    "Tiles N28E077, N29E077, N30E077 not yet committed to repository."
                ),
                scientific_limitations=[
                    "Acquired in February 2000 (C-band radar); radar reflective surface includes tree canopies and urban structures.",
                    "Does not reflect riverbed aggradation, siltation, or new flood guide bunds constructed post-2000.",
                    "Radar speckle and void-filling interpolation can introduce vertical bias in low-relief floodplains.",
                ],
            ),
            SpatialDatasetEntry(
                dataset_id="COPERNICUS_GLO30",
                name="Copernicus Digital Elevation Model GLO-30",
                category=SpatialDatasetCategory.ELEVATION_DEM,
                source_agency="European Space Agency (ESA) / Airbus Defence and Space",
                source_url="https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model",
                license_terms="Copernicus Open Access Policy (Free for commercial and non-commercial research)",
                geographic_coverage="Upper-to-Middle Yamuna Plain (Haryana to Delhi NCR)",
                coordinate_reference_system="EPSG:4326 (WGS 84, EGM2008 Geoid vertical datum)",
                spatial_resolution="1 arc-second (~30 meters)",
                vertical_units="meters (m) above EGM2008 geoid",
                nodata_representation="-32767.0",
                current_status=SpatialDataStatus.UNAVAILABLE_IN_REPOSITORY,
                expected_local_path="data/raw/spatial/dem/copernicus_glo30_yamuna.tif",
                actual_local_path=None,
                acquisition_blockers=(
                    "Requires AWS S3 / Planetary Computer public bucket access script or ESA Copernicus portal download. "
                    "Raster files have not been staged in data/raw/spatial/dem/."
                ),
                scientific_limitations=[
                    "Compiled from TanDEM-X radar data (2011–2015 epoch).",
                    "Provides surface elevation (DSM), including partial tree canopy and structures.",
                    "Water bodies are flattened using hydrological flattening masks, which may alter thalweg profiles.",
                ],
            ),
            SpatialDatasetEntry(
                dataset_id="BHUVAN_CARTODEM_30M",
                name="ISRO Bhuvan CartoDEM 30m Version 3R1",
                category=SpatialDatasetCategory.ELEVATION_DEM,
                source_agency="National Remote Sensing Centre (NRSC) / ISRO",
                source_url="https://bhuvan-app1.nrsc.gov.in/data/download/index.php",
                license_terms="Government of India Open Access for registered Indian users",
                geographic_coverage="National coverage; Yamuna corridor 76.5E–78.0E, 28.0N–31.0N",
                coordinate_reference_system="EPSG:4326 (WGS 84)",
                spatial_resolution="30 meters",
                vertical_units="meters (m) above WGS84 ellipsoid",
                nodata_representation="-9999",
                current_status=SpatialDataStatus.UNAVAILABLE_IN_REPOSITORY,
                expected_local_path="data/raw/spatial/dem/cartodem_yamuna_30m.tif",
                actual_local_path=None,
                acquisition_blockers="Requires OTP-authenticated Bhuvan user credentials; bulk API downloads restricted.",
                scientific_limitations=[
                    "Stereo optical photogrammetry artifacts over water bodies and dense clouds.",
                    "Ellipsoidal height requires conversion to orthometric height (MSL) using local geoid models.",
                ],
            ),
            SpatialDatasetEntry(
                dataset_id="OSM_YAMUNA_HYDROGRAPHY",
                name="OpenStreetMap Yamuna Corridor Waterways & Embankments",
                category=SpatialDatasetCategory.HYDROGRAPHY_RIVER,
                source_agency="OpenStreetMap Contributors / Geofabrik",
                source_url="https://download.geofabrik.de/asia/india.html",
                license_terms="Open Database License (ODbL 1.0)",
                geographic_coverage="Haryana & Delhi NCT (Yamunanagar to Delhi)",
                coordinate_reference_system="EPSG:4326 (WGS 84)",
                spatial_resolution="Vector features (polylines and polygons)",
                vertical_units="N/A",
                nodata_representation="NULL",
                current_status=SpatialDataStatus.UNAVAILABLE_IN_REPOSITORY,
                expected_local_path="data/raw/spatial/hydrography/osm_yamuna_waterways.geojson",
                actual_local_path=None,
                acquisition_blockers="Requires clipping India / Northern Zone OSM extract to corridor bounds.",
                scientific_limitations=[
                    "Crowdsourced geometry with variable temporal synchronization.",
                    "Embankments (man_made=dyke/embankment) often lack crest elevation attributes.",
                ],
            ),
            SpatialDatasetEntry(
                dataset_id="DDA_O_ZONE_FLOODPLAIN",
                name="Delhi Master Plan Zone-O (River Yamuna Floodplain Demarcation)",
                category=SpatialDatasetCategory.ADMINISTRATIVE_BOUNDARY,
                source_agency="Delhi Development Authority (DDA) / Delhi I&FC",
                source_url="https://dda.gov.in/master-plan-2021",
                license_terms="Public Administrative Planning Record",
                geographic_coverage="Wazirabad Barrage to Okhla Barrage (~22 km Delhi urban corridor)",
                coordinate_reference_system="EPSG:4326 / Local Survey Grid",
                spatial_resolution="Vector polygon",
                vertical_units="N/A",
                nodata_representation="NULL",
                current_status=SpatialDataStatus.UNAVAILABLE_IN_REPOSITORY,
                expected_local_path="data/raw/spatial/boundaries/delhi_dda_zone_o.geojson",
                actual_local_path=None,
                acquisition_blockers="Official GIS shapefile restricted across municipal agencies; published predominantly as static PDF plans.",
                scientific_limitations=[
                    "Administrative regulatory planning zone, NOT a dynamic hydraulic inundation model.",
                    "Does not indicate water depth or flow velocity under specific flood discharges.",
                ],
            ),
        ]

    @classmethod
    def scan_repository_dem_status(cls, data_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Scans data/raw/spatial/dem/ for physical DEM raster files.
        If files are present, validates their metadata and statistics.
        If absent, returns a transparent UNAVAILABLE status report.
        """
        base_dir = data_dir or (Path(__file__).resolve().parents[2] / "data")
        dem_dir = base_dir / "raw" / "spatial" / "dem"
        dem_dir.mkdir(parents=True, exist_ok=True)

        # Search for .tif and .tiff files
        tif_files = sorted(list(dem_dir.glob("*.tif")) + list(dem_dir.glob("*.tiff")))

        if not tif_files:
            return {
                "dem_availability": "UNAVAILABLE",
                "scanned_directory": str(dem_dir),
                "total_files_found": 0,
                "active_dem_file": None,
                "validation_report": None,
                "acquisition_guide": {
                    "instructions": (
                        "Place raw GeoTIFF tiles for the Yamuna River reach into data/raw/spatial/dem/. "
                        "Recommended datasets: NASA SRTMGL1 (30m) or Copernicus GLO-30 (30m). "
                        "Required geographic extent: West 76.85°E, South 28.50°N, East 77.60°E, North 30.40°N."
                    ),
                    "accepted_formats": [".tif", ".tiff"],
                    "required_properties": [
                        "Valid georeferenced CRS (EPSG:4326 or EPSG:32643)",
                        "Elevations in meters above mean sea level / EGM geoid",
                        "Valid NoData mask (-32768, -9999, etc.)",
                    ],
                },
                "scientific_notice": (
                    "DEM data is currently UNAVAILABLE in the repository. "
                    "PRAVAAH strictly refuses to fabricate synthetic elevation rasters for operational use."
                ),
            }

        # Inspect the primary DEM file found
        primary_file = tif_files[0]
        from ml.spatial.dem import DEMValidator
        report = DEMValidator.validate_file(primary_file)

        return {
            "dem_availability": "AVAILABLE",
            "scanned_directory": str(dem_dir),
            "total_files_found": len(tif_files),
            "all_files": [f.name for f in tif_files],
            "active_dem_file": primary_file.name,
            "validation_report": report.to_dict(),
            "scientific_notice": (
                "DEM file detected and validated. Outputs represent preliminary topographical surface inspection."
            ),
        }
