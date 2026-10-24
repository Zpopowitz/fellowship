# MANIFEST - Boston SAR data

Generated 2026-10-24. Download method: `curl -L` with curl default User-Agent (see "Failures and deviations"). Verification output: `_logs/verify.json` (from `_logs/verify.py`). Raw download log: `_logs/dl_log.jsonl` (size + sha256 per file).

"Page last modified" = CKAN `metadata_modified` of the dataset page (data.boston.gov API `package_show`, saved as `_ckan_metadata.json` in each folder). Where the source is not CKAN it is stated per entry.

# Part A - Street and access layers

## A1_street_segments_sam: Boston Street Segments (SAM)
- Source page: https://data.boston.gov/dataset/boston-street-segments-sam-system
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-10-24T03:01:37.181530
- Notes: No width field in the column list (verified). REST layer FeatureServer/3 not queried; the GeoJSON export was downloaded. Only GeoJSON downloaded; CSV/SHP/KML exist on the page.
- **File** `A1_street_segments_sam/boston_street_segments_sam_system.geojson`
  - Download URL: https://data.boston.gov/dataset/b9b8b634-f28a-410f-9727-b53d0d006308/resource/e850cfd2-2c6e-4af6-9ac4-e03019412d1e/download/boston_street_segments_sam_system.geojson
  - Downloaded: 2026-10-24; size 22,442,575 bytes; sha256 006c9a6794f05828332689a6081fb00ead4b9e485382cff3fbf6eed9a54ba617
  - Rows/features/records: 19,440
  - Columns (39): `OBJECTID`, `SEGMENT_ID`, `L_F_ADD`, `L_T_ADD`, `R_F_ADD`, `R_T_ADD`, `STREET_ID`, `PRE_DIR`, `ST_NAME`, `ST_TYPE`, `SUF_DIR`, `ALTERNATE_NAME`, `CFCC`, `SPEEDLIMIT`, `ONEWAY`, `F_ZLEV`, `T_ZLEV`, `FT_COST`, `TF_COST`, `FT_DIR`, `TF_DIR`, `SHIELD`, `HWY_NUM`, `MUN_L`, `MUN_R`, `NBHD_L`, `NBHD_R`, `STATE00_L`, `STATE00_R`, `COUNTY00_L`, `COUNTY00_R`, `MCD00_L`, `MCD00_R`, `ZIP_L`, `ZIP_R`, `ownership`, `ROUTE_ID`, `Shape_Length`, `shape_wkt`

## A2_sidewalk_centerline: Sidewalk Centerline
- Source page: https://data.boston.gov/dataset/sidewalk-centerline
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2025-08-31T15:08:04.169835
- Notes: Vintage UNKNOWN (brief says description 2011 vs metadata 2023-12-18; CKAN metadata_modified shown above differs again). The GeoJSON is a zip (member Sidewalk_Centerline.geojson, 70,885,533 bytes uncompressed).
- **File** `A2_sidewalk_centerline/sidewalk_centerline_geojson.zip`
  - Download URL: https://data.boston.gov/dataset/67e1944c-b461-4ea6-8669-43969e8974ca/resource/a1720314-dd92-47ac-8bc4-7eaa4cadb77c/download/sidewalk_centerline_geojson.zip
  - Downloaded: 2026-10-24; size 15,389,567 bytes; sha256 10141ba8f7f06cb164594354c85aee033bb58f56f8d2a2979ec4ef226fe5b238
  - Rows/features/records: 110,031
  - Columns (4): `OBJECTID`, `TYPE`, `Shape_Length`, `shape_wkt`
  - Zip members: Sidewalk_Centerline.geojson (70,885,533 B)

## A3_pedestrian_ramps: Pedestrian Ramp Inventory
- Source page: https://data.boston.gov/dataset/6f4293b7-0189-4434-9342-fb600352d2ef
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-10-18T14:12:16.226644
- Notes: Completion year 2014 is from the brief, not verified.
- **File** `A3_pedestrian_ramps/pedestrian_ramp_inventory.geojson`
  - Download URL: https://data.boston.gov/dataset/6f4293b7-0189-4434-9342-fb600352d2ef/resource/e3faf098-1099-4eb2-98e9-ed17ff498476/download/pedestrian_ramp_inventory.geojson
  - Downloaded: 2026-10-24; size 20,156,861 bytes; sha256 bd536d78f31bc0f9e3a2802e7ee16ea8a5b7f9140751049c9cb06b74cf778eb3
  - Rows/features/records: 24,022
  - Columns (35): `OBJECTID`, `RAMP_ID`, `COND`, `INSP`, `ACCESS_`, `CROSS_`, `APRON_SL`, `LANDING_SL`, `LIP`, `PWD`, `CITYCODE`, `RCI`, `REPAIR_ALT`, `HIGHWAY`, `ADDRESS`, `NPR`, `REVEAL`, `SWK_WIDTH`, `CONST_DATE`, `SWK_MATL`, `MATL`, `CONST_PROG`, `RAMP_CAT`, `INSP_NOTES`, `INSP_DATE`, `CONST_NOTE`, `EST_COST`, `GIS_NOTES`, `AAB_COMP`, `PARENT`, `POINT_X`, `POINT_Y`, `ID2`, `AAB_LIKE_C`, `shape_wkt`

