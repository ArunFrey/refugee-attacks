import pandas as pd
import arvig
from config import google_key


def main():
    # download all data
    ch = arvig.getChronicle(2014, 2021)
    # load all data
    df = ch.load_all("data/raw/")
    # clean data
    df = arvig.clean_data(df)
    # add locations
    df = arvig.add_locations(df, output_file="data/raw/locations.csv", api_key=google_key)
    # translate descriptions
    df = arvig.add_translate(df, output_file="data/raw/translate.csv")
    # merge with location data
    gdf = arvig.merge_with_geo(df, geo_file_path="data/raw/shp/simplified/KRS_2014_ew.shp")
    print(f"{gdf.shape} ({df.shape[0]-gdf.shape[0]} rows lost because of missing location data.)")
    # select columns of interest
    gdf = gdf[["date", "year",
               "key", "name", "state", "key_type", "pop",
               "category_en", "description_en", "source",
               "latitude", "longitude", "geometry"]]
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    # save files
    df.to_csv("data/arvig.csv")
    gdf.to_file("data/arvig.geojson", driver='GeoJSON')
    print(f"Final dataset: {df.shape}")


if __name__ == "__main__":
    main()
