###Load packages 
import pandas as pd
import numpy as np
import itertools
import warnings 
import json
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False
import plotly.express as px
import plotly.graph_objects as go 
from shapely.geometry import Point

warnings.filterwarnings("ignore")

### Dispatch packages
from module.disabled_passenger_api import dispatch_data_loader
from module.add_location import add_ps_location
from module.fake_passenger import generate_fake_passenger
from module.my_azure_storage import * 
from module.generate_random_location import Generate_taxi_random_location
from module.dispatch_data_prepare import dispatch_data_preprocessing
from module.dispatch_taxi_passenger import *



def generate_ps_and_taxi(date, model, fake_ratio=None):
    #passenger api 데이터 받기
    passenger = dispatch_data_loader(date)
    #승객 자세한 위치 정보 부여
    passenger = add_ps_location(passenger)
    #택시 생성
    taxi = Generate_taxi_random_location("서울 대한민국", len(set(passenger["no"])))
    #dispatch를 하기위해 데이터 전처리
    passenger, taxi = dispatch_data_preprocessing(passenger, taxi, date, model)
    #fake data 생성
    if fake_ratio == None:
        pass
    else:
        passenger = generate_fake_passenger(passenger, fake_ratio)
    return passenger, taxi

### Layer information save
def layer_information_save(trips, empty_inf, ps_loc_inf):
    data_ct = connect_container("data")
    block_list = [i.name for i in data_ct.list_blobs()]
    
    for i in ["trips.json", "empty_taxi.json", "waiting_passenger.json"]:  
        if i in block_list:
            delete_blob("data",i)
    
    blob_uploader(json.dumps(trips), "data", "trips")
    blob_uploader(json.dumps(empty_inf), "data", "empty_taxi")
    blob_uploader(json.dumps(ps_loc_inf), "data", "waiting_passenger")
    
### Text information save
def text_information_save(ps_loc_inf, empty_tx, drive_tx, fail_ps, success_ps_num):
    waiting_ps = []
    for i in range(6*60, 30*60+1):
        waiting_ps.extend([sum([i in range(j["timestamp"][0], round(j["timestamp"][1])) for j in ps_loc_inf])])

    dispatch_inf = dict()
    dispatch_inf["waiting_passenger_num"] = waiting_ps
    dispatch_inf['empty_taxi_num'] = empty_tx
    dispatch_inf['driving_taxi_num'] = drive_tx
    dispatch_inf['fail_passenger_cumsum'] = fail_ps
    dispatch_inf['success_passenger_cumsum'] = [int(i) for i in success_ps_num]

    data_ct = connect_container("data")
    block_list = [i.name for i in data_ct.list_blobs()]
    
    if "dispatch_inf.json" in block_list:
        delete_blob("data","dispatch_inf.json")
    
    blob_uploader(json.dumps(dispatch_inf), "data", "dispatch_inf")


