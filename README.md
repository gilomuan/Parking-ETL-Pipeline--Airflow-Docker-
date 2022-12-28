# Parking ETL Pipeline (Airflow/Docker)

Simulates Extract, Transform, and Load processes of customer parking data. Data is requested from API connection made in Airflow and stored in XCOM in JSON format.
JSON data is retrieved from XCOM and transformed accordingly using Pandas DataFrame.
This DataFrame is stored as a csv and loaded into PostgreSQL database.
