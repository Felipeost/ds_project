# Project Title: Event and Weather in Sweden

## Description
This project analyzes and visualizes events in Sweden reported by the Police and shows weather and driving conditions on Swedish roads. It fetches data from the Police API and SMHI API, processes it, and presents it using Streamlit for web-based interaction. The project includes features for filtering events by category and location and provides visualizations on maps.

## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

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




    
