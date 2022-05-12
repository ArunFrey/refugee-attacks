import numpy as np
import pandas as pd


def split_categories(data,
                     var_name="category_de", criteria="& "):
    '''
    Splits rows with multiple categories in var_name into multiple rows
    based on criteria. Defaults to var_name == "category_de"
    and criteria == " &"
    '''
    data[var_name] = data[var_name].str.split(criteria)
    data_split = data.explode(var_name)
    data_split[var_name] = data_split[var_name].str.strip()

    print(f"...{len(data_split) - len(data)} rows added because of "
          f"multiple categories in {var_name}")
    return data_split


def replace_missing_categories(data,
                               var_name="category_de"):
    '''
    Assigns missing category to 'other'.
    '''
    na_vals = data[var_name].isna().sum()

    data[var_name] = data[var_name].replace(np.nan, "Sonstige Angriffe")

    print(f"...{na_vals} NaN values in {var_name} were recategorised as 'Other attack'")

    return(data)


def english_categories(data,
                       input_var="category_de", output_var="category_en"):
    de_to_en = {
        "Sonstige Angriffe": "Other",
        "Tätlicher Übergriff/Körperverletzung": "Assault",
        "Kundgebung/Demo": "Demonstration",
        "Verdachtsfall": "Suspected/unconfirmed",
        "Brandanschlag": "Arson"
    }
    data[output_var] = data[input_var].map(de_to_en)
    return data


def clean_source(data, var_name="source"):
    data[var_name] = data[var_name].str.replace("Quelle:", "").str.strip()
    return data


def clean_description(data, var_name="description_de"):
    data[var_name] = data[var_name].str.strip()
    return data


def sort_date(data, var_name="date"):
    # year style changes in 2017
    data.loc[data['year'] < 2017, var_name] = pd.to_datetime(
        data.loc[data['year'] < 2017, var_name], format="%Y-%m-%d",
        errors='coerce')
    data.loc[data['year'] >= 2017, var_name] = pd.to_datetime(
        data.loc[data['year'] >= 2017, var_name], format="%d.%m.%Y",
        errors='coerce')

    data[var_name] = pd.to_datetime(data[var_name])

    data = data.sort_values(by=var_name)

    return data


def replace_city_vals(data):

    # single condition:
    # specify which names need replacing
    city_vals = dict(
        {
            "Massow": "Massow (LDS)",
            "Haspe (Hcityn)": "Haspe, Hcityn",
            "Marke, Raguhn-Jeßnitz": "Marke",
            "Kirchheim im Schwarzwald": "Kirchheim in Schwaben",
            "Berlin-Hohenschönhausen": "Neu-Hohenschönhausen, Berlin",
            "Einsiedel": "Einsiedel, Chemnitz",
            "Merkers": "Merkers-Kieselbach",
            "Frankenthal in der Pfalz": "Frankenthal (Pfalz)",
            "Gymnich, Erfstadt": "Gymnich Erftstadt",
            "Langenfeld im Rheinland": "Langenfeld",
            "Forst in der Lausitz": "Forst (Lausitz)",
            "Merseburg an der Saale": "Merseburg",
            "Schwedt an der Oder": "Schwedt (Oder)",
            "Naumburg an der Saale": "Naumburg (Saale)",
            "Naumburg": "Naumburg (Saale)",
            "Hebertshausen (Kreis Dachau)": "Hebertshausen",
            "Wedel in Holstein": "Wedel",
            "Alsleben an der Saale": "Alsleben (Saale)",
            "Saalfeld an der Saale": "Saalfeld (Saale)",
            "Schnattenberg": "Schattenberg",
            "Würnsdorf": "Zossen",
            "Ibbenbühren": "Ibbenbüren",
            "Bad Kronzingen": "Bad Krozingen",
            "Neukirch in der Lausitz": "Neukirch/Lausitz"
        }
    )

    data = data.replace({"city": city_vals})

    conditions = [
        (data["city"] == "Halle") &
        (data["state"] == "Sachsen-Anhalt"),
        (data["city"] == "Halle") &
        (data["state"] == "Nordrhein-Westfalen"),
        (data["city"] == "Wittenberge") &
        (data["state"] == "Sachsen-Anhalt"),
        (data["city"] == "Berline") &
        (data["date"] == "2017-02-21"),
    ]

    choices = ["Halle (Saale)", "Halle (Westfalen)", "Wittenberg", "Berlin"]

    data["city"] = np.select(conditions, choices, default=data["city"])

    return data


def replace_state_vals(data):

    conditions = [
        (data["city"] == "Halle") &
        (data["state"] == "Sachsen"),
        (data["city"] == "Haltern") &
        (data["state"] == "Brandenburg"),
        (data["city"] == "Geldern") &
        (data["state"] == "Niedersachsen"),
        (data["city"] == "Goslar") &
        (data["state"] == "Hessen"),
        (data["city"] == "Naumburg (Saale)") &
        (data["state"] == "Sachsen"),
        (data["city"] == "Leverkusen") &
        (data["state"] == "Niedersachsen"),
        (data["city"] == "Röttenbach") &
        (data["state"] == "Baden-Württemberg"),
        (data["city"] == "Hildesheim") &
        (data["state"] == "Baden-Württemberg"),
        (data["city"] == "Dessau") &
        (data["state"] == "Sachsen"),
    ]

    choices = ["Sachsen-Anhalt",
               "Nordrhein-Westfalen",
               "Nordrhein-Westfalen",
               "Niedersachsen",
               "Sachsen-Anhalt",
               "Nordrhein-Westfalen",
               "Bayern",
               "Niedersachsen",
               "Sachsen-Anhalt"
               ]

    data["state"] = np.select(conditions, choices, default=data["state"])

    return data


def clean_data(data):
    print("Cleaning data...")
    print("...splitting categories")
    data = split_categories(data, var_name="category_de")
    print("...replacing missing categories")
    data = replace_missing_categories(data, var_name="category_de")
    print("...adding english categories")
    data = english_categories(data, input_var="category_de",
                              output_var="category_en")
    print("...cleaning source column")
    data = clean_source(data, var_name="source")
    print("...cleaning description_de column")
    data = clean_description(data, var_name="description_de")
    print("...replacing city columns values")
    data = replace_city_vals(data)
    print("...replacing state columns values")
    data = replace_state_vals(data)
    print("...sorting by date column")
    data = sort_date(data, var_name="date")
    print("Data cleaned")
    return data