## A4_fire_hydrants: Fire Hydrants
- Source page: https://data.boston.gov/dataset/1f43041c-e2ff-4784-b537-3ecb7ceae066
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-10-18T14:07:12.819295
- Notes: Date conflict ("January 2019" vs metadata) from the brief: NOT resolved. Data vintage UNKNOWN.
- **File** `A4_fire_hydrants/fire_hydrants.geojson`
  - Download URL: https://data.boston.gov/dataset/1f43041c-e2ff-4784-b537-3ecb7ceae066/resource/1ce1845b-ab8e-4a82-a297-b8b00083a4ca/download/fire_hydrants.geojson
  - Downloaded: 2026-10-24; size 10,728,946 bytes; sha256 684e26859dad2489f8ba4194e872a079ebe28a8578bab5f110f382b64a2c7a2a
  - Rows/features/records: 13,747
  - Columns (29): `OBJECTID`, `OBJECTID_1`, `ANCILLARYR`, `ENABLED`, `FEATURE_ID`, `PLACEMENT_`, `PLACEMENT1`, `UPDATE_ID`, `UPDATE_DAT`, `SYNCH_FLAG`, `SYMBOL_ROT`, `FACILITY_I`, `SUBTYPE_CO`, `SERVICE_AR`, `INSTALL_DA`, `HYDRANT_MA`, `OWNER_CODE`, `METERED_FL`, `ADDRESS_NU`, `STREET_FEA`, `CROSS_STRE`, `LOC_SOURCE`, `MANUFACTUR`, `HYDRANT_MO`, `Longitude`, `Latitude`, `shape_wkt`, `POINT_X`, `POINT_Y`

## A5_work_zones: Public Works Active Work Zones
- Source page: https://data.boston.gov/dataset/public-works-active-work-zones
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-10-24T15:08:44.321719
- Notes: Single CSV snapshot of the download day; not a live feed.
- **File** `A5_work_zones/public_works_active_work_zones.csv`
  - Download URL: https://data.boston.gov/dataset/f9f57091-92f3-463a-8f1c-93e46361296d/resource/36fcf981-e414-4891-93ea-f5905cec46fc/download/tmp79j9lhth.csv
  - Downloaded: 2026-10-24; size 105,451 bytes; sha256 26b456a6b5857c8380b0d439978ba2fdb3eb2402c3b0bafad6331fca41d663e1
  - Rows/features/records: 460
  - Columns (22): `Neighborhood`, `Street`, `Address_1`, `Address_2`, `Intersection`, `From`, `To`, `Permittee`, `Contractor`, `Permit`, `Project_Category`, `Construction_Notes`, `Work_Schedule`, `ExpirationDate`, `Estimated_Completion_Date`, `Roadway_Plates_In_Use`, `Sidewalk_Plates_In_Use`, `Status`, `Trench_Length`, `Contact_Number`, `NumberOfWorkZones`, `District`

