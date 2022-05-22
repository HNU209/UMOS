import pandas as pd
import numpy as np
import warnings 
import matplotlib.pyplot as plt
from osrm_api import * 

warnings.filterwarnings("ignore")

### 1. 차량 분류 변경 -> 휠체어 탑승 불가능 : 0, 휠체어 탑습 가능 : 1 
def cartype_transform(ps_loc_data):
    cartype_dict = {"대형승용": 0, "중형승용": 0, "증형승용": 0, "중형승합": 1}

    ps_loc_data["cartype"] = list(map(lambda data: data.replace(" ", ""), ps_loc_data.cartype))
    ps_loc_data["cartype"] = [cartype_dict[i] for i in ps_loc_data.cartype]
    return ps_loc_data

### 2. 차량 ID 변경 0~547
def change_taxi_id(ps_loc_data):
    change_ID = {i:idx for idx,i in enumerate(set(ps_loc_data.no))}

    ps_loc_data["no"] = [change_ID[i] for i in ps_loc_data["no"]]
    return ps_loc_data

### 3. 고객 타입 임의 부여 (0 : 비휠체어, 1 : 휠체어)
def add_passenger_type(ps_loc_data):
    np.random.seed(1205)
    passenger_type_data = np.random.choice(2 ,size = len(ps_loc_data), p=[0.2, 0.8])
    ps_loc_data["passenger_type"] = passenger_type_data
    return ps_loc_data

### 4. 시간 단위 변환 함수 (0~1440분) 
# - 배차는 매 분마다 수행이 되도록
# - 매초단위로 수행할 경우 최적화를 돌리는게 큰 의미가 없음
def time_transform(ps_loc_data):
    #사용하는 컬럼만 copy
    passenger_df = ps_loc_data[['no', 
                                'cartype',
                                'passenger_type',
                                'settime_date',
                                'settime_time',
                                'receipttime_date',
                                'receipttime_time',
                                'start_point',
                                'end_point',
                                "adm_nm_start",
                                "adm_nm_end"]].copy()
    
    #택시가 콜 수락한 시간
    settime_date = pd.to_datetime(passenger_df["settime_date"], format = '%Y-%m-%d')
    settime_date = list(map(lambda data: data.day, settime_date))
    settime_time = pd.to_datetime(passenger_df['settime_time'], format='%H:%M:%S')
    
    #고객 콜 접수 시간
    receipttime_date = pd.to_datetime(passenger_df['receipttime_date'], format='%Y-%m-%d')
    receipttime_date = list(map(lambda data: data.day, receipttime_date))
    receipttime_time = pd.to_datetime(passenger_df['receipttime_time'], format='%H:%M:%S')
    
    #시분초 -> 0~1440분으로 변환
    set_time = settime_time.dt.minute + settime_time.dt.hour*60
    set_time = set_time.tolist()
    
    receipt_time = receipttime_time.dt.minute + receipttime_time.dt.hour*60
    receipt_time = receipt_time.tolist()
    
    passenger_df['time'] = [t+1440 if d == 17 else t for t,d in zip(receipt_time, receipttime_date)]
    passenger_df['set_time'] = [t+1440 if d == 17 else t for t,d in zip(set_time, settime_date)]
    
    passenger_df.drop(['settime_date','settime_time','receipttime_date','receipttime_time'], axis=1, inplace=True)
    passenger_df.reset_index(drop=True, inplace=True)
    return passenger_df


### 6.택시 운행 정보 데이터 추출
def generate_taxi_inf(ps_loc_data):
    taxi_start_end_dict = dict()
    for i in ps_loc_data.groupby("no"):
        taxi_start_end_dict[i[0]] = {"start":min(i[1]["set_time"])}
    
    taxi_inf = pd.DataFrame(taxi_start_end_dict.values())
    taxi_inf["no"] = taxi_start_end_dict.keys()
    
    np.random.seed(1205)
    taxi_inf["cartype"] = np.random.choice(2 ,size = len(taxi_inf), p=[0.2, 0.8])
    taxi_inf = taxi_inf[["no", "cartype", "start"]]
    return taxi_inf

### 7. 택시 근무시간 고려 출퇴근시간 임의 지정
def operation_inf(taxi_information):
    #A조 17시 이전 근무자 9시간 근무
    #B조 17시 이후 근무자 12시간 근무 
    bins = [i*60 for i in range(6,31)]
    labels = [i for i in range(6,30)]

    taxi_information["start_time"] = pd.cut(taxi_information["start"], bins, labels = labels)
    
    A = taxi_information.loc[np.array(taxi_information["start_time"].tolist()) < 17]
    B = taxi_information.loc[np.array(taxi_information["start_time"].tolist()) >= 17]
    A["start_time"] = np.array(A.start_time.tolist()) * 60
    B["start_time"] = np.array(B.start_time.tolist()) * 60
    
    A["end_time"] = np.array(A.start_time.tolist()) + (9*60)
    B["end_time"] = np.array(B.start_time.tolist()) + (12*60)
    taxi_information = pd.concat([A,B])
    
    taxi_information = taxi_information[["no", "cartype", "start_time", "end_time"]]
    return taxi_information

