import os
import requests
import pandas as pd
import pytz
import logging
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, "etl_pipeline.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info("Data successfully fetched from API.")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred during data extraction: {err}")
    return None

def transform_data(data):
    try:
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

        df = df[df['type'] != 'Sammanfattning natt']
        df = df[df['type'] != 'Sammanfattning kväll och natt']
        df = df[df['type'] != 'Övrigt']

        logging.info("Data transformation completed successfully.")
        return df
    except Exception as err:
        logging.error(f"An error occurred during data transformation: {err}")
        return None

def load_data_to_bigquery(df, credentials_file, project_id, dataset_id, table_id):
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_file)
        client = bigquery.Client(credentials=credentials, project=credentials.project_id)

        try:
            client.get_dataset(dataset_id)
        except Exception:
            dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
            client.create_dataset(dataset)
            logging.info(f"Dataset {dataset_id} created.")

        job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        logging.info(f"Data loaded successfully to {table_id}.")
    except Exception as err:
        logging.error(f"An error occurred during data loading: {err}")

def etl_pipeline():
    url = "https://polisen.se/api/events"
    data = extract_data(url)
    
    if data:
        df = transform_data(data)
        
        if df is not None:
            credentials_file = r"crime-in-sweden-project-47eef163c346.json"
            project_id = "crime-in-sweden-project"
            dataset_id = "Crime_in_Sweden"
            table_id = f"{project_id}.{dataset_id}.events"
            
            load_data_to_bigquery(df, credentials_file, project_id, dataset_id, table_id)

if __name__ == "__main__":
    try:
        start_time = datetime.now()
        logging.info("ETL Pipeline started.")
        etl_pipeline()
        logging.info(f"ETL Pipeline finished. Total duration: {datetime.now() - start_time}")
    except Exception as e:
        logging.critical(f"ETL Pipeline failed: {e}")
