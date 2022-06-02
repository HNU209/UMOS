from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import numpy as np
import asyncio
import json
import os

folder_loc = os.path.dirname(os.path.abspath(__file__))

def start():
    load_dotenv()
    if not os.path.isdir(f'{folder_loc}/json'):
        os.makedirs(f'{folder_loc}/json')
    
# def range_split(blob_client):
#     length = blob_client.get_blob_properties().size
#     size_split = np.linspace(0, length, 4, dtype=int).tolist()
#     size_split_range = []
        
#     for idx, i in enumerate(range(len(size_split[:-1]))):
#         if idx == 0:
#             size_split_range.append([size_split[i], size_split[i+1]])
#         else:
#             size_split_range.append([size_split[i]+1, size_split[i+1]])
#     return size_split_range
        
# def merge_json(type):
#     file_list = os.listdir(os.path.join(folder_loc, 'json'))
#     data_lst = []
    
#     for file in file_list:
#         if 'trip_' in file:
#             with open(f'{folder_loc}/json/{file}', 'r') as f:
#                 data = f.read()
#             data_lst.append(data)

#     data = ''.join(data_lst)
#     data = json.loads(data)

#     with open(f'{folder_loc}/json/{type}.json', 'w') as f:
#         json.dump(data, f)

# async def get_split_data(idx, type, start, end, client):
#     with open(f'{folder_loc}/json/{type}_{idx}.json', 'wb') as f:
#         download_stream = client.download_blob(start_range=start, end_range=end)
#         f.write(download_stream.readall())

# async def get_data(type, blob_client):
#     split_range = range_split(blob_client)
    
#     if type == 'trip':
#         await asyncio.gather(
#             get_split_data(1, type, split_range[0][0], split_range[0][1], blob_client),
#             get_split_data(2, type, split_range[1][0], split_range[1][1], blob_client),
#             get_split_data(3, type, split_range[2][0], split_range[2][1], blob_client),
#         )
#         merge_json(type)
#     else:
#         with open(f'{folder_loc}/json/{type}.json', 'wb') as f:
#             f.write(blob_client.download_blob().readall())

async def get_data(container_client, type):
    blob_name = os.environ.get(type)
    blob_client = container_client.get_blob_client(blob_name)
    with open(f'{folder_loc}/json/{type}.json', 'wb') as f:
        f.write(blob_client.download_blob().readall())
        
async def async_gather(container_client):
    await asyncio.gather(
        get_data(container_client, 'trip'),
        get_data(container_client, 'empty'),
        get_data(container_client, 'ps'),
        get_data(container_client, 'result'),
    )
        
def main():
    start()
    client = BlobServiceClient.from_connection_string(os.environ.get('connect_str'))
    container_client = client.get_container_client(os.environ.get('container_name'))
    asyncio.run(async_gather(container_client))