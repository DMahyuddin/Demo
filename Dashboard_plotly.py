import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

df_energy = pd.read_csv('global-data.csv')

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Global Data on Sustainable Energy (2000-2020)'

color_map = {
    "Fossil Fuels": "#FFB6B3",  
    "Nuclear": "#87CEFA",       
    "Renewables": "#98FB98"    
}

df_energy["Total electricity"] = df_energy["Electricity from Fossil Fuels (TWh)"] + \
                                  df_energy["Electricity from Nuclear (TWh)"] + \
                                  df_energy["Electricity from Renewables (TWh)"]

df_histo = pd.melt(df_energy, id_vars=["Country", "Continent", "Year"],
                   value_vars=["Electricity from Fossil Fuels (TWh)",
                               "Electricity from Nuclear (TWh)",
                               "Electricity from Renewables (TWh)"],
                   var_name="Electricity mode", value_name="Electricity (TWh)")

df_histo["Electricity mode"] = df_histo["Electricity mode"].str.replace("Electricity from ", "").str.slice(stop=-6)

app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand=app.title,
        brand_href="#",
        color="dark",
        dark=True,
        className="mb-4"
    ),
    dbc.Row([
        dbc.Col([
            
            html.Div([
                html.H5("Select range of years:"),
                dcc.RangeSlider(
                    min=df_histo['Year'].min(),
                    max=df_histo['Year'].max(),
                    step=1,
                    id="range-slider",
                    value=[df_histo['Year'].min(), df_histo['Year'].max()],
                    marks={str(year): str(year) for year in df_histo['Year'].unique()},
                ),
                html.Div(id="pourcentage")
            ], className="p-3 bg-light rounded shadow-sm container")
        ], width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([dcc.Graph(id='map')], width=7, className="p-2"),
        dbc.Col([dcc.Graph(id='bar')], width=5, className="p-2"),
    ], className="mb-4"),
], fluid=True)

@app.callback(
    Output("pourcentage", "children"),
    [Input("range-slider", "value"),
     Input("map", "clickData")]
)
def pourcentage(year_range, clickData):
    if clickData is None:
        return dbc.Alert("Select a country on the map to see details.", color="primary")

    country = clickData['points'][0]["location"]
    df_filtered = df_histo[(df_histo["Year"] >= year_range[0]) & (df_histo["Year"] <= year_range[1])]
    pays_elec = df_filtered.query("Country=='" + country + "'")["Electricity (TWh)"].sum()
    tot_elec = df_filtered["Electricity (TWh)"].sum()

    if tot_elec == 0:
        return dbc.Alert("No data available for the selected period.", color="warning")
    
    percentage = (pays_elec / tot_elec) * 100
    formatted_percentage = round(percentage, 2)

    return dbc.Card(
        dbc.CardBody([
            html.H5(f"{country}", className="card-title"),
            html.P(f"Produced {int(pays_elec)} TWh of electricity", className="card-text"),
            html.P(f"In the range of years {year_range[0]}-{year_range[1]}.", className="card-text"),
            html.P(f"This represents {formatted_percentage}% of world production.", className="card-text"),
        ]),
        className="mb-3 shadow-sm"
    )

@app.callback(
    Output("map", "figure"),
    [Input("range-slider", "value")]
)
def make_map(year_range):
    df_filtered = df_energy[(df_energy["Year"] >= year_range[0]) & (df_energy["Year"] <= year_range[1])]
    color = "Total electricity"
    fig = px.choropleth(
        df_filtered,
        locations="Country",
        color=color,
        hover_name="Country",
        hover_data={"Country": False, "Total electricity": True}, 
        locationmode="country names",
        range_color=[df_filtered[color].min(), df_filtered[color].max()],
        scope="world",
        color_continuous_scale=px.colors.sequential.Greens,
    )
    fig.update_geos(
        visible=False,
        showcoastlines=True,
        center={"lat": 30, "lon": 0},
        projection_scale=1.3
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode='closest',
        autosize=True,
        margin=dict(l=20, r=20, t=20, b=20),
        coloraxis_colorbar=dict(title="Total Electricity (TWh)", len=0.75, orientation="v"),
        geo=dict(bgcolor="rgba(255,255,255,1)")
    )
    return fig

@app.callback(
    Output("bar", "figure"),
    [Input("map", "clickData"),
     Input("range-slider", "value")]
)
def bar_chart(clickData, year_range):
    if clickData is None:
        return {}
    
    country = clickData['points'][0]["location"]
    df_bar = df_histo[(df_histo["Country"] == country) & (df_histo["Year"] >= year_range[0]) & (df_histo["Year"] <= year_range[1])]
    
    if df_bar.empty:
        return {}
    
    fig = px.bar(
        df_bar,
        x="Year",
        y="Electricity (TWh)",
        color="Electricity mode",
        color_discrete_map=color_map,
        opacity=0.9,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,1)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