## A6_snow_emergency_routes: Snow Emergency Routes
- Source page: https://data.boston.gov/dataset/snow-emergency-routes
- License as stated: PDDL (CKAN license_title of dataset snow-emergency-routes)
- Page last modified: dataset metadata_modified 2026-10-18T14:13:53.994469; GeoJSON resource last_modified 2026-10-18T14:13:52.210980
- Notes: TWO files. (1) snow_emergency_routes.geojson = dataset-page export: 736 features, 5 columns. (2) layer7_query.geojson = layer 7 "Snow Emergency Routes" of https://gis.boston.gov/arcgis/rest/services/Infrastructure/OpenData/MapServer queried with where=1=1, outSR=4326: 8,422 features, many more columns. The two differ in row count and schema; the dataset page links its REST resource to a different service (services.arcgis.com/.../Ownership/FeatureServer). Whether layer 7 is the source of the dataset-page file is UNKNOWN. License of layer 7 itself: not stated on the MapServer; the PDDL above belongs to the dataset page.
- **File** `A6_snow_emergency_routes/layer7_query.geojson`
  - Download URL: UNKNOWN
  - Downloaded: UNKNOWN; size 24,808,992 bytes; sha256 UNKNOWN
  - Rows/features/records: 8,422
  - Columns (141): `OBJECTID_12`, `OBJECTID`, `Source`, `MaxDist`, `AdjSize`, `TrimDist`, `Length`, `Nearness`, `Comment`, `Adjusted`, `AdjAngDel`, `SrcState`, `ResState`, `SplitStart`, `SplitEnd`, `ManMatch`, `ManAdj`, `ManAdjCnt`, `MatchOrien`, `PrecOvrd`, `Reviewed`, `UpdateTime`, `SEGMENT_ID`, `STREET_ID`, `FULL_NAME`, `NAME_BODY`, `NAME_SUF`, `QA_LIFE`, `QA_FLAG`, `ORIG_FID`, `ID`, `L_F_ADD`, `L_T_ADD`, `R_F_ADD`, `R_T_ADD`, `PREFIX`, `PRETYPE`, `NAME`, `TYPE`, `SUFFIX`, `CFCC`, `POSTAL_L`, `POSTAL_R`, `ACC`, `NAME_TYPE`, `SHIELD`, `HWY_NUM`, `SEG_LEN`, `SPEED`, `ONE_WAY`, `FT_COST`, `TF_COST`, `TF_DIR`, `FT_DIR`, `NAME_FLAG`, `STATUS`, `A1_PREFIX`, `A1_PRETYPE`, `A1_NAME`, `A1_TYPE`, `A1_SUFFIX`, `A1_NM_TYPE`, `A1_SHIELD`, `A1_HWY_NUM`, `A1_FT_DIR`, `A1_TF_DIR`, `A1_NM_FLAG`, `A2_PREFIX`, `A2_PRETYPE`, `A2_NAME`, `A2_TYPE`, `A2_SUFFIX`, `A2_NM_TYPE`, `A2_SHIELD`, `A2_HWY_NUM`, `A2_FT_DIR`, `A2_TF_DIR`, `A2_NM_FLAG`, `A3_PREFIX`, `A3_PRETYPE`, `A3_NAME`, `A3_TYPE`, `A3_SUFFIX`, `A3_NM_TYPE`, `A3_SHIELD`, `A3_HWY_NUM`, `A3_FT_DIR`, `A3_TF_DIR`, `A3_NM_FLAG`, `A4_PREFIX`, `A4_PRETYPE`, `A4_NAME`, `A4_TYPE`, `A4_SUFFIX`, `A4_NM_TYPE`, `A4_SHIELD`, `A4_HWY_NUM`, `A4_FT_DIR`, `A4_TF_DIR`, `A4_NM_FLAG`, `A5_PREFIX`, `A5_PRETYPE`, `A5_NAME`, `A5_TYPE`, `A5_SUFFIX`, `A5_NM_TYPE`, `A5_SHIELD`, `A5_HWY_NUM`, `A5_FT_DIR`, `A5_TF_DIR`, `A5_NM_FLAG`, `STATE00_L`, `STATE00_R`, `COUNTY00_L`, `COUNTY00_R`, `MCD00_L`, `MCD00_R`, `PLACE00_L`, `PLACE00_R`, `TRACT00_L`, `TRACT00_R`, `BLOCK00_L`, `BLOCK00_R`, `F_ZLEV`, `T_ZLEV`, `SAM_R_FROM`, `SAM_R_TO`, `SAM_L_FROM`, `SAM_L_TO`, `OBJECTID_1`, `PWD`, `NAME_1`, `COMBO`, `DIST`, `PWD_DISTRICT`, `OBJECTID_12_13`, `FULL_NAME_1`, `RESP`, `Shape.STLength()`, `PWD.snow_arteries.area`, `PWD.snow_arteries.len`
- **File** `A6_snow_emergency_routes/snow_emergency_routes.geojson`
  - Download URL: https://data.boston.gov/dataset/cd2c0681-e1db-41a3-b7da-25449ec7eecb/resource/1b192b38-10b3-4a9b-bf16-cce8d1ff3baf/download/snow_emergency_routes.geojson
  - Downloaded: 2026-10-24; size 1,031,216 bytes; sha256 b70b3975470c0c923f3445d23a1ca94d8df74616e4576b478f3451062869aff8
  - Rows/features/records: 736
  - Columns (5): `OBJECTID`, `FULL_NAME`, `Responsibility`, `Shape_Length`, `shape_wkt`

# Part B - Buildings