def estimate_taxi_schedule_plot(taxi_inf):
    bins = [i*60 for i in range(6,31)]
    labels = [f"{i}" for i in range(6,30)]

    start = pd.DataFrame(pd.cut(taxi_inf["start_time"], bins, labels = labels).value_counts(sort=False))
    end = pd.DataFrame(pd.cut(taxi_inf["end_time"], bins, labels = labels).value_counts(sort=False))

    f, axes = plt.subplots(1, 2)
    f.set_size_inches((22, 12))
    plt.rc('font', size=20)        # 기본 폰트 크기
    plt.rc('axes', labelsize=20)   # x,y축 label 폰트 크기

    axes[0].barh(start.index ,start["start_time"])
    axes[0].set_yticklabels(labels, fontsize=20)
    axes[0].set_xlim(0, 200)
    axes[0].set_xlabel("차량 대수")
    axes[0].set_ylabel("시간")
    axes[0].set_title("추정 운행 시작 시간 분포")

    axes[1].barh(end.index ,end["end_time"], color = "red")
    axes[1].set_yticklabels(labels, fontsize=20)
    axes[1].set_xlim(0, 200)
    axes[1].set_xlabel("차량 대수")
    axes[1].set_ylabel("시간")
    axes[1].set_title("추정 운행 종료 시간 분포")
    plt.savefig("./result_data/추정운행정보.png")


### 8. 승객 데이터, 택시 데이터 컬럼명 재정의 및 필요 컬럼 추가: 추후 혼동 방지
def redefine_col_name(ps_loc_data, taxi_loc_data): 
    # 컬럼명 변경
    ps_loc_data.columns = ['no', 'cartype', 'ps_type', 'ps_loc_0', 'ps_loc_1', 'adm_nm_start', 'adm_nm_end','call_time', 'set_time', 'ps_route', 'ps_timestamp', 'ps_distance']
    taxi_loc_data.columns = ['no', 'cartype', 'work_start', 'work_end', 'board_status', 'tx_loc']
    # 전처리 후 필요한 컬럼만 추출
    ps_loc_data = ps_loc_data[['ps_type', 'ps_loc_0', 'ps_loc_1', 'call_time', "adm_nm_start", "adm_nm_end", 'ps_route', 'ps_timestamp', 'ps_distance']]
    taxi_loc_data = taxi_loc_data[['no', 'cartype', 'work_start', 'work_end', 'board_status', 'tx_loc']]
    #콜 잡고 차량 올때까지 대기시간
    ps_loc_data["wait_time"] = 0
    #콜 잡히는데 걸리는 시간
    ps_loc_data["dispatch_time"] = 0
    #콜 실패 유무 0:성공, 1:실패 -> 지금은 실패가 없어서 알고리즘 업데이트 아직 x
    ps_loc_data["request_fail"] = 0
    #택시 승객 탑승 유무 (0:탑승, 1:미탑승)
    taxi_loc_data["board_status"] = 1
    return ps_loc_data, taxi_loc_data


### *전처리 메인 함수
def dispatch_data_preprocessing(ps_loc_data, taxi_loc_data): 
    # 승객 전처리
    ps_loc_data = cartype_transform(ps_loc_data)
    ps_loc_data = change_taxi_id(ps_loc_data)
    ps_loc_data = add_passenger_type(ps_loc_data)
    ps_loc_data = time_transform(ps_loc_data)
    ps_loc_data = get_route_time_dataframe(ps_loc_data)

    # 택시 전처리
    taxi_inf = generate_taxi_inf(ps_loc_data)
    taxi_schedule = operation_inf(taxi_inf)
    estimate_taxi_schedule_plot(taxi_schedule) #데이터 기반 택시 운행 추정
    taxi_loc_data["no"] = list(taxi_schedule.no)
    taxi_loc_data = taxi_loc_data.drop(["Taxi_ID"], axis=1)
    taxi_loc_data = pd.merge(taxi_schedule,taxi_loc_data)

    # 승객, 택시 컬럼 추가 및 재정의
    ps_loc_data, taxi_loc_data = redefine_col_name(ps_loc_data, taxi_loc_data)
    return ps_loc_data, taxi_loc_data
