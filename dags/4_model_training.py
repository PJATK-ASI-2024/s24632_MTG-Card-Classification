# model_training_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import pandas as pd
import os
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error, classification_report
import joblib

# ładowanie ścieżek do plików
from config import (
    DATASETS_DIR_PATH,
    MODELS_DIR_PATH,
    REPORTS_DIR_PATH,
)

Path(MODELS_DIR_PATH).mkdir(parents=True, exist_ok=True)
Path(REPORTS_DIR_PATH).mkdir(parents=True, exist_ok=True)

def train_model():
    """
    Trenuje model ML, ocenia jego wydajność i zapisuje model oraz raport ewaluacji.
    """
    # Wczytaj przetworzone dane
    processed_data_path = os.path.join(DATASETS_DIR_PATH, 'processed_data.csv')
    df = pd.read_csv(processed_data_path)
    
    # Definiowanie cechy celu i cech predykcyjnych
    target_variable = 'rarity_numeric'
    features = df.drop(columns=['image_path', target_variable, 'collector_number', 'subtypes']).columns.tolist()
    
    X = df[features]
    y = df[target_variable]
    
    # Podział danych na zbiór treningowy (70%) i walidacyjny (30%)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Inicjalizacja modelu Random Forest z parametrami wybranymi na podstawie AutoML
    model = RandomForestClassifier(
        bootstrap=True,
        criterion='gini',
        max_features=0.5,
        min_samples_leaf=1,
        min_samples_split=4,
        n_estimators=100,
        random_state=42
    )
    
    # Trenowanie modelu na zbiorze treningowym
    model.fit(X_train, y_train)
    
    # Przewidywanie na zbiorze walidacyjnym
    y_pred = model.predict(X_val)
    
    # Obliczenie metryk jakości
    accuracy = accuracy_score(y_val, y_pred)
    mae = mean_absolute_error(y_val, y_pred)
    report = classification_report(y_val, y_pred)
    
    # Zapisanie modelu do pliku
    model_filename = os.path.join(MODELS_DIR_PATH, 'random_forest_model.joblib')
    joblib.dump(model, model_filename)
    print(f"Model został zapisany jako {model_filename}")
    
    # Zapisanie raportu ewaluacji do pliku
    report_filename = os.path.join(REPORTS_DIR_PATH, 'evaluation_report.txt')
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("Metryki jakości prototypowego modelu:\n")
        f.write(f"Accuracy: {accuracy:.4f}\n")
        f.write(f"Mean Absolute Error (MAE): {mae:.4f}\n")
        f.write("Raport klasyfikacji:\n")
        f.write(report)
    print(f"Raport ewaluacji został zapisany jako {report_filename}")
    
    # Opcjonalnie: Wyświetlenie metryk
    print("Metryki jakości prototypowego modelu:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print("Raport klasyfikacji:")
    print(report)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    dag_id='model_training_dag',
    default_args=default_args,
    description='DAG odpowiedzialny za budowę i trenowanie modeli',
    schedule_interval=None,  # Ręczne uruchamianie
    start_date=days_ago(1),
    catchup=False,
) as dag:

    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
    )

    train_model_task
