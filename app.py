###Load packages 
import pandas as pd
from sympy import false
import geopandas as gpd
import numpy as np
import warnings 
import plotly.express as px
import plotly.graph_objects as go 
from shapely.geometry import Point
from my_azure_storage import *
from flask import Flask
from flask_cors import CORS
from flask import send_from_directory
import os

warnings.filterwarnings("ignore")

# Data Load
graph_ct = connect_container("graph-data")

all_fail_data = load_json_trans_data('all_fail_data', graph_ct, type="gpd")

passenger_locations = load_json_trans_data('passenger_locations', graph_ct, type="pd")
ps_final_inf = load_json_trans_data('ps_final_inf', graph_ct, type="pd")
taxi_final_inf = load_json_trans_data('taxi_final_inf', graph_ct, type="pd")

data_ct = connect_container("data")
dispatch_inf = load_json_trans_data('dispatch_inf', data_ct, type="pd")
empty_tx = dispatch_inf["empty_taxi_num"].tolist()
drive_tx = dispatch_inf["driving_taxi_num"].tolist()

trips = load_json_trans_data('trips', data_ct, type="pd")
trips = [{"vendor":i[1]["vendor"], "type":i[1]["type"], "path":i[1]["path"], "timestamps":i[1]["timestamps"]} for i in trips.iterrows()]


######### Visualization
import plotly.io as pio

pio.templates["custom_dark"] = pio.templates["plotly_dark"]
pio.templates["custom_dark"]['layout']['font']['color'] = '#c3c4c7'

###### Page1
# 1-a
page1_1a = f"전체 호출 수 - 총 {len(passenger_locations)}건, 실패 호출 수 - 총 {len(all_fail_data)}건"

# 1-b1
bins = [i*60 for i in range(6,31)]
labels = [i for i in range(6,30)]

fail_passenger_distribution = pd.DataFrame(pd.cut(all_fail_data["call_time"] + 30, bins = bins, labels = labels).value_counts(sort=False)).reset_index()
call_passenger_distribution = pd.DataFrame(pd.cut(passenger_locations["call_time"], bins = bins, labels = labels).value_counts(sort=False)).reset_index()

page1_1b = go.Figure()
page1_1b.add_trace(go.Scatter(x=call_passenger_distribution["index"], y=call_passenger_distribution["call_time"],
                         mode="lines+markers", 
                         name="콜 승객"))
page1_1b.add_trace(go.Scatter(x=fail_passenger_distribution["index"], y=fail_passenger_distribution["call_time"],
                         mode="lines+markers",
                         name="콜 실패 승객"))
page1_1b.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = [i for i in range(6,30)],
        ticktext = [f"{i}시" for i in range(6,30)]
    )
)
page1_1b.update_xaxes(range=[5.5, 29.5])
page1_1b.update_yaxes(
        title_text = "승객수")

page1_1b.update_layout(
    legend={"x": 0.9, "y":1},
    margin={"l":0,"r":0,"b":0,"t":0,"pad":0},
    template="plotly_dark")

# 1-b2
fail_distribution = pd.DataFrame(pd.cut(all_fail_data["call_time"], bins = bins, labels = labels).value_counts(sort=False)).T
call_distribution = pd.DataFrame(pd.cut(passenger_locations["call_time"], bins = bins, labels = labels).value_counts(sort=False)).T

fail_distribution_summary = pd.concat([fail_distribution, call_distribution])
fail_distribution_summary.index = ["실패 승객", "총 승객"]
fail_distribution_summary.columns = [f"{i}시" for i in fail_distribution_summary.columns]
page1_1b_summary = fail_distribution_summary

# 2-a
fail_distribution = pd.DataFrame(pd.cut(all_fail_data["call_time"], bins = bins, labels = labels).value_counts(sort=False)).T
call_distribution = pd.DataFrame(pd.cut(passenger_locations["call_time"], bins = bins, labels = labels).value_counts(sort=False)).T

fail_distribution_summary = pd.concat([fail_distribution, call_distribution])
fail_distribution_summary.index = ["실패 승객", "총 승객"]
fail_distribution_summary.columns = [f"{i}시" for i in fail_distribution_summary.columns]
page1_1b_summary = fail_distribution_summary

# 2-a
waiting_time = pd.DataFrame([(ps_final_inf["dispatch_time"] + ps_final_inf["wait_time"]).tolist(), ps_final_inf["time"].tolist()]).T
waiting_time.columns = ["total_waiting_time", "time"]

