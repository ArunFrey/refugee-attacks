
from dash import callback_context, Dash, dcc, html, Input, Output

import os
import pathlib
import plotly.express as px

from colour import Color
import pandas as pd
import geopandas as gpd
from app import to_timeseries

app = Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Anti-refugee violence in Germany"
server = app.server
app.config["suppress_callback_exceptions"] = True

paper_bgcolor = '#1e2130'
plot_bgcolor = '#1e2130'
font_color = "white"
grid_color = "lightgrey"


BINS = [-1, 0, 0.5, 1, 1.5, 2, 2.5, 5, 7.5, 10, 15, 50]
LABELS = ["          00.00", "00.10 - 00.50", "00.51 - 01.00", "01.01 - 01.50", "01.51 - 02.00", "02.01 - 02.50",
          "02.51 - 05.00", "05.01 - 07.00", "07.01 - 10.00", "10.01 - 15.00", "15.01 - 50.00"]
COLORSCALE = ["antiquewhite"] + \
    [c.hex for c in Color("lightyellow").range_to(Color("darkred"), 10)]
COLORSCALE
COLOR_MAP = dict(zip(LABELS, COLORSCALE))
COLOR_BAR = {
    "All": "#F4D44D",
    "Arson": "#DB073D",
    "Assault": "#8EC7D2",
    "Demonstration": "#0D6986",
    "Other": "#07485B"}
COLOR_TIME = {
    "Germany": "#8CBEB2",
    "East Germany": "#F2EBBF",
    "West Germany": "#F3B562",
}
COLOR_STATE = "#F06060"


def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[
                    html.H5("Anti-refugee violence Dashboard"),
                    html.H6("Visualising xenophobic hostility across Germany"),
                ],
            ),
            html.Div(
                id="banner-logo",
                children=[
                    html.Button(
                        id="learn-more-button", children="LEARN MORE", n_clicks=0
                    ),
                    html.A(
                        html.Img(id="logo", src=app.get_asset_url("dash-logo-new.png")),
                        href="https://plotly.com/dash/",
                    ),
                ],
            ),
        ],
    )


def build_top_panel():
    return html.Div(
        className='row', children=[

            html.Div(children=[

                html.Label(["Select unit"],
                           style={'font-weight': 'bold', 'text-align': 'center'}),

                dcc.Dropdown(
                    id="unit-id",
                    options=["State", "District"],
                    value='District',
                    searchable=False,
                    clearable=False
                )
            ], style=dict(width='20%')),

            html.Div(children=[

                html.Label(["Select category"],
                           style={'font-weight': 'bold', 'text-align': 'center'}),

                dcc.Dropdown(
                    id="category-id",
                    options=["All", "Arson", "Assault", "Demonstration",
                             "Other"],
                    value='All',
                    searchable=False,
                    clearable=False
                )
            ], style=dict(width='20%')),

            html.Div(children=[

                html.Label(["Drag the slider to change the year"],
                           style={'font-weight': 'bold', 'text-align': 'center'}),

                dcc.Slider(
                    int(str(df_year['time'].min())),
                    int(str(df_year['time'].max())),
                    step=None,
                    id='year-id',
                    value=2016,
                    marks={str(time): str(time) for time in df_year['time'].unique()},
                ),
            ], style=dict(width='60%')),

        ], style=dict(display='flex'))


def build_bottom_panel():
    return html.Div(
        className="row", children=[

            html.Div(children=[

                     html.Label(["Select variable"],
                                style={'font-weight': 'bold', 'text-align': 'center'}),

                     dcc.Dropdown(
                         options=[
                             {'label': 'Attacks/100,000', 'value': 'attack_pop'},
                             {'label': 'Attacks (#)', 'value': 'attacks'},
                         ],
                         value="attacks",
                         id="var-id",
                     ),
                     ], style=dict(width='20%')),


            html.Div(children=[

                     html.Label(["Select time window"],
                                style={'font-weight': 'bold', 'text-align': 'center'}),

                     dcc.Dropdown(
                         id="timeunit-id",
                         options=["Yearly", "Monthly", "Weekly"],
                         value="Weekly",
                     ),
                     ], style=dict(width='20%')),


            html.Div(children=[

                     html.Label(["Drag both sliders to select the year range"],
                                style={'font-weight': 'bold', 'text-align': 'center'}),

                     dcc.RangeSlider(
                         int(str(df_year['time'].min())),
                         int(str(df_year['time'].max())),
                         step=None,
                         id='yearrange-id',
                         value=[2014, 2016],
                         marks={str(time): str(time) for time in df_year['time'].unique()},
                     ),
                     ], style=dict(width='60%')),
        ], style=dict(display='flex'))


