# Python3 샘플 코드
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

def holiday_api_month(date):
    url = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo'
    servicekey = "OoraGlG8Wqep6KTvxGKAXZqSH36n1DryLszH/ntM6xaZ85li9b486qWrH+orpFTqj8h9mocjCaNl+1WtDG4FEQ=="
    params ={'serviceKey' : f'{servicekey}', 'solYear' : f"{date[:4]}", 'solMonth' : f'{date[4:]}' }

    response = requests.get(url, params=params)
    soup = bs(response.text, "html.parser")
    data = pd.DataFrame([[i.contents[0] for i in soup.select("datename")],[i.contents[0] for i in soup.select("locdate")]]).T
    data.columns = ["datename","date"]
    return data

def holiday_api_year(date):
    data = [holiday_api_month(date+i) for i in [f"0{i}" if i < 10 else f"{i}" for i in range(1,13)]]
    return pd.concat(data)