## B7_buildings_inventory: Boston Buildings Inventory
- Source page: https://data.boston.gov/dataset/boston-buildings-inventory
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2020-05-11T20:55:14.986790
- Notes: On-site-verification caution is from the brief, not re-read. Height field: NONE in the column list. Closest: num_floors (fields-definitions.csv lists it under category "Height": "Number of floors"). Other files on the page (codes-and-classes, component info, PDF, XLSX) not downloaded.
- **File** `B7_buildings_inventory/building_inventory_021020.csv`
  - Download URL: https://data.boston.gov/dataset/f2a82340-1f9c-49fb-a60b-b5655c9a7931/resource/391a32e6-d4bb-48d3-a990-cb35a5768a40/download/building_inventory_021020.csv
  - Downloaded: 2026-10-24; size 47,663,162 bytes; sha256 2624de61b83bf2b7454039785b77f38bfdb94a5ff65d3670c3ddbe1cf9773250
  - Rows/features/records: 98,930
  - Columns (107): `id`, `pid_long`, `cm_id`, `building_typology`, `building_subtypology`, `use_class`, `sqft_class`, `year_built_class`, `st_num`, `st_name`, `st_name_suf`, `unit_num`, `zipcode`, `yr_built`, `land_sf`, `gross_area`, `living_area`, `sqft`, `num_floors`, `num_bldgs`, `units_res`, `units_com`, `units_mixed`, `ptype`, `ptype_list`, `lu`, `lu_list`, `assessor_category`, `assessor_description`, `own_occ`, `own_occ_list`, `owner_list`, `structure_class`, `structure_class_list`, `bldg_styl`, `bldg_styl_list`, `r_roof_typ`, `ext_fin`, `ext_fin_list`, `ext_cond_list`, `insulation_type`, `foundation_type`, `heat_typ`, `heat_typ_list`, `heating_system_fuel`, `ac`, `ac_list`, `ac_system_type`, `hot_water_system_fuel`, `electric_panel_info`, `has_pv`, `existing_ashp`, `existing_gshp`, `existing_shw`, `historic_district`, `landmark`, `flood`, `stormwater`, `last_major_renovation_date`, `total_site_energy_kbtu`, `perc_electricity`, `perc_gas`, `perc_steam`, `onsite_renewable_kwh`, `census_tract_number`, `ct_pop_disability`, `ct_pop_children_under_5`, `ct_pop_over_65`, `ct_pop_low_to_no_income`, `ct_pop_limited_english_proficiency`, `ct_pop_poc`, `ct_pop_med_illness`, `ct_perc_disability`, `ct_perc_children_under_5`, `ct_perc_over_65`, `ct_perc_low_to_no_income`, `ct_perc_limited_english_proficiency`, `ct_perc_poc`, `ct_perc_med_illness`, `ct_hh_income_200000_or_more`, `ct_perc_income_200000_or_more`, `cashp_only`, `cashp_and_elec_upgrade`, `cashp_outdoor`, `dashp_only`, `dashp_and_elec_upgrade`, `dashp_outdoor`, `gshp_only`, `gshp_and_elec_upgrade`, `vrf_only`, `vrf_and_elec_upgrade`, `awhp_only`, `awhp_and_elec_upgrade`, `hp_recommendation_count`, `insulate_attic`, `insulate_attic_converted`, `ext_roof_insulation`, `insulate_exposed_ducts`, `insulate_exposed_pipes`, `interior_wall_insulation_blow_in`, `exterior_wall_insulation_at_replacement`, `exterior_wall_insulation`, `interior_wall_insulation_board`, `insulate_spandrel`, `asbestos`, `seal_elevator_vent_shafts`, `env_recommendation_count`
- **File** `B7_buildings_inventory/fields-definitions.csv`
  - Download URL: https://data.boston.gov/dataset/f2a82340-1f9c-49fb-a60b-b5655c9a7931/resource/a57ac742-1175-40f7-9789-a9e68aad7de3/download/fields-definitions.csv
  - Downloaded: 2026-10-24; size 17,176 bytes; sha256 56144c17c2875ef3d5c0d873bbe3f564959fe82878f48df6bccdd65205a657c8
  - Rows/features/records: 107
  - Columns (5): `Category`, `Field Name`, `Source`, `Description`, `Notes`