def dispatch_module(passenger_locations, taxi_locations, fail_time, date, model):
    empty_taxi = pd.DataFrame()
    driving_data = pd.DataFrame()
    taxi_statistics_information = pd.DataFrame()
    all_fail_data = pd.DataFrame()
    trips = []
    empty_inf = []
    passenger_loc_information = []

    ###
    waiting_ps = [] #대기 고객
    fail_ps = [] #실패 고객
    empty_tx = [] #배차 가능 차량 
    drive_tx = [] #운행 중인 차량
    success_ps_num = [] #누적 콜 성공 고객
    t = [] #시간

    ###
    ps_remain = []
    for i in range(360, 1801):
        ### Passenger, Taxi 추가 및 제거
        # - 운행 종료 택시 제거 및 360(운행시작시간)에서는 미실행
        if (i % 60 == 0) and (i != 360):
            empty_taxi = empty_taxi.loc[empty_taxi.work_end >= i]
        # - 60분(1시간) 마다 출근 택시 추가
        if i % 60 == 0:
            #운행 시작 택시
            start_taxi = taxi_locations.loc[taxi_locations.work_start == i]
            #배차 안된 택시
            empty_taxi = pd.concat([start_taxi, empty_taxi])
        # - 매 분 콜호출 고객 데이터 업데이트
        call_ps = passenger_locations.loc[passenger_locations.call_time == i]
        # - 빈 차량 정보 누적 업데이트(시각화를 위한 데이터) 
        empty_inf.append([i,empty_taxi])
        # - 콜 대기시간 60분 이상이면 콜실패로 콜 고객 데이터에서 제거
        # - 실패 데이터 시각화를 위한 누적 업데이트
        if len(ps_remain) > 0:
            fail_data = ps_remain.loc[ps_remain["dispatch_time"] >= fail_time]
            fail_data = fail_data[["call_time", "ps_loc_0"]]
            all_fail_data = pd.concat([all_fail_data, fail_data])
            
            ps_remain = ps_remain.loc[ps_remain["dispatch_time"] < fail_time]

        ### 기본 information
        waiting_ps.extend([len(call_ps) + len(ps_remain)])
        empty_tx.extend([len(empty_taxi)])
        drive_tx.extend([len(driving_data)])
        fail_ps.extend([len(all_fail_data)])
        success_ps_num.extend([len(trips)/2])
        t.extend([i])
        
        ### Dispatch
        # - call_ps : 현시 콜 고객, ps_remain : 콜 대기 고객
        # 고객이 있을 때 또는 빈 차량이 있을때 -> 알고리즘 실행
        if (len(call_ps) + len(ps_remain) > 0) & (len(empty_taxi) > 0):
            # - ps_remain(콜 대기 고객)이 있을 때 실행
            if len(ps_remain) > 0:            
                trip, driving, ps_remain, tx_remain, taxi_statistics_inf, ps_locations_inf = match_taxi_ps(ps_remain, empty_taxi, date, model)
                taxi_statistics_inf["time"] = i
                taxi_statistics_information = pd.concat([taxi_statistics_information,taxi_statistics_inf])
                empty_taxi = tx_remain
                driving_data = pd.concat([driving_data, driving])
                passenger_loc_information.append(ps_locations_inf)
                trips.extend(trip)
                
                if len(ps_remain) > 0:
                    ps_remain = pd.concat([ps_remain, call_ps])
            # - ps_remain(콜 대기 고객)이 없고, call_ps(콜 대기 고객)이 있을때 실행
            if (len(ps_remain) == 0) & (len(call_ps) > 0) & (len(empty_taxi) > 0):
                trip, driving, ps_remain, tx_remain, taxi_statistics_inf, ps_locations_inf = match_taxi_ps(call_ps, empty_taxi, date, model)
                empty_taxi = tx_remain
                driving_data = pd.concat([driving_data, driving])
                taxi_statistics_inf["time"] = i
                taxi_statistics_information = pd.concat([taxi_statistics_information,taxi_statistics_inf])
                passenger_loc_information.append(ps_locations_inf)
                trips.extend(trip)
        
        ### Driving taxi, Empty taxi 전환 
        # - driving_data(운행 중인 차량)에서 고객이 내린 차량은 빈 택시로 전환
        if len(driving_data) > 0:
            #목적지까지 운행완료한 택시
            drive_end = driving_data.loc[driving_data["end_time"] <= i]
            drive_end = drive_end[["no","cartype","work_start","work_end","board_status","tx_loc"]]
            #운행 중인 택시
            driving_data = driving_data.loc[driving_data["end_time"] > i]
            #목적지까지 운행완료한 택시 빈 택시에 추가
            empty_taxi = pd.concat([empty_taxi ,drive_end])
            
    ### Passenger_information, Taxi_information
    # - passenger_information
    ps_loc_inf = pd.concat(passenger_loc_information)
    ps_loc_inf = [{"path":[i[1]["loc"].x, i[1]["loc"].y], "timestamp":i[1]["time"]} for i in ps_loc_inf.iterrows()]  
    # - empty_information
    stop_taxi = pd.concat(list(map(lambda data: stop_taxi_inf(data), empty_inf)))
    empty_inf = list(map(lambda data : generate_taxi_pull_over_inf(data[1]) ,stop_taxi.groupby("no")))
    empty_inf = list(itertools.chain(*empty_inf))
    # - Generate Passenger_information, Taxi_information 
    ps_final_inf, taxi_final_inf = generate_drive_inf(taxi_locations, taxi_statistics_information)
    # - fail passenger inf을 기존 승객 데이터에 추가
    for i in ps_loc_inf:
        i.update({"fail":0})

    ps_loc_inf.extend(list(map(lambda data: {"path": [data[1]["ps_loc_0"].x, data[1]["ps_loc_0"].y], "timestamp": [data[1]["call_time"], data[1]["call_time"] + fail_time], "fail":1} ,all_fail_data.iterrows())))
    
    ### Layer information save
    layer_information_save(trips, empty_inf, ps_loc_inf)
    ### Text information save
    text_information_save(ps_loc_inf, empty_tx, drive_tx, fail_ps, success_ps_num)
    return all_fail_data, ps_final_inf, taxi_final_inf


def dispatch_module_main(date, fake_ratio, fail_time):
    ETA_model = get_weights_blob(blob_name = 'ETA_model.pkl')
    
    passenger_locations, taxi_locations = generate_ps_and_taxi(date, ETA_model)
    all_fail_data, ps_final_inf, taxi_final_inf = dispatch_module(passenger_locations, taxi_locations, fail_time , date, ETA_model)
    graph_blob_list = blob_list("graph-data")
    if len(graph_blob_list) != 0:
        for i in graph_blob_list:
            delete_blob("graph-data",i)
            
    all_fail_data = gpd.GeoDataFrame(all_fail_data)
    all_fail_data.columns = ["call_time", "geometry"]
    all_fail_data.to_json()

    blob_uploader(all_fail_data.to_json(), "graph-data", 'all_fail_data')
    blob_uploader(passenger_locations[["call_time"]].to_json(), "graph-data", 'passenger_locations')
    blob_uploader(ps_final_inf.reset_index(drop=True).to_json(), "graph-data", 'ps_final_inf')
    blob_uploader(taxi_final_inf.reset_index(drop=True).to_json(), "graph-data", 'taxi_final_inf')