def generate_modal():
    return html.Div(
        id="markdown",
        className="modal",
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="markdown-text",
                        children=dcc.Markdown(
                            children=(
                                """
                        ### Data

                        This dashboard visualises the distribution of anti-refugee attacks across Germany since 2014.

                        Each instance of anti-refugee violence visualised in this dashboard was gathered by the Amadeu Antonion Stiftung and PRO ASYL.
                        You can find each listing [here](https://www.mut-gegen-rechte-gewalt.de/service/chronik-vorfaelle).



                        ### Variables

                        - **Anti-refugee attacks**: Number of anti-refugee attacks. The data differentiates between the following attack types:
                            - **Arson**: Arson attacks on refugee accommodation centres or other refugee housing.
                            Refugee shelters may have been operating, planned, or under construction at the time of attack.
                            - **Assault**: Physical assaults on refugees or asylum seekers.
                            Assaults are only included if the refugee or asylum seeking status of the victim is known.
                            - **Demonstration**: Anti-refugee or anti-immigrant protests and demonstrations.
                            Note that since 2016, the data only includes demonstrations that led to some judicial violation, and so does not capture the full extent of anti-refugee mobilisation in Germany.
                            - **Other**: Miscellaneous attacks.

                        - **Anti-refugee attacks/100,000**: Anti-refugee attacks in each locality (district, state, region) divided by the number of 100,000 residents in that locality.

                        ### About

                        This dashboard was created by [Arun Frey](https://scholar.google.com/citations?user=TNyIGTcAAAAJ&hl=en&oi=ao), a postdoctoral researcher at the University of Oxford and the Leverhulme Centre for Demographic Science.
                        Arun's research focuses on the opportunities of and challenges with refugee integration.
                        He has written on how terrorist attacks increase anti-refugee hostility among the native population and subject refugees to more violence, vitriol, and deteriorate mental wellbeing among refugee communities ([here](https://doi.org/10.1093/esr/jcaa007) and [here](https://doi.org/10.1093/sf/soab135)).
                        You can find more information on his past and upcoming projects on his [website](https://arunfrey.github.io).


                        ### Source Code

                        You can find the source code of this app on [this Github repository](https://github.com/ArunFrey/refugee-attacks).

                    """
                            )
                        ),
                    ),
                ],
            )
        ),
    )


# load data
try:
    APP_PATH = str(pathlib.Path(__file__).parent.parent.resolve())
except:
    APP_PATH = ""

df = pd.read_csv(os.path.join(APP_PATH, os.path.join("data", "arvig.csv")), encoding="utf-8")
ger = gpd.read_file(os.path.join(APP_PATH, os.path.join(
    "data/raw/shp/simplified", "KRS_2014_ew.shp")))


