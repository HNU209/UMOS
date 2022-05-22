from azure.storage.blob import BlobServiceClient, BlobClient
import geopandas as gpd
import pandas as pd
import json

#rawdata container 연결
def connect_container(container): 
    ### storage connect str (고유값)
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=umos;AccountKey=1cQ5o/cYK4vQQrvWqSXFaZJ8YII5egNWABOlCEdpI5gnC+kjiGChoMF+eNVlGzUtDF8WdqYEiYXZJOSCL8pJBQ==;EndpointSuffix=core.windows.net'
    ### storage connect
    client = BlobServiceClient.from_connection_string(connect_str)
    #rawdata container 없으면 생성
    try:
        client.create_container(container)
    except:
        pass
    #rawdata container 연결
    rawdata_container = client.get_container_client(container) 
    return rawdata_container

def blob_uploader(data, container, save_name):
    ### storage connect str (고유값)
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=umos;AccountKey=1cQ5o/cYK4vQQrvWqSXFaZJ8YII5egNWABOlCEdpI5gnC+kjiGChoMF+eNVlGzUtDF8WdqYEiYXZJOSCL8pJBQ==;EndpointSuffix=core.windows.net'
    
    blob = BlobClient.from_connection_string(conn_str=connect_str, container_name=container, blob_name=f"{save_name}.json")
    blob.upload_blob(data)
    print("upload success", end="\r")

def load_json_trans_data(filename, container, type="pd"):    
    json_blob = container.get_blob_client(f"{filename}.json")
    blob_data = json_blob.download_blob()
    data = json.loads(blob_data.content_as_bytes())
    if type == "pd":
        return pd.DataFrame(data)
    elif type == "gpd":
        return gpd.GeoDataFrame.from_features(data["features"])

def delete_container(container_nm):
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=umos;AccountKey=1cQ5o/cYK4vQQrvWqSXFaZJ8YII5egNWABOlCEdpI5gnC+kjiGChoMF+eNVlGzUtDF8WdqYEiYXZJOSCL8pJBQ==;EndpointSuffix=core.windows.net'
    client = BlobServiceClient.from_connection_string(connect_str)
    client.delete_container(f"{container_nm}")

def container_list():
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=umos;AccountKey=1cQ5o/cYK4vQQrvWqSXFaZJ8YII5egNWABOlCEdpI5gnC+kjiGChoMF+eNVlGzUtDF8WdqYEiYXZJOSCL8pJBQ==;EndpointSuffix=core.windows.net'
    client = BlobServiceClient.from_connection_string(connect_str)
    return [i.name for i in client.list_containers()]

def delete_blob(container, blob_nm):
    container = connect_container(container)    
    target_blob = container.get_blob_client(f'{blob_nm}')
    target_blob.delete_blob()
    
def blob_list(container):
    container = connect_container(container)
    return [i.name for i in container.list_blobs()]