fail_waiting = all_fail_data[["call_time"]]
fail_waiting["total_waiting_time"] = 30
fail_waiting.columns = ["time", "total_waiting_time"]

waiting_time = pd.concat([waiting_time, fail_waiting])
waiting_time["total_waiting_time"] = np.round(waiting_time["total_waiting_time"].values,2)

page1_2a = go.Figure()
page1_2a.add_trace(go.Box(y=waiting_time["total_waiting_time"],hoverinfo='x+y'))
page1_2a.update_layout(
    title={'text': f"전체 기간동안의 평균 승객 대기시간 - {round(np.mean(waiting_time['total_waiting_time']))}분",
           'x':0.5,
           'y':0.9},
    margin={"l":0,"r":0,"b":0,"t":50,"pad":0},
    template="plotly_dark")
page1_2a.update_xaxes(
        visible = False)
page1_2a.update_yaxes(
        title_text = "대기시간",
        visible=True)

# 2-b
waiting_time["time_cut"] = pd.cut(waiting_time["time"], bins = bins, labels = labels).tolist()

top_5per_waiting_time = []
time = []
for i in waiting_time.groupby(["time_cut"]):
    sample = round(len(waiting_time.loc[waiting_time["time_cut"] == i[0]]) * 0.05)
    sample = 1 if sample < 1 else sample
    subset = i[1].sort_values("total_waiting_time", ascending=False).head(sample)
    top_5per_waiting_time.extend([np.mean(subset["total_waiting_time"])])
    time.extend([i[0]])
    
page1_2b = go.Figure()
page1_2b.add_trace(go.Box(x=waiting_time["time_cut"], y=waiting_time["total_waiting_time"]))
page1_2b.add_trace(go.Scatter(x=time, y=top_5per_waiting_time))
page1_2b.update_yaxes(
        title_text = "분")
page1_2b.update_layout(showlegend=False)
page1_2b.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = [i for i in range(6,30)],
        ticktext = [f"{i}시" for i in range(6,30)]),
    title={'text': '시간대별 승객 대기시간',
           'x':0.5,
           'y':0.9},
    margin={"l":0,"r":0,"b":0,"t":50,"pad":0},
    template="plotly_dark"
)

###### Page2
# 1
empty_tx_per = [round(i/(i+j), 2) for i,j in zip(empty_tx, drive_tx)]
drive_tx_per = [1-i for i in empty_tx_per]
t = [i for i in range(360, 1801)]

page2_1 = go.Figure()
page2_1.add_trace(go.Bar(
    x=t,
    y=empty_tx_per,
    name='빈 차량',
    marker_color='indianred'
))
page2_1.add_trace(go.Bar(
    x=t,
    y=drive_tx_per,
    name='운행중인 차량',
    marker_color='blue'
))
page2_1.update_layout(bargap=0)
page2_1.update_layout(
    barmode="stack")
page2_1.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = [i*60 for i in range(6,31)],
        ticktext = [f"{i}시" for i in range(6,31)]),
    yaxis = dict(
        tickmode = 'array',
        tickvals = [0.2, 0.4, 0.6, 0.8, 1.0],
        ticktext = ["20%", "40%", "60%", "80%", "100%"]),
    margin={"l":0,"r":0,"b":0,"t":0,"pad":0},
    template="plotly_dark"
)



# 2 
taxi_final_inf = taxi_final_inf.fillna(0)
taxi_final_inf["total_drive_time"] = taxi_final_inf["total_to_ps_drive_time"] + taxi_final_inf["total_ps_drive_time"]

page2_2 = f"총 운행 차량 대수 : {len(taxi_final_inf)}대/일\n총 운행 거리 : {round(taxi_final_inf[['total_ps_distance', 'total_ps_distance']].values.sum() / 1000)}km/일"

### Page 3
#start, end information
ps_start_inf, ps_end_inf  = [],[]
for i in trips:
    if i["vendor"] == 1:
        ps_start_inf.append([i["timestamps"][0] , i["path"][-1][0], i["path"][-1][1]])
    elif i["vendor"] == 0:
        ps_end_inf.append([i["timestamps"][-1], i["path"][-1][0], i["path"][-1][1]])
        
