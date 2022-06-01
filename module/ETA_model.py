from datetime import datetime
import numpy as np
from module.my_azure_storage import *
#from holiday_api import holiday_api_year
from module.osrm_api import *

def haversine(lat1, lon1, lat2, lon2):
    km_constant = 3959* 1.609344
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    km = km_constant * c
    return km

def ETA_data_prepared(self, date, model):
    try:
        self = self[["time",'start_point','end_point',"adm_cn_start","adm_cn_end"]]
    except:
        self["call_time"] = self["call_time"] + self["dispatch_time"]
        self = self[["call_time",'tx_loc','ps_loc_0',"adm_cn_start","adm_cn_end"]]
        
    self.columns = ["start_time","start_point", "end_point","start_adm","end_adm"]
    
    self["date"] = date 
    self["p_x"] = [i.x for i in self["start_point"]]       
    self["p_y"] = [i.y for i in self["start_point"]]  
    self["d_x"] = [i.x for i in self["end_point"]]       
    self["d_y"] = [i.y for i in self["end_point"]]
    self["straight_km"] = haversine(self["p_y"], self["p_x"], self["d_y"], self["d_x"])
    date = datetime.strptime(date, "%Y%m%d")
    weekday = date.weekday()
    holiday = 1 if weekday >= 5 else 0
    self["weekday"] = weekday
    self["holiday"] = holiday
    
    self = self[["p_x","p_y","d_x","d_y","start_time","straight_km","weekday","holiday", "start_adm", "end_adm"]]
    
    self["start_adm"] = self["start_adm"].astype(str)
    self["end_adm"] = self["end_adm"].astype(str)
    self["weekday"] = self["weekday"].astype(str)
    self["holiday"] = self["holiday"].astype(str)
    ETA_result = model.predict(self)
    return ETA_result
