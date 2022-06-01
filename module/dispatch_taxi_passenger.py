###import packages 
import pandas as pd
import numpy as np
import warnings 

from module.dispatch_ortools import main_dispatch
from module.osrm_api import * 

warnings.filterwarnings("ignore")


### dispatch 실행 - 성공, 실패 분리
def dispatch_success_and_fail(call_data, taxi_data):
    passenger_iloc ,taxi_iloc = main_dispatch(call_data, taxi_data)
    
    #남은 차량 또는 남은 승객
    remain_taxi_mask = list(set(range(len(taxi_data))) - set(taxi_iloc))
    remain_ps_mask = list(set(range(len(call_data))) - set(passenger_iloc))
    
    remain_taxi = taxi_data.iloc[remain_taxi_mask]
    remain_ps = call_data.iloc[remain_ps_mask]
    
    #배차 성공 차량 또는 승객
    success_taxi = taxi_data.iloc[taxi_iloc]
    success_ps = call_data.iloc[passenger_iloc]
    success_ps["no"] = success_taxi["no"].tolist()
    
    success = pd.merge(success_taxi, success_ps)
    return success, [remain_ps, remain_taxi]

### routes, timestamps, distance, wait_time, drive_time 재정의 및 추가 
def dispatch_data_col_update(call_data, taxi_data, date, model):
    success, remain = dispatch_success_and_fail(call_data, taxi_data)
    remain_ps, remain_taxi = remain[0], remain[1]

    #승객에게 가는 route, timestamp, distance 추가
    success = get_route_time_dispatch(success, date, model)
    
    #승객 wait_time, drive_time 추가 
    success["wait_time"] = list(map(lambda data: data[1]['to_ps_timestamp'][-1], success.iterrows()))
    success["drive_time"] = list(map(lambda data: data[1]['ps_timestamp'][-1], success.iterrows()))
    
    #승객 타입 별 탑승 시간 구분 
    ridetime_by_type =  lambda data: 5 if data["ps_type"] == 0 else 10
        
    #timestamps에 현시 더해주기 및 도착 시간 (하차시간 5분 추가)
    success["to_ps_timestamp"] =  list(map(lambda data: (np.array(data[1]["to_ps_timestamp"]) + np.array([data[1]["call_time"] + data[1]["dispatch_time"]])).tolist() , success.iterrows()))
    success["ps_timestamp"] =  list(map(lambda data: (np.array(data[1]["ps_timestamp"]) + np.array([data[1]["to_ps_timestamp"][-1] + ridetime_by_type(data[1])])).tolist(), success.iterrows()))
    success["end_time"] = list(map(lambda data: data[1]["ps_timestamp"][-1] + 5 , success.iterrows()))
    
    #고객 위치 정보 생성
    success_ps_loc = pd.DataFrame(success["ps_loc_0"])
    success_ps_loc["time"] = [[i[1]["call_time"], i[1]["ps_timestamp"][0] - ridetime_by_type(i[1])] for i in success.iterrows()]
    success_ps_loc.columns = ["loc", "time"]

    return success, [remain_taxi, remain_ps], success_ps_loc

def generate_trips_data_and_driving(taxi_data):
    to_ps_taxi =  taxi_data[["board_status", "cartype", "to_ps_route","to_ps_timestamp"]]
    to_ps_taxi.columns = ["vendor", "type", "path", "timestamps"]
    to_ps_taxi = list(to_ps_taxi.T.to_dict().values())

    taxi_data["board_status"] = 0
    taxi = taxi_data[["board_status", "cartype", "ps_route", "ps_timestamp"]]
    taxi.columns = ["vendor", "type", "path", "timestamps"]
    taxi = list(taxi.T.to_dict().values())
    to_ps_taxi.extend(taxi)
    
    taxi_data["board_status"] = 1
    taxi_data["tx_loc"] = taxi_data["ps_loc_1"]
    taxi_data = taxi_data[['no', 'cartype', 'work_start', 'work_end', 'board_status', "end_time",'tx_loc']]
    return taxi_data, to_ps_taxi

