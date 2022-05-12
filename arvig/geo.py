import geopandas as gpd


def merge_with_geo(data, geo_file_path):
    # load geo county file
    geo = gpd.read_file(geo_file_path, encoding="utf-8")
    geo = geo.rename(columns={
        "AGS": "key",
        "GEN": "name",
        "BEZ": "key_type",
        "EWZ": "pop"
    }
    )
    geo = geo[["key", "name", "key_type", "pop", "geometry"]]
    gdf = gpd.GeoDataFrame(
        data, geometry=gpd.points_from_xy(data.longitude, data.latitude)
    )

    # set crs
    target_crs = {"datum": "WGS84", "proj": "merc"}
    gdf.set_crs(epsg=4326, inplace=True)
    geo = geo.to_crs(crs=target_crs)
    gdf = gdf.to_crs(crs=target_crs)

    # merge
    gdf = gpd.sjoin(gdf, geo, how="right", predicate="within")

    # set index
    gdf = gdf.set_index("index_left")
    gdf.index.name = "attack_id"
    gdf = gdf.sort_index()

    return gdf
