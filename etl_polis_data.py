import requests
import pandas as pd
import pytz
from google.cloud import bigquery
from google.oauth2 import service_account

# Extract
url = "https://polisen.se/api/events"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    sweden_tz = pytz.timezone('Europe/Stockholm')
    df['datetime'] = df['datetime'].dt.tz_convert(sweden_tz)
    
    df['date'] = df['datetime'].dt.date
    df['time'] = df['datetime'].dt.time
    
    df['location_name'] = df['location'].apply(lambda x: x['name'])
    df['location_gps'] = df['location'].apply(lambda x: x['gps'])
    df['name'] = df['name'].apply(lambda x: x.split(',')[1].strip())
    
    df['id'] = df['id'].astype('int64')
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    df[['latitude', 'longitude']] = df['location_gps'].str.split(',', expand=True)
    df['latitude'] = df['latitude'].astype(float)
    df['longitude'] = df['longitude'].astype(float)
    
    df = df.drop(columns=['location', 'location_gps', 'url'])
    
df['id'] = df['id'].astype('int64')
df['name'] = df['name'].astype('string')
df['location_name'] = df['location_name'].astype('string')
df['summary'] = df['summary'].astype('string')
df['type'] = df['type'].astype('object')
df['latitude'] = df['latitude'].astype(float)
df['longitude'] = df['longitude'].astype(float)
df['date'] = pd.to_datetime(df['date'])
df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')

df = df[df['name'] != 'Sammanfattning natt']
df = df[df['name'] != 'Sammanfattning kväll och natt']
df = df[df['name'] != 'Övrigt']

# Load
credentials = service_account.Credentials.from_service_account_file(
    r"C:\Users\lalka\OneDrive\Skrivbord\Studier\Projekt\working repo\ds_project\crime-in-sweden-project-47eef163c346.json"
)

client = bigquery.Client(credentials=credentials, project=credentials.project_id)
project_id = "crime-in-sweden-project"
dataset_id = "Crime_in_Sweden"
table_id = f"{project_id}.{dataset_id}.events"

try:
    client.get_dataset(dataset_id)
except Exception as e:
    dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
    client.create_dataset(dataset)

job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()

print(f"Data loaded successfully to {table_id}")

