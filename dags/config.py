import os
from dotenv import load_dotenv

# 1. Wczytanie zmiennych z pliku .env
load_dotenv()

# 2. Zdefiniowanie ścieżek i innych zmiennych
AIRFLOW_IMAGE_NAME = os.getenv("AIRFLOW_IMAGE_NAME", "apache/airflow:2.5.1")
AIRFLOW_UID = os.getenv("AIRFLOW_UID", "50000")

GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "asilaby-ed62c735371a.json")
GOOGLE_SHEETS_NAME = os.getenv("GOOGLE_SHEETS_NAME", "df")
GOOGLE_SHEETS_MODEL_SHEET = os.getenv("GOOGLE_SHEETS_MODEL_SHEET", "test_df")
GOOGLE_SHEETS_TRAIN_SHEET = os.getenv("GOOGLE_SHEETS_TRAIN_SHEET", "train_df")
GOOGLE_SHEETS_PROCESSED_SHEET = os.getenv("GOOGLE_SHEETS_PROCESSED_SHEET", "processed_df")
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL", "klucz-api@asilaby.iam.gserviceaccount.com")

BULK_DATA_PATH = os.getenv("BULK_DATA_PATH", "data/default-cards.json")
TYPES_DICT_PATH = os.getenv("TYPES_DICT_PATH", "data/mtg_types.json")

RAW_DATASET_PATH = os.getenv("RAW_DATASET_PATH", "datasets/cards_metadata.csv")
PROCESSED_DATASET_PATH = os.getenv("PROCESSED_DATASET_PATH", "datasets/processed_data.csv")
TEST_DATASET_PATH = os.getenv("TEST_DATASET_PATH", "datasets/test_df.csv")
TRAIN_DATASET_PATH = os.getenv("TRAIN_DATASET_PATH", "datasets/train_data.csv")

COLOR_DICTIONARY_PATH = os.getenv("COLOR_DICTIONARY_PATH", "dictionaries/colors_code_mapping.txt")

DOWNLOAD_LOGS_PATH = os.getenv("DOWNLOAD_LOGS_PATH", "logs/download_cards.log")
PROCESSED_LOG_PATH = os.getenv("PROCESSED_LOG_PATH", "logs/process_cards.log")
EDA_REPORT_PATH = os.getenv("EDA_REPORT_PATH", "reports/report_eda.html")
DOWLOAD_CARDS_REPORT_PATH = os.getenv("DOWLOAD_CARDS_REPORT_PATH", "reports/raport.txt")

DATA_ANALYSIS_SCRIPT_PATH = os.getenv("DATA_ANALYSIS_SCRIPT_PATH", "scripts/data_analysis.py")
DOWNLOAD_BULK_DATA_SCRIPT_PATH = os.getenv("DOWNLOAD_BULK_DATA_SCRIPT_PATH", "scripts/download_bulk_data.py")
DOWNLOAD_IMAGES_SCRIPT_PATH = os.getenv("DOWNLOAD_IMAGES_SCRIPT_PATH", "scripts/download_card_images.py")
DOWNLOAD_TYPES_SCRIPT_PATH = os.getenv("DOWNLOAD_TYPES_SCRIPT_PATH", "scripts/download_types.py")
CREATE_DATASET_SCRIPT_PATH = os.getenv("CREATE_DATASET_SCRIPT_PATH", "scripts/make_metadata_csv.py")

CARDS_DIR_PATH = os.getenv("CARDS_DIR_PATH", "cards")
DATA_DIR_PATH = os.getenv("DATA_DIR_PATH", "data")
DATASETS_DIR_PATH = os.getenv("DATASETS_DIR_PATH", "datasets")
DICTIONARIES_DIR_PATH = os.getenv("DICTIONARIES_DIR_PATH", "dictionaries")
LOGS_DIR_PATH = os.getenv("LOGS_DIR_PATH", "logs")
NOTEBOOKS_DIR_PATH = os.getenv("NOTEBOOKS_DIR_PATH", "notebooks")
REPORTS_DIR_PATH = os.getenv("REPORTS_DIR_PATH", "reports")
SCRIPTS_DIR_PATH = os.getenv("SCRIPTS_DIR_PATH", "scripts")
MODELS_DIR_PATH = os.getenv("MODELS_DIR_PATH", "models")
VISUALIZATIONS_DIR_PATH = os.getenv("VISUALIZATIONS_DIR_PATH", "visualizations")