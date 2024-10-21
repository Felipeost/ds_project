# Project Title: Event and Weather in Sweden

## Description
This project analyzes and visualizes events in Sweden reported by the Police and shows weather and driving conditions on Swedish roads. It fetches data from the Police API and SMHI API, processes it, and presents it using Streamlit for web-based interaction. The project includes features for filtering events by category and location and provides visualizations on maps.

## Table of Contents
- [Structure](#structure)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Structure
```
ds_project/
│
├── .streamlit/
│   ├── config.toml               # Configuration for Streamlit (Styles)
│   └── secrets.toml (hidden)     # Sensitive information (BigQuery credentials)
│
├── pages/                        # Directory for Streamlit pages
│   ├── 2_Händelser.py            # Streamlit page for events
│   └── 3_Väder.py                # Streamlit page for weather
│
├── .gitignore                    # Specifies files and directories to ignore in version control
├── 1_intro.py                    # Main page for Streamlit application
├── comments.csv                  # CSV file for collecting user comments
├── etl_pipeline.log              # Log file for the ETL pipeline
├── etl_polis_data.py             # ETL pipeline for fetching Police API data and loading into BigQuery
├── my.bat (hidden)               # .bat file for automating pipeline execution with Windows Task Scheduler
├── requirements.txt              # Text file with required packages
└── README.md                     # Project overview, instructions, and documentation
```

## Features
- Fetches data from Police API and SMHI API
- Allows filtering by event category and location
- Visualizes events and road conditions on an interactive map
- Provides detailed information for each reported incident and information about the weather in each particular city

## Technologies Used
- Python
- Streamlit
- Pandas
- Folium
- Google Cloud BigQuery
- Git

## Installation
To get a local copy up and running, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Felipeost/ds_project.git

2. Navigate to the project directory:
   ```bash
   cd ds_project

3. (Optional) Create and activate a virtual environment (recommended):
    ```bash
    python -m venv env
    # On Windows use:
    env\Scripts\activate
    # On macOS/Linux use:
    source env/bin/activate

4. Install required packages:
   ```bash
   pip install -r requirements.txt

5. (Optional) Set up your Google Cloud credentials as per your project requirements.

## Usage

To run the application, use the following command:
    ```bash
    streamlit run Intro.py

This will start a local server, and you can access the application in your web browser at http://localhost:8501.

To run the pipeline for fetching the data from Polis API and storaging it in your BigQuery DataBase, run the file `etl_polis_data.py`




    
