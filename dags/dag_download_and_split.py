from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import json
import requests
from dotenv import load_dotenv
import pandas as pd
from sklearn.model_selection import train_test_split
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Załaduj zmienne z pliku .env
load_dotenv()

# Pobierz zmienne środowiskowe
DATA_DIR_PATH = os.getenv("DATA_DIR_PATH")
BULK_DATA_PATH = os.getenv("BULK_DATA_PATH")
TYPES_DICT_PATH = os.getenv("TYPES_DICT_PATH")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
GOOGLE_SHEETS_NAME = os.getenv("GOOGLE_SHEETS_NAME")
GOOGLE_SHEETS_MODEL_SHEET = os.getenv("GOOGLE_SHEETS_MODEL_SHEET")
GOOGLE_SHEETS_TRAIN_SHEET = os.getenv("GOOGLE_SHEETS_TRAIN_SHEET")

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
    'pobranie_podzial_danych',
    default_args=default_args,
    description='DAG do pobrania i podziału danych',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

def download_bulk_data(**kwargs):
    bulk_data_url = "https://api.scryfall.com/bulk-data"
    try:
        response = requests.get(bulk_data_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching bulk data: {e}")
    
    bulk_data = response.json()
    default_cards_entry = next((entry for entry in bulk_data.get('data', []) if entry.get('type') == 'default_cards'), None)
    
    if not default_cards_entry:
        raise Exception("default_cards not found in bulk data")
    
    download_uri = default_cards_entry.get('download_uri')
    if not download_uri:
        raise Exception("download_uri for default_cards not found")
    
    try:
        download_response = requests.get(download_uri, stream=True)
        download_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading default_cards: {e}")
    
    with open(BULK_DATA_PATH, 'wb') as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"default_cards downloaded and saved to {BULK_DATA_PATH}")

def download_types(**kwargs):
    endpoints = {
        'supertypes': 'https://api.scryfall.com/catalog/supertypes',
        'types': 'https://api.scryfall.com/catalog/card-types',
        'artifact-types': 'https://api.scryfall.com/catalog/artifact-types',
        'battle-types': 'https://api.scryfall.com/catalog/battle-types',
        'creature-types': 'https://api.scryfall.com/catalog/creature-types',
        'enchantment-types': 'https://api.scryfall.com/catalog/enchantment-types',
        'land-types': 'https://api.scryfall.com/catalog/land-types',
        'planeswalker-types': 'https://api.scryfall.com/catalog/planeswalker-types',
        'spell-types': 'https://api.scryfall.com/catalog/spell-types'
    }

    mtg_types = {
        'supertypes': [],
        'types': [],
        'subtypes': {}
    }

    for key, url in endpoints.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if key == 'supertypes' or key == 'types':
                mtg_types[key] = data.get('data', [])
            else:
                category_key = key.replace('-types', '').capitalize()
                if category_key == 'Spell':
                    mtg_types['subtypes']['Instant'] = data.get('data', [])
                    mtg_types['subtypes']['Sorcery'] = data.get('data', [])
                else:
                    mtg_types['subtypes'][category_key] = data.get('data', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching {key}: {e}")

    with open(TYPES_DICT_PATH, 'w', encoding='utf-8') as f:
        json.dump(mtg_types, f, ensure_ascii=False, indent=2)
    print(f"MTG types downloaded and saved to {TYPES_DICT_PATH}")

def split_data(**kwargs):
    # Wczytaj bulk data
    with open(BULK_DATA_PATH, 'r', encoding='utf-8') as f:
        bulk_data = json.load(f)
    
    # Przekształć dane na DataFrame
    df = pd.DataFrame(bulk_data)
    
    # Podział danych
    train_df, test_df = train_test_split(df, test_size=0.3, random_state=42)
    
    # Przechowaj DataFrame w XCom jako JSON
    kwargs['ti'].xcom_push(key='train_data', value=train_df.to_json())
    kwargs['ti'].xcom_push(key='test_data', value=test_df.to_json())

def save_to_google_sheets(**kwargs):
    # Pobierz dane z XCom
    ti = kwargs['ti']
    train_json = ti.xcom_pull(key='train_data', task_ids='split_data')
    test_json = ti.xcom_pull(key='test_data', task_ids='split_data')
    
    train_df = pd.read_json(train_json)
    test_df = pd.read_json(test_json)
    
    # Autoryzacja z Google Sheets
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
    client = gspread.authorize(creds)
    
    # Otwórz lub utwórz arkusz Google Sheets
    try:
        sh = client.open(GOOGLE_SHEETS_NAME)
    except gspread.SpreadsheetNotFound:
        sh = client.create(GOOGLE_SHEETS_NAME)
        sh.share('your_email@example.com', perm_type='user', role='writer')  # Zastąp swoim emailem
    
    # Zapisz zbiór modelowy
    try:
        model_sheet = sh.worksheet(GOOGLE_SHEETS_MODEL_SHEET)
    except gspread.WorksheetNotFound:
        model_sheet = sh.add_worksheet(title=GOOGLE_SHEETS_MODEL_SHEET, rows="1000", cols="20")
    model_sheet.clear()
    model_sheet.update([train_df.columns.values.tolist()] + train_df.values.tolist())
    
    # Zapisz zbiór douczeniowy
    try:
        train_sheet = sh.worksheet(GOOGLE_SHEETS_TRAIN_SHEET)
    except gspread.WorksheetNotFound:
        train_sheet = sh.add_worksheet(title=GOOGLE_SHEETS_TRAIN_SHEET, rows="1000", cols="20")
    train_sheet.clear()
    train_sheet.update([test_df.columns.values.tolist()] + test_df.values.tolist())
    
    print("Dane zostały zapisane do Google Sheets")

# Definicja zadań
download_bulk_data_task = PythonOperator(
    task_id='download_bulk_data',
    python_callable=download_bulk_data,
    provide_context=True,
    dag=dag,
)

download_types_task = PythonOperator(
    task_id='download_types',
    python_callable=download_types,
    provide_context=True,
    dag=dag,
)

split_data_task = PythonOperator(
    task_id='split_data',
    python_callable=split_data,
    provide_context=True,
    dag=dag,
)

save_to_google_sheets_task = PythonOperator(
    task_id='save_to_google_sheets',
    python_callable=save_to_google_sheets,
    provide_context=True,
    dag=dag,
)

# Ustalanie kolejności zadań
download_bulk_data_task >> download_types_task >> split_data_task >> save_to_google_sheets_task