### 기본 매칭 알고리즘 휠체어 사용자 우선 매칭
def basic_match_dispatch(call_data, taxi_data, date, model):
    
    taxi_statistics_inf = pd.DataFrame()
    ps_locations_inf = pd.DataFrame()

    #휠체어, 비휠체어 승객 데이터 분할
    passenger_call_0 = call_data.loc[call_data["ps_type"] == 0]
    passenger_call_1 = call_data.loc[call_data["ps_type"] == 1]

    #휠체어, 비휠체어 차량 데이터 분할
    taxi_locations_0 = taxi_data.loc[taxi_data["cartype"] == 0]
    taxi_locations_1 = taxi_data.loc[taxi_data["cartype"] == 1]

    ##################################################################################
    ##휠체어 배차
    success_1, remain_1, ps_loc_inf = dispatch_data_col_update(passenger_call_1, taxi_locations_1, date, model)
    ps_locations_inf = pd.concat([ps_locations_inf,ps_loc_inf])
    taxi_statistics_inf = pd.concat([taxi_statistics_inf,success_1[["no","dispatch_time","wait_time", "drive_time", "ps_distance", "to_ps_distance"]]])

    ###휠체어 고객 배차 후 데이터 반환
    driving_1, trip_1 = generate_trips_data_and_driving(success_1)
    ###################################################################################
    ##비휠체어 고객 배차
    #모든 휠체어 고객 배차 성공 시
    if len(remain_1[1]) == 0:
        #비휄체어 고객 배차
        taxi_remain = pd.concat([remain_1[0], taxi_locations_0])
        success_2, remain_2, ps_loc_inf = dispatch_data_col_update(passenger_call_0, taxi_remain, date, model)
        ps_locations_inf = pd.concat([ps_locations_inf,ps_loc_inf])
        taxi_statistics_inf = pd.concat([taxi_statistics_inf,success_2[["no","dispatch_time","wait_time", "drive_time", "ps_distance", "to_ps_distance"]]])
        
        taxi_remain = remain_2[0]

        ###비휠체어 고객 배차 후 데이터 반환
        driving_2, trip_2 = generate_trips_data_and_driving(success_2)
        
        if len(remain_2[1]) > 0: 
            passenger_remain = remain_2[1]
        else:
            passenger_remain = pd.DataFrame()
    #차가 없으면 이번 time pass
    elif len(remain_1[1]) > 0: 
        taxi_remain = pd.concat([remain_1[0], taxi_locations_0])
        success_2, remain_2, ps_loc_inf = dispatch_data_col_update(passenger_call_0, taxi_remain, date, model)
        ps_locations_inf = pd.concat([ps_locations_inf,ps_loc_inf])
        taxi_statistics_inf = pd.concat([taxi_statistics_inf,success_2[["no","dispatch_time","wait_time", "drive_time", "ps_distance", "to_ps_distance"]]])
        ###비휠체어 고객 배차 후 데이터 반환
        driving_2, trip_2 = generate_trips_data_and_driving(success_2)    
        passenger_remain = pd.concat([remain_1[1],remain_2[1]])
        taxi_remain = remain_2[0]
    
    trip = trip_1 + trip_2
    driving = pd.concat([driving_1, driving_2])
    return trip, driving, passenger_remain, taxi_remain, taxi_statistics_inf, ps_locations_inf

