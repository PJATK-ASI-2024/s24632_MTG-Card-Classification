from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import json
import ijson
import requests
import pandas as pd
from sklearn.model_selection import train_test_split
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import time

# ładowanie ścieżek do plików
from config import (
    DATA_DIR_PATH,
    BULK_DATA_PATH,
    TYPES_DICT_PATH,
    GOOGLE_SHEETS_CREDENTIALS, 
    GOOGLE_SHEETS_NAME,
    GOOGLE_SHEETS_MODEL_SHEET,
    GOOGLE_SHEETS_TRAIN_SHEET
)

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default arguments dla DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['your_email@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definicja DAG
dag = DAG(
    'pobranie_podzial_danych_debug',
    default_args=default_args,
    description='DAG do pobrania i podziału danych z logowaniem i debugowaniem',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

def debug_wrapper(func):
    """Dekorator dodający debugowanie dla funkcji."""
    def wrapper(*args, **kwargs):
        logger.debug(f"Rozpoczęcie funkcji: {func.__name__}")
        logger.debug(f"Argumenty: {args}")
        logger.debug(f"Słownik argumentów: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Zakończenie funkcji: {func.__name__} z wynikiem: {result}")
            return result
        except Exception as e:
            logger.error(f"Błąd w funkcji {func.__name__}: {e}")
            raise
    return wrapper

@debug_wrapper
def download_bulk_data(**kwargs):
    logger.info("Rozpoczęcie pobierania danych bulk.")
    bulk_data_url = "https://api.scryfall.com/bulk-data"
    try:
        response = requests.get(bulk_data_url)
        response.raise_for_status()
        logger.info("Dane bulk pobrane pomyślnie.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd podczas pobierania danych bulk: {e}")
        raise

    bulk_data = response.json()
    default_cards_entry = next((entry for entry in bulk_data.get('data', []) if entry.get('type') == 'default_cards'), None)

    if not default_cards_entry:
        logger.error("Nie znaleziono 'default_cards' w danych bulk.")
        raise Exception("Nie znaleziono 'default_cards' w danych bulk.")

    download_uri = default_cards_entry.get('download_uri')
    if not download_uri:
        logger.error("Nie znaleziono 'download_uri' dla 'default_cards'.")
        raise Exception("Nie znaleziono 'download_uri' dla 'default_cards'.")

    try:
        download_response = requests.get(download_uri, stream=True)
        download_response.raise_for_status()
        logger.info("'default_cards' pobrane pomyślnie.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd podczas pobierania 'default_cards': {e}")
        raise

    with open(BULK_DATA_PATH, 'wb') as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info(f"'default_cards' zapisane do {BULK_DATA_PATH}")

@debug_wrapper
def download_types(**kwargs):
    logger.info("Rozpoczęcie pobierania typów MTG.")
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
            logger.info(f"Pobrano dane dla: {key}")
            if key == 'supertypes' or key == 'types':
                mtg_types[key] = data.get('data', [])
            else:
                category_key = key.replace('-types', '').capitalize()
                if category_key == 'Spell':
                    mtg_types['subtypes']['Instant'] = data.get('data', [])
                    logger.info("Dodano podtypy dla 'Instant'.")
                    mtg_types['subtypes']['Sorcery'] = data.get('data', [])
                    logger.info("Dodano podtypy dla 'Sorcery'.")
                else:
                    mtg_types['subtypes'][category_key] = data.get('data', [])
                    logger.info(f"Dodano podtypy dla '{category_key}'.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Błąd podczas pobierania {key}: {e}")
            raise Exception(f"Błąd podczas pobierania {key}: {e}")

    with open(TYPES_DICT_PATH, 'w', encoding='utf-8') as f:
        json.dump(mtg_types, f, ensure_ascii=False, indent=2)
    logger.info(f"Typy MTG zapisane do {TYPES_DICT_PATH}")

@debug_wrapper
def split_data(**kwargs):
    logger.info("Rozpoczęcie podziału danych.")
    chunk_size = 10000
    selected_columns = ["name", "type_line", "oracle_text", "cmc", "colors", "set", "collector_number", "rarity", "image_uris"]

    train_path = os.path.join(DATA_DIR_PATH, "train.csv")
    test_path = os.path.join(DATA_DIR_PATH, "test.csv")

    try:
        with open(BULK_DATA_PATH, 'r', encoding='utf-8') as f:
            objects = ijson.items(f, 'item')
            data = []

            for obj in objects:
                row = {key: obj.get(key, None) for key in selected_columns}
                data.append(row)

            df = pd.DataFrame(data)

            # Podział na zbiory treningowe i testowe
            train_df, test_df = train_test_split(df, test_size=0.3, random_state=42)

            # Zapis do plików CSV
            train_df.to_csv(train_path, index=False)
            test_df.to_csv(test_path, index=False)

        logger.info(f"Zapisano dane treningowe do {train_path}")
        logger.info(f"Zapisano dane testowe do {test_path}")

        kwargs['ti'].xcom_push(key='train_data_path', value=train_path)
        kwargs['ti'].xcom_push(key='test_data_path', value=test_path)

    except Exception as e:
        logger.error(f"Błąd podczas podziału danych: {e}")
        raise

@debug_wrapper
def save_to_google_sheets(**kwargs):
    logger.info("Rozpoczęcie zapisu danych do Google Sheets.")
    ti = kwargs['ti']
    train_data_path = ti.xcom_pull(key='train_data_path', task_ids='split_data')
    test_data_path = ti.xcom_pull(key='test_data_path', task_ids='split_data')

    if not train_data_path or not test_data_path:
        logger.error("Nie znaleziono ścieżek do danych w XCom.")
        raise ValueError("Brak danych do zapisania.")

    try:
        train_df = pd.read_csv(train_data_path)
        test_df = pd.read_csv(test_data_path)
    except Exception as e:
        logger.error(f"Błąd podczas wczytywania danych z plików: {e}")
        raise

    def clean_df(df):
        return df.replace([float('inf'), float('-inf'), pd.NA], None).fillna('')

    train_df = clean_df(train_df)
    test_df = clean_df(test_df)

    try:
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)

        sh = client.open(GOOGLE_SHEETS_NAME)
    except Exception as e:
        logger.error(f"Błąd autoryzacji Google Sheets: {e}")
        raise

    datasets = {
        GOOGLE_SHEETS_MODEL_SHEET: train_df,
        GOOGLE_SHEETS_TRAIN_SHEET: test_df
    }

    for sheet_name, df in datasets.items():
        try:
            if sheet_name not in [ws.title for ws in sh.worksheets()]:
                sh.add_worksheet(title=sheet_name, rows="100", cols="20")

            sheet = sh.worksheet(sheet_name)
            sheet.clear()

            for i in range(0, len(df), 1000):  # Batch upload co 1000 wierszy
                sheet.append_rows(df.iloc[i:i+1000].values.tolist(), value_input_option='USER_ENTERED')
                logger.info(f"Zapisano batch {i//1000 + 1} do arkusza {sheet_name}")
                time.sleep(1)  # Dodanie przerwy 1 sekundy po każdym batchu, aby uniknąć przekroczenia limitu

        except Exception as e:
            logger.error(f"Błąd podczas zapisu do arkusza {sheet_name}: {e}")
            raise

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

# Kolejność zadań
download_bulk_data_task >> download_types_task >> split_data_task >> save_to_google_sheets_task