## B8_bostonplans_3d: Boston Planning citywide 3D model (tile grid + documentation only)
- Source page: http://www.bostonplans.org/3d-data-maps/3d-smart-model/3d-data-download
- License as stated: PDDL, stated in the page text ("made available under the Open Data Commons Public Domain Dedication and License (PDDL)")
- Page last modified: Page: UNKNOWN (no date read from the page). HTTP Last-Modified: Bos3d_TileGrid.zip = Wed, 20 Dec 2023 19:39:59 GMT; 3D_Data_Documentation.pdf = Wed, 05 Feb 2025 15:18:20 GMT
- Notes: ONLY the tile grid (a SketchUp .skp) and the documentation PDF were fetched, as listed. The actual building model tiles (Bos3d_CityWide_Data) were NOT downloaded. The documentation PDF (p.11, name/description paired by text position) defines a HEIGHT_FT attribute: "The relative height from the Max Elevation of the model to the lowest [corner]", plus MAX_EL_FT / MIN_EL_FT / GND_EL_FT. Whether the 2011-baseline model files carry populated values is UNKNOWN (tiles not read).
- **File** `B8_bostonplans_3d/3D_Data_Documentation.pdf`
  - Download URL: http://maps.bostonplans.org/3d/3D_Data_Documentation.pdf
  - Downloaded: 2026-10-24; size 15,990,008 bytes; sha256 fe35bcd0e2da5a647f54f23083e60d0e25abf74175009c4eba28ecd511a919f3
  - Rows: n/a (not tabular or not parsed)
- **File** `B8_bostonplans_3d/Bos3d_TileGrid.zip`
  - Download URL: https://maps.bostonplans.org/3d/Bos3d_CityWide_Data/Bos3d_TileGrid.zip
  - Downloaded: 2026-10-24; size 3,828,416 bytes; sha256 c8dc7a0b9659ab90f260fcd1e01f19a77ba06653c3fbd3e867bca448abbd0a6c
  - Rows: n/a (not tabular or not parsed)
  - Zip members: Bos3d_TileGrid_SKPr14.skp (4,606,312 B)

## B9_massgis_structures: MassGIS Building Structures (2-D roofprints), Boston file
- Source page: https://www.mass.gov/info-details/massgis-data-building-structures-2-d
- License as stated: not stated (no license text found in the page text read)
- Page last modified: Page date: UNKNOWN (not extracted). HTTP Last-Modified of the statewide zip = 20 May 2026 (statewide file NOT downloaded).
- Notes: Boston-only file used instead of the 355 MB statewide zip. The file name `structures_poly_35` follows the page's city/town link pattern (structures_poly_N.zip); that N=35 is Boston was a HYPOTHESIS, then supported by the data itself: TOWN_ID=35 on 120,406 of 120,423 records and SOURCE='City of Boston' on 120,378. Page text says Boston polygons come from the City of Boston, March 2019. No height attribute among the 16 columns. `massgis-structures-download-links.xls` is the page's city/town link sheet (old .xls, not parsed).
- **File** `B9_massgis_structures/massgis-structures-download-links.xls`
  - Download URL: https://www.mass.gov/doc/massgis-structures-download-links/download
  - Downloaded: 2026-10-24; size 381,952 bytes; sha256 c1a938f5b436edadbd0141e30cd2abf2d37640a4b4ab301f9472413ffe651992
  - Rows: n/a (not tabular or not parsed)
- **File** `B9_massgis_structures/structures_poly_35_boston.zip`
  - Download URL: UNKNOWN
  - Downloaded: UNKNOWN; size 25,252,275 bytes; sha256 UNKNOWN
  - Rows/features/records: 120,423
  - Columns (16): `STRUCT_ID`, `SOURCE`, `SOURCETYPE`, `SOURCEDATE`, `SOURCEDATA`, `MOVED`, `AREA_SQ_FT`, `TOWN_ID`, `TOWN_ID2`, `TOWN_ID3`, `LOCAL_ID`, `EDIT_DATE`, `EDIT_BY`, `COMMENTS`, `SHAPE_AREA`, `SHAPE_LEN`
  - Zip members: structures_poly_35.cpg (5 B), structures_poly_35.dbf (55,756,395 B), structures_poly_35.prj (537 B), structures_poly_35.sbn (1,123,996 B), structures_poly_35.sbx (31,012 B), structures_poly_35.shp (39,796,580 B), structures_poly_35.shp.xml (78,796 B), structures_poly_35.shx (963,484 B)

# Part C - Per-building records

