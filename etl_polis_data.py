import requests
import pandas as pd
import pytz
from google.cloud import bigquery
from google.oauth2 import service_account

# Step 1: Fetch the data from the API
url = "https://polisen.se/api/events"
response = requests.get(url)

if response.status_code == 200:
    # Step 3: Load the response into a JSON format
    data = response.json()
    
    # Step 4: Convert JSON data to a Pandas DataFrame
    df = pd.DataFrame(data)
  
    # Step 5: Dealing with datetime-column
    df['datetime'] = pd.to_datetime(df['datetime'])

    sweden_tz = pytz.timezone('Europe/Stockholm')
    df['datetime'] = df['datetime'].dt.tz_convert(sweden_tz)

    df['date'] = df['datetime'].dt.date
    df['time'] = df['datetime'].dt.time
    
    # Step 6: Split 'location' into 'Location_name' and 'Location_gps'
    df['location_name'] = df['location'].apply(lambda x: x['name'])
    df['location_gps'] = df['location'].apply(lambda x: x['gps'])

    # Step 7: Extract the middle part (event type) from the 'name' field
    df['name'] = df['name'].apply(lambda x: x.split(',')[1].strip()) # Otherwise the name contains date, type of event and place

    # Step 8: Transform data types
    df['id'] = df['id'].astype('int64')  # Ensuring id is int64
    df['datetime'] = pd.to_datetime(df['datetime'])  # Converting to datetime

    # Step 9: Split 'Location_gps' into separate 'latitude' and 'longitude' columns
    df[['latitude', 'longitude']] = df['location_gps'].str.split(',', expand=True)
    df['latitude'] = df['latitude'].astype(float)  # Convert to float
    df['longitude'] = df['longitude'].astype(float)  # Convert to float

    # Step 10: Drop the original 'Location_gps' column
    df = df.drop(columns=['location', 'location_gps','url'])

else:
    print(f"Failed to fetch data. Status code: {response.status_code}")

# Change datatypes of columns to appropriate ones
df['id'] = df['id'].astype('int64') 
df['name'] = df['name'].astype('string') 
df['location_name'] = df['location_name'].astype('string')
df['summary'] = df['summary'].astype('string')
df['type'] = df['type'].astype('object')  
df['latitude'] = df['latitude'].astype(float) 
df['longitude'] = df['longitude'].astype(float)

df['date'] = pd.to_datetime(df['date']) 
df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')

df = df[df['name']!='Sammanfattning natt']
df = df[df['name']!='Sammanfattning kväll och natt']
df = df[df['name']!='Övrigt']
# Loading data



# Load credentials
credentials = service_account.Credentials.from_service_account_file(
    "C:\\Users\\lalka\\OneDrive\\Skrivbord\\Studier\\Projekt\\crime-in-sweden-project-811e550bf4e4.json"
) # Chage to your own path to JSON key

# Set up BigQuery Client with credentials
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Define BigQuery dataset and table name
project_id = "crime-in-sweden-project"  
dataset_id = "Crime_in_Sweden"
table_id = f"{project_id}.{dataset_id}.events" 

# Create the dataset if it does not exist
try:
    client.get_dataset(dataset_id)  # Check if dataset exists
except Exception as e:
    # If dataset does not exist, create it
    dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
    client.create_dataset(dataset)  # This creates the dataset
    print(f"Dataset {dataset_id} created.")

# Upload DataFrame to BigQuery
job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)

# Load data to BigQuery
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)

# Wait for the job to complete
job.result()

print(f"Data loaded successfully to {table_id}")

