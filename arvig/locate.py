import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim, GoogleV3
import csv
import logging


def get_location(address, api_key=None):

    if api_key is not None:
        locator = GoogleV3(api_key=api_key)
    else:
        logging.info("Google API key missing. Switching to Nominatim.")
        locator = Nominatim(user_agent="geocoder")

    geocode = RateLimiter(locator.geocode, min_delay_seconds=1 / 20)

    results = geocode(address)

    # if there's no results, return empty results.
    if (results is None) or (len(results) == 0):
        output = {
            "address": address,
            "address_formatted": None,
            "latitude": None,
            "longitude": None,
        }
    else:
        output = {
            "address": address,
            "address_formatted": results.address,
            "latitude": results.latitude,
            "longitude": results.longitude,
        }

    return output


def add_locations(data, output_file, api_key=None):

    if hasattr(data, "address"):
        addresses = data["address"]

    else:
        try:
            print("No address, using 'city' and 'state' columns instead.")
            data["address"] = data["city"] + ", " + data["state"]
            addresses = data["address"]
        except Exception:
            raise ValueError("Missing city and state in input data")

    try:
        output = pd.read_csv(output_file)
        addresses_done = output["address"]
    except Exception:
        print("No location output file. Generating new...")
        addresses_done = []

    # select unique addresses, then subset leftover
    addresses = list(set(addresses))
    addresses_left = list(set(addresses).difference(addresses_done))
    results = []

    with open(output_file, "a+", newline="\n") as csv_output:

        # header
        cols = ["address", "address_formatted", "latitude", "longitude"]
        writer = csv.DictWriter(
            csv_output, delimiter=",", lineterminator="\n", fieldnames=cols
        )

        # add header if file does not exist
        if csv_output.tell() == 0:
            writer.writeheader()

        for address in addresses_left:
            location = get_location(address, api_key)
            results.append(location)
            writer.writerow(location)

            # Print status every 100 addresses
            if len(results) % 100 == 0:
                print("Completed {} of {} addresses"
                      .format(len(results), len(addresses_left)))

    if len(results) == len(addresses_left):
        print(f"Finished geocoding all {len(addresses_left)} addresses")
        print(f"Merging location to data")
        locations = pd.read_csv(output_file)
        data = data.merge(locations, how="left", on="address")
        return data