def match_taxi_ps(call_data, taxi_data, date, model):
    priority_call_data = call_data.loc[call_data["call_time"] != max(call_data["call_time"])].sort_values(by=["call_time"])
    now_call_data = call_data.loc[call_data["call_time"] == max(call_data["call_time"])]
    if len(priority_call_data) != 0:
        if len(priority_call_data) <= len(taxi_data):
            trip, driving, passenger_remain, taxi_remain, taxi_statistics_inf, ps_locations_inf = basic_match_dispatch(priority_call_data, taxi_data, date, model)
            passenger_remain = pd.concat([passenger_remain, now_call_data])
            if len(taxi_remain) > 0:
                trip1, driving1, passenger_remain, taxi_remain, taxi_statistics_inf1, ps_locations_inf1 = basic_match_dispatch(passenger_remain, taxi_remain, date, model)
                
                trip = trip + trip1
                driving = pd.concat([driving, driving1])
                taxi_statistics_inf = pd.concat([taxi_statistics_inf, taxi_statistics_inf1])
                ps_locations_inf = pd.concat([ps_locations_inf, ps_locations_inf1])
            else:
                pass
        elif len(priority_call_data) > len(taxi_data):
            sub_priority_call_data = priority_call_data.head(len(taxi_data))
            remain_priority_call_data = priority_call_data.tail(len(priority_call_data) -len(taxi_data))
            
            trip, driving, passenger_remain, taxi_remain, taxi_statistics_inf, ps_locations_inf = basic_match_dispatch(sub_priority_call_data, taxi_data, date, model)
            passenger_remain = pd.concat([now_call_data, remain_priority_call_data, passenger_remain])
    else: 
        trip, driving, passenger_remain, taxi_remain, taxi_statistics_inf, ps_locations_inf = basic_match_dispatch(call_data, taxi_data, date, model)
    
    # 콜 실패 고객 콜 수락 대기 시간 더해주기
    if len(passenger_remain) > 0:
        passenger_remain["dispatch_time"] = list(map(lambda data: data+1 ,passenger_remain["dispatch_time"]))
    
    return trip, driving, passenger_remain, taxi_remain, taxi_statistics_inf, ps_locations_inf


##Generate Empty dataset 
def stop_taxi_inf(taxi_min_inf): 
    sub_stop_taxi_inf = pd.DataFrame([taxi_min_inf[1]["no"].values, taxi_min_inf[1]["tx_loc"].values, np.array([taxi_min_inf[0]] * len(taxi_min_inf[1]))]).T
    sub_stop_taxi_inf.columns = ["no", "tx_loc", "time"]
    return sub_stop_taxi_inf

def generate_taxi_pull_over_inf(pull_over_inf):
    taxi_pull_over = []
    while len(pull_over_inf) != 0:
        sub_data= pull_over_inf.loc[pull_over_inf.tx_loc == pull_over_inf.tx_loc.iloc[0]]
        pull_over_inf = pull_over_inf.loc[pull_over_inf.tx_loc != pull_over_inf.tx_loc.iloc[0]]
        if len(sub_data) == 1:
            taxi_pull_over.extend([{"path" :[sub_data.iloc[0]["tx_loc"].x, sub_data.iloc[0]["tx_loc"].y], "timestamp" : [int(sub_data.iloc[0]["time"])]}])
        else:
            taxi_pull_over.extend([{"path" :[sub_data.iloc[0]["tx_loc"].x, sub_data.iloc[0]["tx_loc"].y], "timestamp" : [int(min(sub_data["time"])), int(max(sub_data["time"]))]}])
    return taxi_pull_over


#택시 운행 정보 및 승객 정보 생성
def generate_drive_inf(taxi_loc, taxi_stat_inf):
    taxi_final_inf = pd.DataFrame()
    ps_final_inf = pd.DataFrame()

    for i in taxi_stat_inf.groupby("no"):
        taxi_subset = pd.DataFrame([i[1]["no"].values[0], sum(i[1].wait_time) ,sum(i[1].drive_time), sum(i[1].ps_distance), sum(i[1].to_ps_distance), len(i[1])]).T
        taxi_subset.columns = ["no", "total_to_ps_drive_time", "total_ps_drive_time","total_ps_distance", "total_to_ps_distance", "drive_cnt"] 
        taxi_final_inf = pd.concat([taxi_final_inf,taxi_subset])
        ps_subset = pd.DataFrame([i[1].dispatch_time.values, i[1].wait_time.values, i[1].time.values]).T
        ps_subset.columns = ["dispatch_time", "wait_time", "time"]
        ps_final_inf = pd.concat([ps_final_inf,ps_subset])
        
    not_work_taxi = pd.DataFrame(taxi_loc.loc[list(map(lambda data: data not in taxi_final_inf.no.tolist(), taxi_loc.no))].no.tolist(), columns=["no"])
    not_work_taxi["total_drive_time"] = 0 
    not_work_taxi["total_ps_distance"] = 0
    not_work_taxi["total_to_ps_distance"] = 0
    not_work_taxi["drive_cnt"] = 0

    taxi_final_inf = pd.concat([taxi_final_inf, not_work_taxi])
    return ps_final_inf, taxi_final_inf


