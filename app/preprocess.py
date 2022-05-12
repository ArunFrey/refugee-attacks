import pandas as pd
from itertools import product


def to_timeseries(data, time="year", category=None, states_only=False):

    if time == "day":
        data["time"] = data["date"]

    elif time == "week":
        data["time"] = pd.to_datetime(data['date']).dt.to_period('W')
        data["time"] = data["time"].dt.to_timestamp()

    elif time == "month":
        data["time"] = data["date"].str.replace("-[0-9][0-9]$", "", regex=True)

    elif time == "year":
        data["time"] = data["year"]

    # gen district data
    data_kreis = (data
                  .groupby(["key", "time", "category_en"], as_index=False)
                  .agg(attacks=("attack_id", "count")))

    data_kreis_all = (data.groupby(["key", "time"], as_index=False)
                      .agg(attacks=("attack_id", "count"))
                      .assign(category_en="All"))

    data_kreis = pd.concat([data_kreis, data_kreis_all])

    # gen total data, to input 0s
    data_kreis_total = pd.DataFrame(product(data["key"].unique(),
                                            data["time"].unique(),
                                            data_kreis["category_en"].unique()),
                                    columns=["key", "time", "category_en"])

    # merge
    data_kreis = data_kreis_total.merge(data_kreis,
                                        on=["key", "time", "category_en"],
                                        how="left")

    # replace nas with 0
    data_kreis = data_kreis.apply(lambda x: x.fillna(0))

    # obtain name and population data
    data_kreis = data_kreis.merge(data.groupby("key", as_index=False)
                                  .agg(
        name=("name", "first"),
        state=("state", "first"),
        pop=("pop", "first")))

    # gen state data
    data_state = data_kreis.assign(key=data_kreis["key"]//1000)
    data_state = (data_state
                  .groupby(["key", "time", "category_en"], as_index=False)
                  .agg(
                      name=("state", "first"),
                      state=("state", "first"),
                      attacks=("attacks", "sum"),
                      pop=("pop", "sum")))

    # gen west data
    data_west = data_state[data_state["key"] <= 10].assign(key=-1)
    data_west = (data_west
                 .groupby(["key", "time", "category_en"], as_index=False)
                 .agg(
                     attacks=("attacks", "sum"),
                     pop=("pop", "sum"))
                 .assign(name="West Germany"))

    # gen east data
    data_east = data_state[data_state["key"] > 10].assign(key=-2)
    data_east = (data_east
                 .groupby(["key", "time", "category_en"], as_index=False)
                 .agg(
                     attacks=("attacks", "sum"),
                     pop=("pop", "sum"))
                 .assign(name="East Germany"))

    # gen germany data
    data_ger = data_kreis.assign(key=0)
    data_ger = (data_ger.groupby(["key", "time", "category_en"], as_index=False)
                .agg(
                    attacks=("attacks", "sum"),
                    pop=("pop", "sum"))
                .assign(name="Germany"))

    data_kreis = pd.concat([data_kreis, data_state, data_ger, data_west, data_east])

    if category is not None:
        data_kreis = data_kreis[data_kreis["category_en"] == category]

    if states_only == True:
        data_kreis = data_kreis[data_kreis["key"] <= 16]

    data_kreis = data_kreis.sort_values(["key", "time", "category_en"])

    return data_kreis