# clean geo data
ger = ger[["AGS", "geometry"]].rename(columns={"AGS": "key"})
ger['key'] = ger['key'].astype(int)
ger_state = ger.assign(key=ger["key"] // 1000).dissolve(by="key")
ger = ger.set_index("key")
ger = pd.concat([ger, ger_state])

# subset data
df = df[(df["year"] < 2020) & (df["category_en"] != "Suspected/unconfirmed")]

# gen timeseries data
df_year = to_timeseries(df, time="year")
df_month = to_timeseries(df, time="month", category="All", states_only=True)
df_week = to_timeseries(df, time="week", category="All", states_only=True)

# gen unique key-name data
df_key = df_year.groupby("key").agg({"name": "first", "state": "first"})

# gen var
df_year["attack_pop"] = (df_year["attacks"] / (df_year["pop"] / 100000)).round(2)
df_month["attack_pop"] = df_month["attacks"] / (df_month["pop"] / 100000).round(2)
df_week["attack_pop"] = df_week["attacks"] / (df_week["pop"] / 100000).round(2)

df_year["attack_pop_c"] = pd.cut(
    df_year['attack_pop'], BINS, include_lowest=True, labels=LABELS)

app.layout = html.Div([

    build_banner(),

    generate_modal(),

    build_top_panel(),

    html.Div(children=[
             dcc.Graph(id='fig-map'),
             ], style={'width': '60%', 'display': 'inline-block'}),

    html.Div(children=[
             dcc.Graph(id='fig-bar'),
             ], style={'width': '40%', 'float': 'right'}),

    html.Br(),

    build_bottom_panel(),

    dcc.Graph(id='fig-timeseries')

])


# learn-more button
@ app.callback(
    Output("markdown", "style"),
    [Input("learn-more-button", "n_clicks"), Input("markdown_close", "n_clicks")],
)
def update_click_output(button_click, close_click):
    ctx = callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "learn-more-button":
            return {"display": "block"}

    return {"display": "none"}


# map plot
@ app.callback(
    Output('fig-map', 'figure'),
    Input('unit-id', 'value'),
    Input('year-id', 'value'),
    Input('category-id', 'value'),
)
def update_map(region, year, category):

    # select region
    if region == "State":
        df_cat = df_year[(df_year["key"] > 0) & (df_year["key"] <= 16)]
        ger_cat = ger[(ger.index != 0) & (ger.index <= 16)]

    if region == "District":
        df_cat = df_year[df_year["key"] > 16]
        ger_cat = ger[(ger.index > 16)]

    # subset category
    df_cat = df_cat[df_cat["category_en"] == category]
    # colrange = (0, max(df_cat["attack_pop"]))

    # subset year
    df_cat = df_cat[df_cat["time"] == year]

    # set annotations
    annotations = [
        dict(
            showarrow=False,
            align="right",
            text="<b>Anti-refugee attacks<br>per 100,000 residents</b>",
            font=dict(color=font_color),
            bgcolor="#1f2630",
            x=0.95,
            y=0.95,
        )
    ]

    for i, bin in enumerate(reversed(LABELS)):
        color = COLOR_MAP[bin]
        annotations.append(
            dict(
                arrowcolor=color,
                text=bin,
                x=0.95,
                y=0.85 - (i / 20),
                ax=-100,
                ay=0,
                arrowwidth=10,
                arrowhead=0,
                bgcolor="#1f2630",
                font=dict(color=font_color),
            )
        )

    # figure
    fig = px.choropleth_mapbox(df_cat, geojson=ger_cat, locations="key",
                               # color_continuous_scale="Pinkyl",
                               # colrange = colrange,
                               color_discrete_map=COLOR_MAP,
                               color=df_cat["attack_pop_c"],
                               opacity=0.8,
                               labels={'attacks': "Attacks",
                                       'attack_pop': "Attacks/100,000",
                                       'attack_pop_c': "Attacks/100,000"},
                               hover_name="name",
                               hover_data=["attack_pop", "attacks"]
                               )

    fig.update_traces(marker_line_width=0)

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            accesstoken="pk.eyJ1IjoiYXJ1bmYiLCJhIjoiY2wyNmFva3h4MHE4bDNmcWkzbTcwazNvcCJ9.kKtt_EUOJa9uP8sraSkfyA",
            style='mapbox://styles/arunf/cl2rqw7yw001214pd60i50fbk',  # works
            center={"lat": 51.2, "lon": 10.4515},
            zoom=4.66,
        ),
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        font_color=font_color,
        transition_duration=200,
        annotations=annotations,
        showlegend=False,
    )

    fig.update_geos(visible=False, fitbounds="locations")

    return fig


