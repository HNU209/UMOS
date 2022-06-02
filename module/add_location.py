from module.disabled_passenger_api import dispatch_data_loader
from module.my_azure_storage import *
import osmnx as ox
from numpy import random 
from shapely.geometry import Point

import geopandas as gpd
import pandas as pd
import numpy as np
import itertools
import re 
from tqdm import tqdm
import warnings 

warnings.filterwarnings("ignore")

extradata_ct = connect_container("extradata")

## 도로 데이터
edges = load_json_trans_data("edges", extradata_ct, type = "gpd")
nodes = load_json_trans_data("nodes", extradata_ct, type = "gpd")

##행정구역 데이터
hjd_20180401 = load_json_trans_data("hjd_20180401", extradata_ct, type = "gpd")

#운영지역인 "서울", "인천", "경기"만 추출
def hjd_filter(data):
    #11 서울, 23 인천, 31 경기 
    return (data[:2] == "11") | (data[:2] == "23") | (data[:2] == "31")

hjd_20180401 = hjd_20180401.loc[list(map(lambda data: hjd_filter(data) ,hjd_20180401.adm_cd))]


# "방화 제3동' 처럼 숫자 앞 "제"가 들어가 있는 것을 "방화3동"으로 변경, 
# 정규표현식으로 [제+숫자] 패턴이 있으면 "제"를 제거 후 위치 변수를 생성해준다 
def generate_places_name(main_category, middle_category):
    #변경된 행정구역명 변수 생성 
    change_dict = {"명륜1가동": "혜화동", "명륜2가동":"혜화동", "명륜3가동":"혜화동", "명륜4가동":"혜화동", 
                "명륜5가동":"혜화동","답십리3동":"답십리1동","답십리4동":"답십리2동","장안3동":"장안2동", 
                "장안3동":"장안1동","제기1동":"제기동", "제기2동":"제기동","장안4동":"장안2동","신설동":"용신동",
                "전농3동":"전농2동","공릉1.3동":"공릉1동", "이문3동":"이문2동","고촌면":"고촌읍", "소사본1동":"소사본동", "소사본2동":"소사본동",
                "양촌면":"양촌읍", "용두동":"용신동", "신당3동": "신당동", "신당4동":"신당동" ,"신당6동":"신당동",
                "신당2동":"신당동", "신당1동":"신당동", "김포1동":"김포본동", "김포2동":"장기본동", "지금동":"다산2동", "도농동":"다산2동",
                "가능2동":"흥선동", "가능3동":"흥선동", "신흥동": "오정동"}
    
    p = re.compile("제+[0-9]")
    mask =  p.findall(middle_category)
    mask = [mask[0][1:]] if len(list(itertools.chain(*mask))) > 2 else mask
    if len(mask) > 0:
        middle_category = middle_category.split(mask[0])[0] + mask[0][1] + middle_category.split(mask[0])[1]
    try: 
        middle_category = change_dict[middle_category]
    except:
        pass
    category = middle_category + " " + main_category
    return category

#데이터에 맞는 법정동 geometry 리스트 반환
def get_location_bjd_geometry_and_admname(location_list, hjd_df):
    HJD_Dong_2018 = list(map(lambda data: data.split(" ")[-1], hjd_df.adm_nm))
    HJD_Sigon_2018 = list(map(lambda data: data.split(" ")[1], hjd_df.adm_nm))

    hjd_geometry = []
    adm_code = []
    for i in location_list:
        place = i.split(" ")
        step1_mask = np.where(np.array(HJD_Dong_2018) == place[0])[0].tolist()
        if len(step1_mask) == 1:
            hjd_geometry.append(hjd_df.iloc[step1_mask[0]].geometry)
            adm_code.append(hjd_df.iloc[step1_mask[0]].adm_nm)
        else:
            step2_mask = np.where(np.array(HJD_Sigon_2018) == place[1])[0].tolist()
            step2_mask = set(step1_mask) & set(step2_mask)
            hjd_geometry.append(hjd_df.iloc[list(step2_mask)[0]].geometry)
            adm_code.append(hjd_df.iloc[list(step2_mask)[0]].adm_nm)
            
    return hjd_geometry, adm_code

#행정구역 별 랜덤 좌표 필요한 갯수 데이터프레임 추출
def generate_location_cnt_df(move_data, where):
    pos_cnt = move_data[f"{where}pos"].value_counts().to_frame().reset_index()
    pos_cnt.columns = [f"{where}pos", "cnt"]    
    pos_cnt = pd.merge(move_data[[f"{where}pos", f"{where}_geometry"]].drop_duplicates([f"{where}pos"]), pos_cnt)
    return pos_cnt

