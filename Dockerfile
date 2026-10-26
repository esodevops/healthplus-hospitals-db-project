FROM apache/airflow:3.3.0-python3.12

# Keep Airflow at the same version while adding the project's runtime packages.
RUN pip install --no-cache-dir "apache-airflow==3.3.0" pandas psycopg2-binary sqlalchemy python-dotenv certifi apache-airflow-providers-standard apache-airflow-providers-smtp --constraint "${HOME}/constraints.txt"
