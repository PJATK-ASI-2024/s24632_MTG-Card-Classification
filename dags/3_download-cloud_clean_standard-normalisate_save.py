from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import logging
import time


# ładowanie ścieżek do plików
from config import (
    GOOGLE_SHEETS_CREDENTIALS, 
    GOOGLE_SHEETS_NAME,
    GOOGLE_SHEETS_MODEL_SHEET,
    GOOGLE_SHEETS_PROCESSED_SHEET
)

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default arguments dla DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['your_email@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definicja DAG
dag = DAG(
    'przetwarzanie_danych',
    default_args=default_args,
    description='DAG do przetwarzania danych',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 2),
    catchup=False,
)

def fetch_data_from_google_sheets(**kwargs):
    # Autoryzacja z Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
    client = gspread.authorize(creds)

    # Otwórz arkusz Google Sheets
    sh = client.open(GOOGLE_SHEETS_NAME)

    # Pobierz dane z arkusza "Zbior modelowy"
    try:
        model_sheet = sh.worksheet(GOOGLE_SHEETS_MODEL_SHEET)
    except gspread.WorksheetNotFound:
        raise Exception(f"Worksheet {GOOGLE_SHEETS_MODEL_SHEET} not found in {GOOGLE_SHEETS_NAME}")

    # Pobieranie danych w batch'ach
    batch_size = 1000  
    total_rows = model_sheet.row_count
    num_batches = -(-total_rows // batch_size)  # Zaokrąglenie w górę do najbliższej liczby całkowitej
    data = []
    for i in range(num_batches):
        start_row = i * batch_size + 1
        end_row = min((i + 1) * batch_size, total_rows)
        batch_data = model_sheet.get(f'A{start_row}:Z{end_row}')
        data.extend(batch_data)
        time.sleep(1)
        logger.info(f"Pobrano batch {i+1}/{num_batches} z arkusza {GOOGLE_SHEETS_MODEL_SHEET}")

    # Utworzenie DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])

    # Przechowaj DataFrame w XCom jako JSON
    kwargs['ti'].xcom_push(key='raw_data', value=df.to_json())
    
    # Przechowaj DataFrame w XCom jako JSON
    kwargs['ti'].xcom_push(key='raw_data', value=df.to_json())
    
    return

def clean_data(**kwargs):
    ti = kwargs['ti']
    raw_json = ti.xcom_pull(key='raw_data', task_ids='fetch_data_from_google_sheets')
    df = pd.read_json(raw_json)
    
    # Usuwanie brakujących wartości
    df = df.dropna()
    
    # Usuwanie duplikatów
    df = df.drop_duplicates()
    
    # Przechowaj oczyszczone dane w XCom
    ti.xcom_push(key='clean_data', value=df.to_json())

def standardize_and_normalize(**kwargs):
    ti = kwargs['ti']
    clean_json = ti.xcom_pull(key='clean_data', task_ids='clean_data')
    df = pd.read_json(clean_json)
    
    # Wybierz kolumny numeryczne do skalowania
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    
    normalizer = MinMaxScaler()
    df[numeric_cols] = normalizer.fit_transform(df[numeric_cols])
    
    # Przechowaj przetworzone dane w XCom
    ti.xcom_push(key='processed_data', value=df.to_json())

def save_processed_data_to_google_sheets(**kwargs):
    ti = kwargs['ti']
    processed_json = ti.xcom_pull(key='processed_data', task_ids='standardize_and_normalize')
    df = pd.read_json(processed_json)
    
    # Autoryzacja z Google Sheets
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
    client = gspread.authorize(creds)
    
    # Otwórz arkusz Google Sheets
    sh = client.open(GOOGLE_SHEETS_NAME)
    
    # Zapisz dane do arkusza "Przetworzone dane"
    try:
        processed_sheet = sh.worksheet(GOOGLE_SHEETS_PROCESSED_SHEET)
    except gspread.WorksheetNotFound:
        processed_sheet = sh.add_worksheet(title=GOOGLE_SHEETS_PROCESSED_SHEET, rows="1000", cols="20")
    
    processed_sheet.clear()
    processed_sheet.update([df.columns.values.tolist()] + df.values.tolist())
    
    print("Przetworzone dane zostały zapisane do Google Sheets")

# Definicja zadań
fetch_data_task = PythonOperator(
    task_id='fetch_data_from_google_sheets',
    python_callable=fetch_data_from_google_sheets,
    provide_context=True,
    dag=dag,
)

clean_data_task = PythonOperator(
    task_id='clean_data',
    python_callable=clean_data,
    provide_context=True,
    dag=dag,
)

standardize_normalize_task = PythonOperator(
    task_id='standardize_and_normalize',
    python_callable=standardize_and_normalize,
    provide_context=True,
    dag=dag,
)

save_processed_data_task = PythonOperator(
    task_id='save_processed_data_to_google_sheets',
    python_callable=save_processed_data_to_google_sheets,
    provide_context=True,
    dag=dag,
)

# Ustalanie kolejności zadań
fetch_data_task >> clean_data_task >> standardize_normalize_task >> save_processed_data_task