ps_start_inf = pd.DataFrame(ps_start_inf, columns = ["start_time","long","lat"])
ps_end_inf = pd.DataFrame(ps_end_inf, columns = ["end_time","long","lat"])

bins = [i*60 for i in range(6,31)]
labels = [i*60 for i in range(6,30)]

time_list = [i for i in range(420,1441,60)]

# 1_1
ps_start_inf["time"] = pd.cut(ps_start_inf["start_time"], bins = bins, labels = labels).tolist()

start_inf = []
for i in time_list:
    subset_start_inf = ps_start_inf.loc[ps_start_inf["time"] == i]
    start_inf.append(subset_start_inf)

frames = [{   
    'name':f'frame_{idx+7}',
    'data':[{
        'type':'densitymapbox',
        'lat':i["lat"].tolist(),
        'lon':i["long"].tolist(),
        'showscale': False,
        'radius':10}],           
} for idx,i in enumerate(start_inf)]  

sliders = [{
    'transition':{'duration': 0},
    'x':0.11, 
    'y':0.04,
    'len':0.80,
    'steps':[
        {
            'label':f"{idx+7}시",
            'method':'animate',
            'args':[
                ['frame_{}'.format(idx+7)],
                {'mode':'immediate', 'frame':{'duration':100, 'redraw': True}, 'transition':{'duration':50}}
              ],
        } for idx,i in enumerate(start_inf)]
}]

play_button = [{
    'type':'buttons',
    'showactive':True,
    'x':0.1, 'y':-0.05,
    'buttons':[{ 
        'label': 'Play',
        'method':'animate',
        'args':[
            None,
            {
                'frame':{'duration':200, 'redraw':True},
                'transition':{'duration':100},
                'fromcurrent':True,
                'mode':'immediate',
            }
        ]
    }]
}]

# Defining the initial state
data = frames[0]['data']

# Adding all sliders and play button to the layout
layout = go.Layout(
    sliders=sliders,
    updatemenus=play_button,
    mapbox={
        'accesstoken':"pk.eyJ1IjoiZHVzZ3Vyd24iLCJhIjoiY2wzbW9yNjdsMDZ0djNpbW9vbnhsZXBobCJ9.KDVqndg88Clx3Bq3_GTF4Q",
        'center':{"lat": 37.557, "lon":126.99},
        'zoom':10,
        'style':'dark'},
    height = 600,
    margin = {'l':0, 'r':0, 'b':80, 't':0},
    template="custom_dark"
)

# Creating the figure
page3_1_1 = go.Figure(data=data, layout=layout, frames=frames)


# 3-1-1-a
data = go.Densitymapbox(lat=ps_start_inf.lat, lon=ps_start_inf.long,
                                 radius=7)

layout_basic = go.Layout(
    mapbox={
        'accesstoken':"pk.eyJ1IjoiZHVzZ3Vyd24iLCJhIjoiY2wzbW9yNjdsMDZ0djNpbW9vbnhsZXBobCJ9.KDVqndg88Clx3Bq3_GTF4Q",
        'center':{"lat": 37.557, "lon":126.99},
        'zoom':10,
        'style':'dark'},
    height = 600,
    margin = {'l':0, 'r':0, 'b':0, 't':0},
    template="plotly_dark"
)

page3_1_1_a = go.Figure(data=data, layout=layout_basic)



# 1-2
ps_end_inf["time"] = pd.cut(ps_end_inf["end_time"], bins = bins, labels = labels).tolist()

end_inf = []
for i in time_list:
    subset_end_inf = ps_end_inf.loc[ps_end_inf["time"] == i]
    end_inf.append(subset_end_inf)

frames = [{   
    'name':f'frame_{idx+7}',
    'data':[{
        'type':'densitymapbox',
        'lat':i["lat"].tolist(),
        'lon':i["long"].tolist(),
        'showscale': False,
        'radius':10}],           
} for idx,i in enumerate(end_inf)]  

# Defining the initial state
data = frames[0]['data']

# Creating the figure
page3_1_2 = go.Figure(data=data, layout=layout, frames=frames)


data = go.Densitymapbox(lat=ps_end_inf.lat, lon=ps_end_inf.long,
                                 radius=7)

