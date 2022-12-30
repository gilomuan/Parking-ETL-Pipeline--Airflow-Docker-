# **Parking ETL Pipeline (Airflow/Docker)**
## **Gabriel Ilomuanya**
##### Data Engineer | Software Engineer
##### BS. Computer Science (Villanova University, May 2022)


##
## **Overview**
Simulates the ETL (Extract, Transform, and Load) processes of customer parking data. Data is requested from an API connection made in Airflow, and stored in XCOM as JSON format. This JSON data is retrieved from XCOM and transformed accordingly to the requested schema using Pandas DataFrame. This DataFrame is stored as a CSV and loaded into PostgreSQL database.

This code was implemented for a parking company located in Long Branch NJ, using their servers and data. However, this demo is created to demonstrate such a pipeline, so to maintain the confidentiality of the company's information, Airflow will be run in Docker for the demo, and an open source API of similar parking information will be used as the dataset. 

The DAG file for the python script can be found in /DAGS/parking_dag.py .

## **DEMO** (DOCKER SIMULATION)

### Dataset

The Dataset used to simulate this process is Metered Parking Transactions from Arlington, Virginia. It contains all the relevant fields for a parking company such as payment type, price per hour, total paid, etc. The dataset was obtained from the following API:

https://datahub-v2.arlingtonva.us/api/ParkingMeter/ParkingTransactions

This is what it looked like: 

![image](https://user-images.githubusercontent.com/55989986/209993277-94cf7273-0f7a-4ac4-817c-ef2552a7e7c8.png)

### Connections/Variables

The DAGs written in parking_dag.py require connections to the API and Postgres Server (in this case, postgres is being run through CeleryExecutor on a Docker Container). Connections have to be specified in airflow in order to run these DAGs successfully: 

![image](https://user-images.githubusercontent.com/55989986/209994275-bcaa9571-b1dd-49ec-899c-ed7ecc682ed3.png)

The file path for the CSV containing the pandas dataframe is stored as a variable in Airflow for later retrieval during the load process (for the purpose of this simulation, we will create a temporary folder in the project directory):

![image](https://user-images.githubusercontent.com/55989986/209995383-3c088849-bb24-4588-b90f-306cc85fa798.png)

### Pipeline

The graph view of the pipeline shows the tasks and their dependencies:

![image](https://user-images.githubusercontent.com/55989986/210085790-79b3397d-816d-4930-ab17-27e9a2715762.png)

The tasks are scheduled to run every 2 minutes, meaning the latest data is exctracted, transformed, and loaded into the postgres database within each occurence of that interval. Here is a quick breakdown of each task and what it does:

* is_api_available - Creates a connection to the API and checks if it accepts requests.
* create_table - Creates a table in the postgres container in Airflow for parking_data with relevant fields.
* extract_user - Requests to pull 50 records of the data from the API and stores it in XCOM for retrieval in the transform task.
* transform_data - Pulls data from XCOM, appends it into a transformed Pandas DataFrame and stores it as a CSV file.
* load_data - Loads data from the CSV file into the postgres server and parking_data database that was created.

Here is the pipeline running every 2 minutes successfully: 

![image](https://user-images.githubusercontent.com/55989986/210086771-f09dbe4b-25c3-41a0-9924-7121648e828b.png)

### PostgreSQL 

We can query the created database from inside the docker container or can open the postgres UI hosted by Docker, which makes for an easier and more eye-pleasing experience. To use the postgres UI, we have to sign in to postgres, for the purposes of this demo, the username was left as admin@admin.com and the password "root". We also have to create a connection to this server, which is implemented using a postgres hook in the python dag script during the load process. Furthermore, the connection has to be specified in Postgres to retrieve the database. In this demo, the IP address is of the docker container runnning Postgres, which can be found by running " # Hostname -I " in the command line of the container. Here is how I setup the database server:

![image](https://user-images.githubusercontent.com/55989986/210087617-a7742f3c-cef6-448a-9a86-a7625287eb40.png)

The parking_data database can now be found in Postgres and queried accordingly:

![image](https://user-images.githubusercontent.com/55989986/210087812-0daf6824-48fc-461a-acf6-cec3afe9ab6a.png)





