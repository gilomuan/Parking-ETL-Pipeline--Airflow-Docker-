#!/usr/bin/env python
"""Sample ETL Pipeline DAG script for Parking Company.

Simulates Extract, Transform, and Load processes of customer parking data.
Data is requested from API connection made in Airflow and stored in XCOM in JSON format.
JSON data is retrieved from XCOM and transformed accordingly using Pandas DataFrame.
This DataFrame is stored as a csv and loaded into PostgreSQL database.
"""

import os
from airflow import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.bash import BashOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests
import json
import pandas as pd
from datetime import datetime, date, timedelta

__author__ = "Gabriel Ilomuanya"
__date__ = "December 2022"

# Grab current date
current_date = datetime.today().strftime('%Y-%m-%d')

# Default settings for all the dags in the pipeline
default_args = {

    "owner": "Airflow", 
    "start_date" : datetime(2022,8,1),
    "retries" : 1,
    "retry_delay": timedelta(minutes=5)

}

def _transform_parking_data(ti):
    """
    Transforms the parking data into a csv file that can be loaded into postgres 
    """
    parking_data = ti.xcom_pull(task_ids =['extract_user']) # Extract the json object from XCom

    if not parking_data:
        raise Exception('No processed parking data.') # Check if parking_data is empty

    # Convert the parking data into a pandas dataframe
    data = json.dumps(parking_data[0])
    jsonDict = json.loads(data)
    df = pd.json_normalize(jsonDict)
    df = df.set_index('parkingTransactionKey') # Index becomes transaction key

    # Check if file has been created already and upsert accordingly
    csv_path = Variable.get('parking_data_csv_path') # Path is retrieved from variable created in Airflow
    if os.path.exists(csv_path):
        df_header = False
        df_mode = 'a'
    else:
        os.mkdir(csv_path)
        df_header = True
        df_mode = 'w'
    filename = os.path.join(csv_path,"processed_parking_data_00.csv")

    # Drop irrelevant columns 
    df = df.drop(['transactionSourceCode', 'meterId', 'zoneNbr','meterManufacturerName', 'blockNbr', 'sourceStreetDisplayName',
       'sideDirectionName', 'latitudeCrd', 'longitudeCrd', 'statePlaneXCrd',
       'statePlaneYCrd', 'handicapInd','timeRestrictionDsc', 'zoneSpaceCnt'],axis=1)
    
    # Store Parking Data in CSV format
    df.to_csv(filename, index=False, mode=df_mode, header=df_header)

def _load_parking_data():
    '''
    This function uses the Postgres Hook to copy users from processed_data.csv
    and into the table
    
    '''
    # Connect to the Postgres connection
    hook = PostgresHook(postgres_conn_id = 'postgres')

    # Retrieve csv path from airflow variable 
    csv_path = Variable.get('parking_data_csv_path')
    filename = os.path.join(csv_path,"processed_parking_data_00.csv")
    # Insert the data from the CSV file into the postgres database
    hook.copy_expert(
        sql = "COPY parking_data FROM stdin WITH DELIMITER as ','",
        filename=filename
    )

with DAG('parking_pipeline', default_args=default_args, schedule_interval=timedelta(minutes=2), catchup=False) as dag:


    # Dag #1 - Check if the API is available
    is_api_available = HttpSensor(
        task_id='is_api_available',
        method='GET',
        http_conn_id='is_api_available',
        endpoint= '',
    )

    # Dag #2 - Create a table
    create_table = PostgresOperator(
        task_id = 'create_table',
        postgres_conn_id='postgres',
        sql='''
            drop table if exists parking_data;
            create table parking_data(
                startDtm text not null,
                endDtm text not null,
                transactionAmt text not null,
                paymentTypeName text not null,
                transactionStatusCode text not null,
                maxHoursCnt text not null,
                meterTypeDsc text not null,
                dollarPerHourRate text not null,
                activeStatusInd text not null,
                metroAreaName text not null
            );
        '''
    )

    # DAG #3 - Extract Data
    extract_data = SimpleHttpOperator(
            task_id = 'extract_user',
            http_conn_id='is_api_available',
            method='GET',
            endpoint= '?$top=50', # Limit to 50 records per request
            response_filter=lambda response: json.loads(response.text),
            log_response=True
    )

    # Dag #4 - Process data
    transform_data = PythonOperator(
        task_id = 'transform_data',
        python_callable=_transform_parking_data

    )

    # Dag #5 - Load data
    load_data = PythonOperator(
        task_id = 'load_data',
        python_callable=_load_parking_data

    )

    # Dependencies
    is_api_available >> create_table >> extract_data >> transform_data >> load_data