layout_basic = go.Layout(
    mapbox={
        'accesstoken':"pk.eyJ1IjoiZHVzZ3Vyd24iLCJhIjoiY2wzbW9yNjdsMDZ0djNpbW9vbnhsZXBobCJ9.KDVqndg88Clx3Bq3_GTF4Q",
        'center':{"lat": 37.557, "lon":126.99},
        'zoom':10,
        'style':'dark'},
    height = 600,
    margin = {'l':0, 'r':0, 'b':0, 't':0},
    template="plotly_dark"
)

page3_1_2_a = go.Figure(data=data, layout=layout_basic)
page3_1_2_a


# 2
all_fail_data["call_time"] = all_fail_data["call_time"] + 30
all_fail_data["time"] = pd.cut(all_fail_data["call_time"], bins = bins, labels = labels).tolist()

all_fail_data["lat"] = [i.y for i in all_fail_data["geometry"]]
all_fail_data["long"] = [i.x for i in all_fail_data["geometry"]]

fail_inf = []
for i in time_list:
    subset_fail_inf = all_fail_data.loc[all_fail_data["time"] == i]
    fail_inf.append(subset_fail_inf)

frames = [{   
    'name':f'frame_{idx+7}',
    'data':[{
        'type':'scattermapbox',
        'lat':i["lat"].tolist(),
        'lon':i["long"].tolist()}],           
} for idx,i in enumerate(fail_inf)]  

# Defining the initial state
data = frames[0]['data']

# Creating the figure
page3_2 = go.Figure(data=data, layout=layout, frames=frames)

# 3
extradata_ct = connect_container("extradata")
hjd_20180401 = load_json_trans_data("hjd_20180401", extradata_ct, type = "gpd")

ps_wait_inf = []
for i in trips:
    if i["vendor"] == 1:
        ps_wait_inf.append([i["timestamps"][-1] - i["timestamps"][0] , Point([i["path"][-1][0], i["path"][-1][1]])])

ps_wait_inf = gpd.GeoDataFrame(ps_wait_inf, columns = ["wait_time", "geometry"])


ps_wait_inf = gpd.sjoin(ps_wait_inf, hjd_20180401)

ps_wait_inf = ps_wait_inf.groupby(["adm_nm"]).mean(["wait_time"]).reset_index().drop("index_right",axis=1)
ps_wait_inf = pd.merge(ps_wait_inf, hjd_20180401).set_index("adm_nm")
ps_wait_inf["wait_time"] = np.round(ps_wait_inf["wait_time"].values,2)

ps_wait_inf.columns = ['Wait Time (min)', 'geometry', 'adm_cd']

page3_3 = px.choropleth_mapbox(ps_wait_inf,
                           geojson=ps_wait_inf.geometry,
                           locations=ps_wait_inf.index,
                           color="Wait Time (min)",
                           center={"lat": 37.557, "lon": 126.99},
                           mapbox_style="carto-positron",
                           zoom=10)
page3_3.update_layout(
    mapbox={
        'accesstoken':"pk.eyJ1IjoiZHVzZ3Vyd24iLCJhIjoiY2wzbW9yNjdsMDZ0djNpbW9vbnhsZXBobCJ9.KDVqndg88Clx3Bq3_GTF4Q",
        'style':'dark'},
    margin={"r":0,"t":0,"l":0,"b":0},
    height = 600,
    template="plotly_dark")

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html
import plotly.graph_objects as go

server = Flask(__name__)
CORS(server)


app = dash.Dash(__name__, server=server,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[
                    html.H4("RESULT REPORT"),
                ],
            )
        ])


