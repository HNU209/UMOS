import pandas as pd 
import numpy as np
import itertools
import geopandas as gpd
from module.my_azure_storage import *
from module.osrm_api import *
from module.add_location import add_ps_location


def generate_fake_passenger_O_D(fake_num=0.001):
    #KT 이동량 데이터 기준 일 평균 서울지역 읍면동 별 유동 인구 RAW DATA
    extradata_ct = connect_container("extradata")
    main_data = load_json_trans_data("fake_passenger_raw_data", extradata_ct)

    #서울시 장애인 인구 4.## %(0.04) 적용?? -> 실제 장애인 비율의  1/4(0.01), 1/40(0.001), 1/400(0.0001)
    main_data["이동인구(합)"] = main_data["이동인구(합)"] * fake_num

    #포아송 분포로 만든 이동 분포
    rng = np.random.default_rng()
    s = rng.poisson(main_data["이동인구(합)"].values)

    main_data["이동인구(합)"] = s

    main_data["출발 행정동 코드"] = list(map(str, main_data["출발 행정동 코드"]))
    main_data["도착 행정동 코드"] = list(map(str, main_data["도착 행정동 코드"]))

    # 이동인구 없는 행 제거
    main_data = main_data.loc[main_data["이동인구(합)"] != 0]

    # main_data -> O-D 수 기준으로 데이터 재구성
    main_data = pd.DataFrame(list(itertools.chain(*[[i.tolist()] * j  for i,j in zip(main_data.values[:,:2], main_data.values[:,2])])), columns = ["origin_code","dest_code"])
    return main_data


def data_prepared(main_data):
    #법정동 코드
    extradata_ct = connect_container("extradata")
    hjd_20180401 = load_json_trans_data("hjd_20180401", extradata_ct, type="gpd")

    start = main_data[["origin_code"]]; end = main_data[["dest_code"]]
    start.columns = ["adm_cd"]
    end.columns = ["adm_cd"]

    start = pd.merge(start, hjd_20180401[["adm_cd", "adm_nm"]])
    end = pd.merge(end, hjd_20180401[["adm_cd", "adm_nm"]])

    main_data = pd.concat([start["adm_nm"], end["adm_nm"]], axis=1)
    main_data.columns = ["startpos", "endpos"]

    main_data["startpos"] = list(map(lambda data: f"{data.split(' ')[-1]} {data.split(' ')[1]}",main_data["startpos"]))
    main_data["endpos"] = list(map(lambda data: f"{data.split(' ')[-1]} {data.split(' ')[1]}",main_data["endpos"]))
    return main_data


###시간 단위 변환 함수 (0~1440분) 
def time_transform(ps_loc_data):
    ps_loc_data = ps_loc_data["call_time"].value_counts().reset_index() 
    ps_loc_data.columns = ["time", "cnt"]
    ps_loc_data["ratio"] = [i/sum(ps_loc_data["cnt"]) for i in ps_loc_data["cnt"]]
    return ps_loc_data

def add_passenger_type(ps_loc_data):
    np.random.seed(1205)
    passenger_type_data = np.random.choice(2 ,size = len(ps_loc_data), p=[0.2, 0.8])
    ps_loc_data["ps_type"] = passenger_type_data
    return ps_loc_data

def generate_fake_passenger(data, fake_num=5):
    fake_data = generate_fake_passenger_O_D(fake_num)
    fake_data = data_prepared(fake_data)
    fake_data = add_ps_location(fake_data, mode = "fake")
    fake_data = add_passenger_type(fake_data)
    time_data = time_transform(data)
    fake_data["time"] = np.random.choice(time_data["time"].tolist() ,size = len(fake_data), p= time_data["ratio"].tolist())
    
    fake_data = fake_data[["ps_type", "start_point", "end_point", "time", "adm_nm_start", "adm_nm_end"]]
    fake_data.columns = ["ps_type", "start_point", "end_point", "call_time", "adm_nm_start", "adm_nm_end"]
    
    fake_data = get_route_time_dataframe(fake_data)
    
    fake_data.columns = ['ps_type', 'ps_loc_0', 'ps_loc_1', 'call_time', "adm_nm_start", "adm_nm_end", 'ps_route', 'ps_timestamp', 'ps_distance']
     #콜 잡고 차량 올때까지 대기시간
    fake_data["wait_time"] = 0
    #콜 잡히는데 걸리는 시간
    fake_data["dispatch_time"] = 0
    #콜 실패 유무 0:성공, 1:실패 -> 지금은 실패가 없어서 알고리즘 업데이트 아직 x
    fake_data["request_fail"] = 0
    data = pd.concat([data, fake_data])
    return data