# bar plot
@ app.callback(
    Output("fig-bar", "figure"),
    Input("fig-map", "hoverData"),
    Input('unit-id', 'value'),
    Input('year-id', 'value'),
    Input('category-id', 'value'),
)
def update_bar_plot(hoverData, unit, year, category):

    # select region in map
    try:
        region = hoverData['points'][0]['hovertext']
    except:
        region = "Berlin"

    # subset at state or district level
    if unit == "District":
        df_bar = df_year[(df_year['name'] == region) & (df_year["key"] > 16)]
    elif unit == "State":
        df_bar = df_year[(df_year['name'] == region) & (df_year["key"] <= 16)]

    # set max range of plot at highest value across all years
    max_yrange = max(df_bar["attacks"])

    # subset at year level
    df_bar = df_bar[(df_bar['time'] == year)]

    # figure
    fig = px.bar(df_bar, x="category_en", y="attacks", color="category_en",
                 title=f"{region} ({year})",
                 labels={"attacks": "Attacks (#)", "category_en": "Categories"},
                 range_y=(0, max_yrange if max_yrange > 10 else 10),
                 color_discrete_map=COLOR_BAR,
                 )

    fig.update_traces(marker=dict(line=dict(width=0)))

    fig.update_layout(
        title=dict(
            y=0.9,
            x=0.5,
            font=dict(size=15)
        ),
        xaxis_title="",
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        font_color=font_color,
        yaxis_gridcolor=grid_color,
        showlegend=False,
    )

    return(fig)


# timeseries plot
@ app.callback(
    Output("fig-timeseries", "figure"),
    Input("fig-map", "hoverData"),
    Input("var-id", "value"),
    Input("yearrange-id", "value"),
    Input("timeunit-id", "value"),
)
def update_time_plot(hoverData, var, yearrange, timeunit):

    # select region in map and select underlying state
    try:
        region = hoverData['points'][0]['hovertext']
    except:
        region = "Berlin"

    state = df_key[df_key["name"] == region]["state"].values[0]

    COLOR_TIME[state] = COLOR_STATE

    # select time unit
    if timeunit == "Monthly":
        df = df_month
    elif timeunit == "Weekly":
        df = df_week
    elif timeunit == "Yearly":
        df = df_year

    # subset data to current state and Germany (total, east, west)
    df = df[(df["name"].isin(["Germany", state, "West Germany", "East Germany"]))
            & (df["key"] <= 16) & (df["category_en"] == "All")]

    # set max y range across all timeperiods
    max_y = max(df[var]) + 0.1

    # subset by time
    if timeunit != "Yearly":
        df = df[pd.DatetimeIndex(df["time"]).year.isin(range(yearrange[0], yearrange[1] + 1))]
    elif timeunit == "Yearly":
        df = df[df["time"].isin(range(yearrange[0], yearrange[1] + 1))]

    df = df.sort_values(["key", "time"], ascending=False)

    if timeunit == "Yearly":
        fig = px.bar(df, x="time", y=var,
                     color="name",
                     barmode="group",
                     labels={"attack_pop": "Attacks per 100,000 residents",
                             "attacks": "Attacks (#)",
                             "category_en": "Categories", "name": ""},
                     range_y=(0, max_y),
                     color_discrete_map=COLOR_TIME,
                     )
        fig.update_traces(marker=dict(line=dict(width=0)))

    elif timeunit != "Yearly":
        fig = px.line(df, x="time", y=var,
                      color="name",
                      line_dash="name",
                      line_dash_sequence=["solid", "solid", "dot", "dash"],
                      line_shape="spline",
                      render_mode="svg",
                      labels={"attack_pop": "Attacks per 100,000 residents",
                              "attacks": "Attacks (#)",
                              "category_en": "Categories", "name": ""},
                      range_y=(0, max_y),
                      color_discrete_map=COLOR_TIME,
                      )

        fig.update_traces(line=dict(width=3))

    fig.for_each_trace(lambda trace: trace.update(visible="legendonly")
                       if trace.name in ["East Germany", "West Germany"] else ())

    fig.update_xaxes(showgrid=False)

    fig.update_layout(
        xaxis_title="",
        legend=dict(
            yanchor="top", y=1,
            xanchor="left", x=0
        ),
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        font_color=font_color,
        yaxis_gridcolor=grid_color,
        transition_duration=200
    )

    return(fig)


if __name__ == '__main__':
    app.run_server(debug=True, host="127.0.0.1")


df_year["attack_pop_c"]