def build_tabs():
    return html.Div(
        id="tabs",
        className="tabs",
        children=[
            dcc.Tabs(
                id="app-tabs",
                value="tab1",
                className="custom-tabs",
                children=[
                    dcc.Tab(
                        id="Level-of-Service",#"Specs-tab",
                        label="Level of Service",
                        value="tab1",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="Vehicle-Operation-Status",#"Control-chart-tab",
                        label="Vehicle Operation Status",
                        value="tab2",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="Spatial-Distribution-of-Call-Requests",
                        label="Spatial Distribution of Call Requests",
                        value="tab3",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                ],
            )
        ],
    )

COLORS = {
    "text":"white"
}


build_tab_1 = [
        html.Div(
            children=[
                 #page1
                 html.Br(),
                 html.H2(html.B("1. 호출요청 및 호출실패"), style={"color": COLORS["text"]}),
                 #page1-a
                 dbc.Alert([html.Li(html.B(f"전체 호출 수:  총 {len(passenger_locations)}건 | 전체 실패 호출 수:  총 {len(all_fail_data)}건"),
                                    style={'font-size':'120%',"color": COLORS["text"]})], color="#3c434a"),
                 #page1-b
                 html.Li(html.B("시간대 별 효출요청 및 호출실패 건수"),style={"font-size": '120%', "color": COLORS["text"]}),
                 dcc.Graph(figure=page1_1b),
                 html.Hr(style={"color": COLORS["text"]}),
                 #page2
                 html.Br(),
                 html.H2(html.B("2. 승객 대기시간 분포"), style={"color": COLORS["text"]}),
                 dbc.Row([dcc.Graph(figure=page1_2b, style={'width': '70%', 'display': 'inline-block', 'padding': '10 0 0 0'}),
                          dcc.Graph(figure=page1_2a, style={'width': '30%', 'display': 'inline-block', 'padding': '0 0 0 10'})])]
            )
    ]
    

build_tab_2 = [
        html.Div(
            children=[
                 #page2
                 html.Br(),
                 html.H2(html.B("1. 차량 운행 정보"), style={"color": COLORS["text"]}),
                 html.Br(),
                 #page2-a
                 html.Li(html.B("차량 운행 기록 정보"), style={'font-size': '110%', "color": COLORS["text"]}),
                 dbc.Alert([html.B(f"총 운행 차량 대수: {len(taxi_final_inf)}대/일 | 총 운행 거리: {round(taxi_final_inf[['total_ps_distance', 'total_ps_distance']].values.sum() / 1000)}km/일, 총 운행 시간: {round(sum(taxi_final_inf['total_drive_time'])/60)}hour/일", 
                                           style={'font-size':'120%', "color": COLORS["text"]})], color="#3c434a"),
                 #page2-b
                 html.Br(),
                 html.Li(html.B("시간대 별 전체 차량 운행 현황"), style={'font-size': '110%', "color": COLORS["text"]}),
                 dcc.Graph(figure=page2_1)])
    ]


build_tab_3 = [
        html.Div(
            children=[
                 #page3
                 html.Br(),
                 html.H2(html.B("1. 시간대별 승/하차 위치"), style={'color': COLORS["text"]}),
                 html.Br(),
                 #page3-1
                 html.Li(html.B("승차"), style={'font-size': '110%', "color": COLORS["text"]}),
                 dbc.Row([dcc.Graph(figure=page3_1_1, style={'width': '50%', 'display': 'inline-block', 'padding': '10 0 0 0'}),
                          dcc.Graph(figure=page3_1_1_a, style={'width': '50%', 'display': 'inline-block', 'padding': '0 0 0 10'})]),
                 html.Br(),
                 html.Li(html.B("하차"), style={'font-size': '110%', "color": COLORS["text"]}),
                 dbc.Row([dcc.Graph(figure=page3_1_2, style={'width': '50%', 'display': 'inline-block', 'padding': '10 0 0 0'}),
                          dcc.Graph(figure=page3_1_2_a, style={'width': '50%', 'display': 'inline-block', 'padding': '0 0 0 10'})]),                 
                 html.Hr(style={'color': COLORS["text"]}),
                 #page3-2
                 html.Br(),
                 html.H2(html.B("2. 시간대별 배차 실패지점 위치"), style={'color': COLORS["text"]}),
                 html.Br(),
                 dcc.Graph(figure=page3_2),
                 html.Hr(style={'color': COLORS["text"]}),
                 #page3-3
                 html.Br(),
                 html.H2(html.B("3. 시간대별 읍면동별 승객 대기시간 분포"), style={'color': COLORS["text"]}),
                 html.Br(),
                 dcc.Graph(figure=page3_3)])
    ]


app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='/static/base-styles.css'
    ),
    html.Div(
    id="big-app-container",
    children=[
        build_banner(),
        html.Div(
            id="app-container",
            children=[
                build_tabs(),
                # Main app
                html.Div(id="app-content"),
            ],
        ),
    ],
)])


@app.server.route('/static/<path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)

@app.callback(
    [Output("app-content", "children")],
    [Input("app-tabs", "value")]
)
def render_tab_content(tab_switch):
    if tab_switch == "tab1":
        return build_tab_1
    elif tab_switch == "tab2":
        return build_tab_2
    return build_tab_3

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8000, debug=False)