#위치 좌표 랜덤 생성
def Generate_random_location(data, CNT):   #place : 관심지역,  cnt: 차량 수    
    #Meter -> Euclid : 단위 변환
    def euclid_distance_cal(meter):
        ###유클리드 거리와 실제 거리를 기반으로 1미터당 유클리드 거리 추출
        #점 쌍 사이의 유클리드 거리를 계산
        dis_1 = ox.distance.euclidean_dist_vec(36.367658 , 127.447499, 36.443928, 127.419678)
        #직선거리 계산
        dis_2 = ox.distance.great_circle_vec(36.367658 , 127.447499, 36.443928, 127.419678)
        return dis_1/dis_2 * meter
    
    #위치 좌표 랜덤 생성
    locations = []
    for i in random.choice(range(len(data)), size = CNT, replace = True):
        #교차로 중심에 생성되지 않게 고정 미터로 생성이 아닌 해당 링크 길이로 유동적인 미터 생성
        random_num = random.choice([0.1,0.2,0.3,0.4,0.5])
        random_meter = data.iloc[i]["length"] * random_num
        #좌표 생성
        new_node = list(ox.utils_geo.interpolate_points(data.iloc[i]["geometry"], euclid_distance_cal(random_meter)))
        #좌표의 처음과 끝은 노드이기 때문에 제거하고 선택
        del new_node[0], new_node[-1]
        #랜덤으로 선택한 하나의 링크에서 하나의 택시 좌표 선택 
        idx = random.choice(len(new_node), size = 1)
        location = new_node[idx[0]]
        locations.append(location)
        
    locations = list(map(lambda data: Point(data),locations))

    return locations

#도로 행정구역 경계로 서브셋 추출
def generate_subset(geometry, data_edges):
    data_edges["idx"] = range(len(data_edges))
    
    subset = gpd.GeoDataFrame({"geometry": [geometry]})
    subset = data_edges.iloc[sorted(gpd.sjoin(subset, data_edges,how='left', op="intersects").idx.values)]
    return subset


def main_random_location(data_edges, pos_cnt, move_data, where):
    random_locations = []

    for i in tqdm(range(len(pos_cnt))):
        subset = generate_subset(pos_cnt.iloc[i][f"{where}_geometry"], data_edges)
        random_location = Generate_random_location(subset, pos_cnt.iloc[i].cnt)
        random_locations.append(random_location)
    pos_cnt[f"{where}_random_location"] = random_locations
    
    node_mask_dict = dict()
    for i in range(len(pos_cnt)):
        mask =  np.where(np.array(move_data[f"{where}pos"]) == pos_cnt.iloc[i][f"{where}pos"])[0].tolist()
        nodes = pos_cnt.iloc[i][f"{where}_random_location"]
        for m,n in zip(mask,nodes):
            node_mask_dict[m] = n
            
    return pos_cnt, node_mask_dict

def add_ps_location(disabled_data, hjd_20180401 = hjd_20180401, mode = "basic"):
    #출발지, 도착지 리스트로 정의
    if mode == "basic":
        start_location = list(map(lambda data: generate_places_name(disabled_data.iloc[data]["startpos1"], disabled_data.iloc[data]["startpos2"]), range(len(disabled_data))))
        end_location = list(map(lambda data: generate_places_name(disabled_data.iloc[data]["endpos1"], disabled_data.iloc[data]["endpos2"]), range(len(disabled_data))))

        disabled_data["startpos"] = [i.replace(".","·") if "." in i else i for i in start_location]
        disabled_data["endpos"] = [i.replace(".","·") if "." in i else i for i in end_location]
    elif mode == "fake":
        pass
    start_result = get_location_bjd_geometry_and_admname(disabled_data["startpos"], hjd_20180401)
    end_result = get_location_bjd_geometry_and_admname(disabled_data["endpos"], hjd_20180401)

    disabled_data["start_geometry"] = start_result[0]
    disabled_data["end_geometry"] = end_result[0]
    disabled_data["adm_cn_start"] = start_result[1]
    disabled_data["adm_cn_end"] = end_result[1]
    
    startpos_cnt =  generate_location_cnt_df(disabled_data,"start")
    endpos_cnt =  generate_location_cnt_df(disabled_data,"end")

    startpos_cnt, start_dict = main_random_location(edges, startpos_cnt, disabled_data, "start")
    endpos_cnt, end_dict = main_random_location(edges, endpos_cnt, disabled_data, "end")

    disabled_data["start_point"] = [start_dict[i] for i in range(len(disabled_data))]
    disabled_data["end_point"] = [end_dict[i] for i in range(len(disabled_data))]
    try: 
        disabled_data = disabled_data[["no", "cartype", "settime_date", "settime_time", "receipttime_date", "receipttime_time",
                                    "start_point", "end_point", "adm_cn_start", "adm_cn_end", "start_geometry", "end_geometry"]]
    except:
        pass
    return disabled_data