## C10_property_assessment: Property Assessment FY2026 + data key + occupancy codes
- Source page: https://data.boston.gov/dataset/property-assessment
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-05-22T15:38:49.055112
- Notes: Data key PDF page 1 says "Updated: December, 2024". GIS join service https://gis.boston.gov/arcgis/rest/services/Assessing/Property_Assessment_FY25/MapServer recorded only, not queried. Non-empty (not blank/0) counts of 184,552 rows: YR_BUILT 161,992; STRUCTURE_CLASS 17,625; RES_FLOOR 150,957; CD_FLOOR 66,000; GROSS_AREA 150,548. Data key page 2: RES_FLOOR = "Number of residential building stories", YR_BUILT = "Year property was built", STRUCTURE_CLASS = "Structural classification of building" (A Struct Steel, B Reinforced Concrete, C Brick/Concrete, D Wood/Frame, E Metal, R Residential).
- **File** `C10_property_assessment/fy2026-property-assessment-data_rev.csv`
  - Download URL: https://data.boston.gov/dataset/e02c44d2-3c64-459c-8fe2-e1ce5f38a035/resource/ee73430d-96c0-423e-ad21-c4cfb54c8961/download/fy2026-property-assessment-data_rev.csv
  - Downloaded: 2026-10-24; size 80,191,023 bytes; sha256 d0b656f516162c56a92782a255c731b967bd551b3e26cf412e080fdf041791fa
  - Rows/features/records: 184,552
  - Columns (67): `PID`, `CM_ID`, `GIS_ID`, `ST_NUM`, `ST_ALPHA`, `ST_NUM2`, `ST_NAME`, `UNIT_NUM`, `CITY`, `ZIP_CODE`, `BLDG_SEQ`, `NUM_BLDGS`, `LUC`, `LU`, `LU_DESC`, `BLDG_TYPE`, `OWN_OCC`, `OWNER`, `MAIL_ADDRESSEE`, `MAIL_STREET_ADDRESS`, `MAIL_CITY`, `MAIL_STATE`, `MAIL_ZIP_CODE`, `RES_FLOOR`, `CD_FLOOR`, `RES_UNITS`, `COM_UNITS`, `RC_UNITS`, `LAND_SF`, `GROSS_AREA`, `LIVING_AREA`, `LAND_VALUE`, `BLDG_VALUE`, `SFYI_VALUE`, `TOTAL_VALUE`, ` GROSS_TAX `, `YR_BUILT`, `YR_REMODEL`, `STRUCTURE_CLASS`, `ROOF_STRUCTURE`, `ROOF_COVER`, `INT_WALL`, `EXT_FNISHED`, `INT_COND`, `EXT_COND`, `OVERALL_COND`, `BED_RMS`, `FULL_BTH`, `HLF_BTH`, `KITCHENS`, `TT_RMS`, `BDRM_COND`, `BTHRM_STYLE1`, `BTHRM_STYLE2`, `BTHRM_STYLE3`, `KITCHEN_TYPE`, `KITCHEN_STYLE1`, `KITCHEN_STYLE2`, `KITCHEN_STYLE3`, `HEAT_TYPE`, `HEAT_SYSTEM`, `AC_TYPE`, `FIREPLACES`, `ORIENTATION`, `NUM_PARKING`, `PROP_VIEW`, `CORNER_UNIT`
- **File** `C10_property_assessment/property-assessment-fy2026-data-key.pdf`
  - Download URL: https://data.boston.gov/dataset/e02c44d2-3c64-459c-8fe2-e1ce5f38a035/resource/440f72b7-bb2c-4c37-971f-c1097d155559/download/property-assessment-fy2026-data-key.pdf
  - Downloaded: 2026-10-24; size 169,774 bytes; sha256 f62946109db73f54daa2e95272c6572ef93ccd0c04ce5f6e953c2684224f2ed2
  - Rows: n/a (not tabular or not parsed)
- **File** `C10_property_assessment/propertyoccupancycodes.pdf`
  - Download URL: https://data.boston.gov/dataset/e02c44d2-3c64-459c-8fe2-e1ce5f38a035/resource/d6c1268c-cd83-4dc3-a914-bba1ed59da6d/download/propertyoccupancycodes.pdf
  - Downloaded: 2026-10-24; size 55,727 bytes; sha256 7ff079564b0d2f534cdc41d0697f8d87b3f16e0e8bfabefa53dd7c06f1edde9c
  - Rows: n/a (not tabular or not parsed)

