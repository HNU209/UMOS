###import packages 
import numpy as np
import itertools
import warnings 
from ortools.linear_solver import pywraplp
from itertools import repeat

warnings.filterwarnings("ignore")

#####################################################################################################################
### 배차 알고리즘

###costs 뽑는 과정
# cost - 차량과 승객의 직선 거리(meter) 뽑는 함수  
def haversine(lat1, lon1, lat2, lon2):
    km_constant = 3959* 1.609344
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    km = km_constant * c
    return km

# 운행 가능한 모든 차량과 호출 승객의 모든 costs 구하는 함수 
def get_taxi_meter(ps_loc_data, taxi_loc_data):
    return list(map(lambda data: haversine(data.y, data.x, taxi_loc_data.y, taxi_loc_data.x).tolist(), ps_loc_data))

#####################################################################################################################
### 배차 알고리즘

def dispatch(passenger_location_data, taxi_location_data, cost_matrix):
    #Calculate cost matrix
    # 모든 빈택시와 모든 승객들에 대해서 각각의 통행시간을 계산
    passenger_cnt = len(passenger_location_data)
    taxi_cnt = len(taxi_location_data)
    
    #Declare the MIP solver
    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver('SCIP')

    taxi_idx = sorted(list(itertools.chain(*list(repeat(list(range(taxi_cnt)), passenger_cnt)))))
    passenger_idx = list(itertools.chain(*list(repeat(list(range(passenger_cnt)), taxi_cnt))))

    #Create the variables
    # x[i, j] is an array of 0-1 variables, which will be 1
    # if worker i is assigned to task j.
    x = {}
    for t, p in zip(taxi_idx, passenger_idx):
        x[t, p] = solver.IntVar(0, 1, '')

    #Create the constraints
    #Each worker is assigned to at most 1 task.
    for i in range(taxi_cnt):
        solver.Add(solver.Sum([x[i, j] for j in range(passenger_cnt)]) <= 1)

    # Each task is assigned to exactly one worker.
    for j in range(passenger_cnt):
        solver.Add(solver.Sum([x[i, j] for i in range(taxi_cnt)]) == 1)

    #Create the objective function
    objective_terms = []
    for i in range(taxi_cnt):
        for j in range(passenger_cnt):
            objective_terms.append(cost_matrix[i][j] * x[i, j])

    solver.Minimize(solver.Sum(objective_terms))
    #Invoke the solver
    status = solver.Solve()
    # Print solution
    taxi_iloc = []
    passenger_iloc = []

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        #print('Total distance = ', solver.Objective().Value(), '\n')
        for i in range(taxi_cnt):
            for j in range(passenger_cnt):
                # Test if x[i,j] is 1 (with tolerance for floating point arithmetic).
                if x[i, j].solution_value() > 0.5:
                    #print('taxi %d assigned to passenger %d.  duration(s) = %d' %
                    #    (i, j, cost_matrix[i][j]))  
                    taxi_iloc.append(i) 
                    passenger_iloc.append(j)
    return passenger_iloc, taxi_iloc

# main 배차 함수
def main_dispatch(ps_loc_data, taxi_loc_data):
    if len(ps_loc_data) <= len(taxi_loc_data):  
        costs = list(map(lambda data: get_taxi_meter(ps_loc_data.ps_loc_0, data), taxi_loc_data.tx_loc))
        passenger_iloc, taxi_iloc = dispatch(ps_loc_data, taxi_loc_data, costs)
    elif len(ps_loc_data) > len(taxi_loc_data):
        costs = list(map(lambda data: get_taxi_meter(taxi_loc_data.tx_loc, data), ps_loc_data.ps_loc_0))
        taxi_iloc, passenger_iloc = dispatch(taxi_loc_data, ps_loc_data, costs)
    return passenger_iloc, taxi_iloc