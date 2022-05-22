from my_azure_storage import *
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import requests
import datetime as dt

## 데이터 컬럼 설명
'''
no : 차량고유번호
cartype : '차량타입'
receipttime : '예정일시'
settime : '배차일시'
ridetime : '승차일시'
startpos1 : '출발지구군'
startpos2 : '출발지상세'
endpos1 : '목적지구군'
endpos2 : '목적지상세'
'''

def load_disabled_calltaxi_data(date):
    ## 요청 인자
    key = '474d574475686e753130366a52454b54'
    file_type = 'xml' # xml - xml, xls - 엑셀, json - json
    service = 'disabledCalltaxi' # 장애인콜시스템
    start_index = 1 # 데이터 행 시작번호
    end_index = 200 # 데이터 행 끝번호
    reg_date = date # 요청일
    
    ## 요청 url
    url = f'http://openapi.seoul.go.kr:8088/{key}/{file_type}/{service}/{start_index}/{end_index}/{reg_date}'

    ## API 요청
    html = requests.get(url)
    soup = bs(html.text)

    ## parsing
    data = []
    items = soup.findAll('item')
    for item in items:
        no = item.find('no').text
        cartype = item.find('cartype').text
        receipttime = item.find('receipttime').text
        settime = item.find('settime').text
        ridetime = item.find('ridetime').text
        startpos1 = item.find('startpos1').text
        startpos2 = item.find('startpos2').text
        endpos1 = item.find('endpos1').text
        endpos2 = item.find('endpos2').text

        data.append([no, cartype, receipttime, settime, ridetime, startpos1, startpos2, endpos1, endpos2])

    ## list => dataframe
    df = pd.DataFrame(data, columns=['no', 'cartype', 'receipttime', 'settime', 'ridetime', 'startpos1', 'startpos2', 'endpos1', 'endpos2'])    
    
    ## 결측치나 입력이 이상하게 되있는 경우 제외
    def error_change_nan(df, columns):
        df[f"{columns}"] = [i if "오" in i else np.nan for i in df[f"{columns}"]]
        return df

    for i in ['receipttime', 'settime', 'ridetime']:
        df = error_change_nan(df, i)
    
    df = df.replace('',np.nan)
    df = df.dropna(axis=0)
    return df

def data_prepared(df):
    ## string column to datetime column
    df['receipttime'] = pd.to_datetime(df['receipttime'].map(lambda x: x.replace('오전', 'AM') if '오전' in x else x.replace('오후', 'PM')), format = "%Y-%m-%d %p %I:%M:%S")
    df['settime'] = pd.to_datetime(df['settime'].map(lambda x: x.replace('오전', 'AM') if '오전' in x else x.replace('오후', 'PM')), format = "%Y-%m-%d %p %I:%M:%S")
    df['ridetime'] = pd.to_datetime(df['ridetime'].map(lambda x: x.replace('오전', 'AM') if '오전' in x else x.replace('오후', 'PM')), format = "%Y-%m-%d %p %I:%M:%S")
    
    ## split date & time function
    def split_column(df, col_name):
        df[f'{col_name}_date'] = df[col_name].dt.date
        df[f'{col_name}_time'] = df[col_name].dt.time
        df = df.drop([col_name], axis=1)
        return df

    ## split data
    for col_name in ['receipttime', 'settime', 'ridetime']:
        df = split_column(df, col_name)
    return df

def container_blob_check(date): 
    #container 연결
    rawdata_container = connect_container("rawdata")
    #blob 리스트
    blob_list = [i.name for i in rawdata_container.list_blobs()]
    
    if len(date) > 1:
        ###요청일자 확인 
        mask = np.array(list(map(lambda data: f"{data}.json" in blob_list, date)))
        if mask.any() == False: 
            date_1 = load_disabled_calltaxi_data(date[0])
            date_2 = load_disabled_calltaxi_data(date[1])
            blob_uploader(date_1.to_json(), "rawdata", date[0])
            blob_uploader(date_2.to_json(), "rawdata", date[1])
            date_1 = load_json_trans_data(date[0], rawdata_container)
            date_2 = load_json_trans_data(date[1], rawdata_container)
        elif mask.all():
            date_1 = load_json_trans_data(date[0], rawdata_container)
            date_2 = load_json_trans_data(date[1], rawdata_container)
        else: 
            mask = np.where(mask == False)[0][0]
            if mask == 0:
                date_1 = load_disabled_calltaxi_data(date[0])
                blob_uploader(date_1.to_json(), "rawdata", date[0])
            elif mask == 1:
                date_2 = load_disabled_calltaxi_data(date[1])
                blob_uploader(date_2.to_json(), "rawdata", date[1])
            date_1 = load_json_trans_data(date[0], rawdata_container)
            date_2 = load_json_trans_data(date[1], rawdata_container)
        return date_1, date_2
    elif len(date) == 1:
        date_list = f"{date[0]}.json"
        if date_list in blob_list:
            date_1 = load_json_trans_data(date[0], rawdata_container)
        else: 
            date_1 = load_disabled_calltaxi_data(date[0])
            blob_uploader(date_1.to_json(), "rawdata", date[0])
            date_1 = load_json_trans_data(date[0], rawdata_container)
        return date_1
    
#20220101 -> 20220101 00:06:00 ~ 20220102 00:06:00 (배차일시 기준)
#20220101 -> 20220101 00:06:00 ~ 20220102 00:06:00 (배차일시 기준)
def dispatch_data_loader(date):
    Day = dt.datetime.strptime(date,"%Y%m%d")
    date = [dt.datetime.strftime(Day, "%Y%m%d"), dt.datetime.strftime(Day+dt.timedelta(days=1), "%Y%m%d")]
        
    # Storage를 통해 데이터 load
    date_1, date_2 = container_blob_check(date)
    
    ### Day1
    date_1 = data_prepared(date_1)
    date_hour_mask_1 = list(map(lambda data : data.hour >=6 ,date_1["receipttime_time"].tolist()))
    date_day_mask_1 = list(map(lambda data : data.day == (Day+dt.timedelta(days=1)).day ,date_1["receipttime_date"].tolist()))
    mask_1 = [any([h,d]) for h,d in zip(date_hour_mask_1, date_day_mask_1)]
    #요청 날짜 06~24시
    date_1 = date_1.loc[mask_1]
    
    ### Day2 
    date_2 = data_prepared(date_2)
    
    date_hour_mask_2 = list(map(lambda data : data.hour <=5 ,date_2["receipttime_time"].tolist()))
    date_day_mask_2 = list(map(lambda data : data.day == (Day+dt.timedelta(days=1)).day ,date_2["receipttime_date"].tolist()))
    mask_2 = [all([h,d]) for h,d in zip(date_hour_mask_2, date_day_mask_2)]
    #요청 날짜 다음날 00~06시
    date_2 = date_2.loc[mask_2]
    
    date = pd.concat([date_1, date_2])
    return date

def basic_loader(date):
    # Storage를 통해 데이터 load
    date_1 = container_blob_check([date])
    date_1 = data_prepared(date_1)
    return date_1