## C11_building_permits: Approved Building Permits + data dictionary
- Source page: https://data.boston.gov/dataset/approved-building-permits
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-10-24T15:10:09.594530
- Notes: Brief said 23 fields; the CSV header has 24 columns (verified). Snapshot of download day.
- **File** `C11_building_permits/approved_building_permits.csv`
  - Download URL: https://data.boston.gov/dataset/cd1ec3ff-6ebf-4a65-af68-8329eceab740/resource/6ddcd912-32a0-43df-9908-63574f8c7e77/download/tmpn5gbpnpu.csv
  - Downloaded: 2026-10-24; size 240,265,420 bytes; sha256 b5052342974522e28b2afb74a35d0a132b6b6cdae78799d2acf540ab1759ee58
  - Rows/features/records: 667,231
  - Columns (24): `permitnumber`, `worktype`, `permittypedescr`, `description`, `comments`, `applicant`, `declared_valuation`, `total_fees`, `issued_date`, `expiration_date`, `status`, `occupancytype`, `sq_feet`, `address`, `city`, `state`, `zip`, `ward`, `property_id`, `parcel_id`, `gpsy`, `gpsx`, `y_latitude`, `x_longitude`
- **File** `C11_building_permits/isd_approved_building_permits_data_dictionary.pdf`
  - Download URL: https://data.boston.gov/dataset/cd1ec3ff-6ebf-4a65-af68-8329eceab740/resource/65032067-580e-4167-9a5c-94fa8ac2d9a7/download/isd_approved_building_permits_data_dictionary.pdf
  - Downloaded: 2026-10-24; size 122,581 bytes; sha256 0d97a1a8e6063fa9a9ca80b224a1fc0544a496d2948171951577e00416873502
  - Rows: n/a (not tabular or not parsed)

## C12_building_violations: Building and Property Violations
- Source page: https://data.boston.gov/dataset/building-and-property-violations1
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-10-24T15:09:19.655719
- Notes: CKAN resource "size" field says 14 (not meaningful); actual file is 4,105,101 bytes.
- **File** `C12_building_violations/building_and_property_violations.csv`
  - Download URL: https://data.boston.gov/dataset/705244a6-70a6-4ff8-ab8e-56441aff18e7/resource/800a2663-1d6a-46e7-9356-bedb70f5332c/download/tmpilpychd0.csv
  - Downloaded: 2026-10-24; size 4,105,101 bytes; sha256 efc4c2f92c0a00b8a2a193836c3cf1b219c3c0bad09d96214a14bc901db8ec74
  - Rows/features/records: 17,493
  - Columns (24): `case_no`, `ap_case_defn_key`, `status_dttm`, `status`, `code`, `value`, `description`, `violation_stno`, `violation_sthigh`, `violation_street`, `violation_suffix`, `violation_city`, `violation_state`, `violation_zip`, `ward`, `contact_addr1`, `contact_addr2`, `contact_city`, `contact_state`, `contact_zip`, `sam_id`, `latitude`, `longitude`, `location`

# Part D - Incidents

## D13_fire_incidents: Boston Fire Incident Reporting
- Source page: https://data.boston.gov/dataset/fire-incident-reporting
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2026-10-18T22:41:37.115158; main resource last_modified 2026-10-18T22:41:37
- Notes: CKAN lists this resource size as 242,753,000; the downloaded file is 88,638,650 bytes (reason UNKNOWN; not investigated). The two code-list CSVs and the 2012/2013 files on the page were NOT downloaded (not listed in the brief). Columns include alarm_date and alarm_time; no apparatus and no arrival-time column.
- **File** `D13_fire_incidents/fire_incident_reporting.csv`
  - Download URL: https://data.boston.gov/dataset/ac9e373a-1303-4563-b28e-29070229fdfe/resource/91a38b1f-8439-46df-ba47-a30c48845e06/download/tmpd2wnqzrg.csv
  - Downloaded: 2026-10-24; size 88,638,650 bytes; sha256 6939948bb2d57901fa19e8a578535901ef6d55acd981ca24aadc017b2650cd0b
  - Rows/features/records: 601,721
  - Columns (19): `incident_number`, `exposure_number`, `alarm_date`, `alarm_time`, `incident_type`, `incident_category`, `incident_description`, `incident_detail`, `estimated_property_loss`, `estimated_content_loss`, `address`, `district`, `city_section`, `neighborhood`, `zip`, `location_type`, `location_subtype`, `property_use`, `property_description`

## D14_911_dispatch_counts: 911 Daily Dispatch Count by Agency
- Source page: https://data.boston.gov/dataset/911-daily-dispatch-count-by-agency
- License as stated: PDDL (CKAN license_title)
- Page last modified: dataset metadata_modified 2019-05-18T02:50:16.633696
- Notes: Date range Nov 2010 to Apr 2014 is from the brief; not checked against the Date column.
- **File** `D14_911_dispatch_counts/911-daily-dispatch-count-by-agency.csv`
  - Download URL: https://data.boston.gov/dataset/17129fad-fff9-4eac-ad74-51fb4bf63c22/resource/2459542e-7026-48e2-9128-ca29dd3bebf8/download/911-daily-dispatch-count-by-agency.csv
  - Downloaded: 2026-10-24; size 50,664 bytes; sha256 85ba95b5ad83fcb96a5968e26d920601e9ed57ef269335a5cd104f6bf00f6694
  - Rows/features/records: 1,268
  - Columns (8): `Date`, `Year`, `Month`, `DayOfYear`, `Total`, `BPD`, `BFD`, `EMS`

