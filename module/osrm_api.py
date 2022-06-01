###import packages 
import itertools
import warnings 
import polyline
import requests
import math
import numpy as np
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from module.ETA_model import ETA_data_prepared
import pickle

warnings.filterwarnings("ignore")

#holiday_date = holiday_api_year("2022")

###승객 route 추가 (osrm 이용) 
def get_res(pickup_point, dropoff_point):
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    steps = "?steps=true"
    loc = "{},{};{},{}".format(pickup_point.x, pickup_point.y, dropoff_point.x, dropoff_point.y)
    url = "http://203.247.62.228:3388/route/v1/driving/"
    r = session.get(url + loc + steps) 
    if r.status_code!= 200:
        return {}
  
    res = r.json()   
    all_steps = res["routes"][0]["legs"][0]["steps"]
    all_steps = all_steps[:-1]
    return all_steps

def get_part_time(step):
    duration_part = math.ceil((step["duration"] / 60)*100)/100
    location_part = polyline.decode(step["geometry"])
    duration_part = [math.ceil((duration_part/(len(location_part)-1)*100))/100] * (len(location_part) - 1)
    return duration_part

def get_part_route(step):
    location_part = polyline.decode(step["geometry"])
    location_part = list(map(lambda data: [data[1],data[0]] ,location_part))
    return location_part
    
def get_total_route(all_step):
    total_route = list(map(lambda data: get_part_route(data), all_step))
    last_location = total_route[-1][-1]
    total_route = list(map(lambda data: data[:-1], total_route))
    total_route = list(itertools.chain(*total_route))
    total_route.append(last_location)
    return total_route

def get_total_time(all_step):
    total_time = list(map(lambda data: get_part_time(data), all_step))
    total_time = list(itertools.chain(*total_time))
    total_time = list(itertools.accumulate(total_time)) 
    start_time = [0]
    start_time.extend(total_time)
    total_time = start_time
    return total_time 

def get_distance(all_step):
    total_distance = list(map(lambda data: data["distance"], all_step))
    total_distance = sum(total_distance)
    return total_distance

def get_route_time_dataframe(data_frame, date, model):
    total_all_steps = list(map(lambda data: get_res(data[1]["start_point"], data[1]["end_point"]), data_frame.iterrows())) 
    total_all_route = list(map(lambda data: get_total_route(data), total_all_steps))
    total_all_time = list(map(lambda data: get_total_time(data), total_all_steps))
    total_all_distance = list(map(lambda data: get_distance(data), total_all_steps))
    data_frame["route"] = total_all_route 
    data_frame["timestamp"] = total_all_time
    data_frame["distance"] = total_all_distance
     ### ETA model로 시간 조정
    ETA_result = ETA_data_prepared(data_frame, date, model)
    
    data_frame["timestamp"] = [(np.array(timestamp) * weight).tolist() for timestamp, weight in zip(np.array(data_frame["timestamp"].tolist()), [p/i[-1] for i, p in zip(data_frame["timestamp"].tolist(), ETA_result)])]
    
    return data_frame 

def get_route_time_dispatch(data_frame, date, model):
    total_all_steps = list(map(lambda data: get_res(data[1]["tx_loc"], data[1]["ps_loc_0"]), data_frame.iterrows())) 
    total_all_route = list(map(lambda data: get_total_route(data), total_all_steps))
    total_all_time = list(map(lambda data: get_total_time(data), total_all_steps))
    total_all_distance = list(map(lambda data: get_distance(data), total_all_steps))
    data_frame["to_ps_route"] = total_all_route
    data_frame["to_ps_timestamp"] = total_all_time
    data_frame["to_ps_distance"] = total_all_distance
     ### ETA model로 시간 조정
    ETA_result = ETA_data_prepared(data_frame, date, model)
    data_frame["to_ps_timestamp"] = [(np.array(timestamp) * weight).tolist() for timestamp, weight in zip(np.array(data_frame["to_ps_timestamp"].tolist()), [p/i[-1] for i, p in zip(data_frame["to_ps_timestamp"].tolist(), ETA_result)])]
    return data_frame 

def get_route_time_locations(start_point, end_point):
    all_steps = get_res(start_point, end_point)
    all_route = get_total_route(all_steps)
    all_time = get_total_time(all_steps)
    all_distance = get_distance(all_steps)
    return all_route, all_time, all_distance