## D15: NFIRS public data (SKIPPED - large, awaiting your confirmation)
- Landing page: https://www.usfa.fema.gov/data-insights/nfirs/data/ (read; links to OpenFEMA)
- File list page: https://www.fema.gov/about/openfema/data-sets/fema-usfa-nfirs-annual-data (page text: "Last updated June 25, 2026"; page says zips range 132 MB to 822MB, but HEAD sizes in the TSV include files above 1 GB, e.g. nfirs_all_incident_pdr_2020.zip = 1,018,959,213 B)
- License: not stated on the pages read.
- Page statement: NFIRS decommissioned January 2026; 2025 is the last PDR year; files cover 1980-2025.
- Names + HEAD sizes + Last-Modified of 71 linked files: `E_location_only/nfirs_file_list_HEAD_sizes.tsv` (page snapshot beside it). Nothing downloaded.

# Part E - Location only (nothing downloaded)

- MassGIS LiDAR terrain (2013-2021 mosaic, incl. spring 2021 East MA): https://www.mass.gov/info-details/massgis-data-lidar-terrain-data . Page: "Date published: May 30, 2023; Last updated: May 30, 2023". License: not stated in the page text read. The page links DEM/hillshade/slope zips and a tile index; where point-cloud files are: UNKNOWN.
- USGS 3DEP point clouds: `s3://usgs-lidar-public` (location from the brief; not opened). "Public domain" is per the brief, NOT verified.
- MBTA GTFS feed (official): https://cdn.mbta.com/MBTA_GTFS.zip - linked from https://www.mbta.com/developers/gtfs . HEAD: 22,280,208 B, Last-Modified Wed, 21 Oct 2026 21:21:35 GMT. License: page says use "is governed by the MassDOT Developers License Agreement"; PDF: https://cdn.mbta.com/sites/default/files/2023-08/mbta-massdot-develop-license-agreement.pdf (terms not read). Docs: https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md . Whether the feed contains pathways.txt / entrances: UNKNOWN (zip not opened; one copy was fetched to a temp folder by mistake while testing the URL, and deleted).

# Part F - Robot-side code (cloned depth 1 into `F_robot_code/`; each is its own git repo)

| Repo | Commit | License | Notes |
|---|---|---|---|
| roborescue/rcrs-server | 56facf79fd62fb4e7596dfbfd07fb93cf1b6a21e (2026-10-12) | BSD-3-Clause (LICENSE head "BSD 3-Clause License"; GitHub API spdx BSD-3-Clause) | "osm2gml" appears in build.gradle and docs/map-creation (grep hit); not read further |
| hamidosooli/Multi-Robot-Task-Assignment | e09c4644fded1365b0485b753eb7944249177057 (2024-08-19) | **not stated** (no LICENSE file; GitHub API license null; no "licen" match in README) | no reuse rights shown; clarify before using |
| jr-robotics/robo-gym | f086bc90068c41ffd1889d290f3766d69291bf26 (2025-07-22) | MIT (LICENSE head; GitHub API spdx MIT) | **UNCONFIRMED** that this is the team's "robo-gym" |

# Known gaps (UNKNOWN, not fabricated)

Street and alley width; sprinkler and exit status per building; indoor layouts or BIM; Boston Fire Department pre-plans; unreinforced masonry inventory; tunnels and utilities; bridge clearances; live road-closure feed; robot capability and availability data.

# Building codes

780 CMR and 527 CMR not downloaded or scraped (ICC terms, per brief).

# Failures and deviations

1. First attempt used Python `urllib` on the data.boston.gov download URLs: HTTP 403 Forbidden on all 8 files, first with a browser-style User-Agent (my mistake: spoofing), then with an honest custom UA. Logs: `_logs/dl_log_attempt1_spoofedUA.jsonl`, `_logs/dl_log_attempt2_urllib_honestUA.jsonl`. Cause of the 403 is UNKNOWN (not investigated). I then switched to `curl` with its default UA, which received the site's normal 302 redirect to its S3 bucket and downloaded fine. No CAPTCHA, robots block or credentials involved.
2. Snow routes: dataset file and layer 7 disagree (see A6).
3. Fire incidents: CKAN size field vs actual size mismatch (see D13).
