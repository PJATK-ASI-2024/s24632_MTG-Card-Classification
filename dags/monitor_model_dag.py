import os
import subprocess
import logging
from datetime import datetime

import pandas as pd
import joblib
import pytest

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowSkipException
from airflow.utils.email import send_email_smtp

# ----------------------------------------------------------------
# 1. Konfiguracja podstawowa DAG-a
# ----------------------------------------------------------------

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,  
    "email_on_retry": False,
    "retries": 0,
}

with DAG(
    dag_id="model_validation_and_monitoring",
    default_args=default_args,
    description="DAG sprawdzający jakość modelu i uruchamiający testy jednostkowe z powiadomieniem e-mail.",
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["monitoring", "model", "validation"],
) as dag:

    # ----------------------------------------------------------------
    # 2. Funkcje pomocnicze
    # ----------------------------------------------------------------

    def load_model_and_evaluate(**context):
        """
        Ładuje model z pliku .joblib i nowy zbiór testowy z CSV.
        Wylicza accuracy i ewentualnie inne metryki.
        Zwraca accuracy i ewentualne dodatkowe dane w XCom.
        """

        # Ścieżki do plików:
        model_path = os.path.join(
            os.getenv("MODELS_DIR_PATH", "models"), 
            "random_forest_model.joblib"  
        )
        test_data_path = os.getenv("TEST_DATASET_PATH", "datasets/test_df.csv")

        logging.info(f"Model path: {model_path}")
        logging.info(f"Test data path: {test_data_path}")

        # Załaduj model
        try:
            model = joblib.load(model_path)
            logging.info("Model wczytany poprawnie.")
        except Exception as e:
            logging.error(f"Nie udało się wczytać modelu: {e}")
            # Jeśli modelu nie ma lub jest uszkodzony, rzucamy wyjątek
            raise ValueError("Brak modelu lub uszkodzony plik modelu (.joblib).")

        # Załaduj dane testowe
        if not os.path.isfile(test_data_path):
            raise FileNotFoundError(f"Brak pliku z danymi testowymi: {test_data_path}")

        df_test = pd.read_csv(test_data_path)
        logging.info(f"Wczytano zbiór testowy o rozmiarze: {df_test.shape}")

        target_variable = 'rarity_numeric'
        features = df_test.drop(columns=['image_path', target_variable, 'collector_number', 'subtypes']).columns.tolist()
        
        X = df_test[features]
        y = df_test[target_variable]

        # Predykcja
        y_pred = model.predict(X)

        # Prosta metryka accuracy
        accuracy = (y_pred == y).mean()

        logging.info(f"Obliczone accuracy: {accuracy:.4f}")

        # Zapisujemy accuracy w XCom, żeby użyć w kolejnym tasku
        context["ti"].xcom_push(key="accuracy", value=accuracy)

    def run_pytest(**context):
        """
        Uruchamia testy jednostkowe za pomocą pytest i zwraca w XCom:
        - status: "PASSED" lub "FAILED"
        - logs: pełny log z wykonania testów
        """
        # Można trzymać testy w katalogu `tests/`
        # Poniżej przykład uruchomienia w podkatalogu `tests/`:
        command = ["pytest", "tests/", "--maxfail=1", "--disable-warnings", "-q"]
        
        try:
            # Uruchom pytest jako subprocess i przechwyć wyjście (stdout + stderr)
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False  # nie rzucaj wyjątku na kodzie != 0
            )
            
            # Zwracamy logi i status w XCom
            test_logs = result.stdout + "\n" + result.stderr

            if result.returncode == 0:
                test_status = "PASSED"
            else:
                test_status = "FAILED"
            
            logging.info(f"Test status: {test_status}")
            logging.info(f"Test logs:\n{test_logs}")

            context["ti"].xcom_push(key="test_status", value=test_status)
            context["ti"].xcom_push(key="test_logs", value=test_logs)
        
        except Exception as e:
            # Jeśli coś poszło wyjątkowo źle, rzucamy błąd
            raise RuntimeError(f"Uruchomienie testów się nie powiodło: {e}")

    def check_results_and_send_email(**context):
        """
        Sprawdza accuracy z poprzedniego taska i status testów. 
        Jeżeli accuracy < 0.65 LUB testy = FAILED, wysyła powiadomienie mailowe.
        """
        accuracy = context["ti"].xcom_pull(key="accuracy", task_ids="evaluate_model")
        test_status = context["ti"].xcom_pull(key="test_status", task_ids="run_tests")
        test_logs = context["ti"].xcom_pull(key="test_logs", task_ids="run_tests")

        # Na wypadek, gdyby któryś z XCom był None
        if accuracy is None:
            accuracy = -999  # sygnalizuj, że coś poszło nie tak
        if not test_status:
            test_status = "FAILED"
            test_logs = "Brak logów - testy nie zostały uruchomione lub zadanie padło."

        # Progi i warunki
        CRITICAL_THRESHOLD = 0.65
        is_below_threshold = (accuracy < CRITICAL_THRESHOLD)
        tests_failed = (test_status == "FAILED")

        # Jeśli wszystko jest OK, pomijamy wysyłkę maila
        if (not is_below_threshold) and (not tests_failed):
            logging.info(
                f"Accuracy {accuracy:.4f} >= {CRITICAL_THRESHOLD}, "
                "i testy zakończyły się sukcesem. Mail nie zostanie wysłany."
            )
            raise AirflowSkipException("Nie ma potrzeby wysyłać powiadomienia.")

        # W przeciwnym razie – przygotowujemy treść maila i wysyłamy
        subject = "[ALERT] Walidacja modelu nie powiodła się"
        
        body = (
            f"<h3>Uwaga! Model nie spełnił kryteriów jakości lub testy padły.</h3>\n"
            f"<p><b>Aktualne accuracy:</b> {accuracy:.4f}<br>"
            f"<b>Próg krytyczny:</b> {CRITICAL_THRESHOLD}<br>"
            f"<b>Testy jednostkowe:</b> {test_status}</p>\n"
            f"<hr>\n"
            f"<p><b>Logi testów:</b><br><pre>{test_logs}</pre></p>"
        )

        # send_email_smtp(to, subject, html_content, files=None, cc=None, bcc=None, mime_subtype='mixed', mime_charset='utf-8')
        # Możesz wstawić tu listę odbiorców w zależności od potrzeb
        send_email_smtp(
            to=["s24632@pjwstk.edu.pl"],  
            subject=subject,
            html_content=body,
        )

        logging.info("Wysłano alert e-mail z informacjami o niepowodzeniu.")

    # ----------------------------------------------------------------
    # 3. Definicje zadań w DAG-u
    # ----------------------------------------------------------------

    # Task 1: Załadowanie modelu + nowych danych i obliczenie accuracy
    evaluate_model = PythonOperator(
        task_id="evaluate_model",
        python_callable=load_model_and_evaluate,
    )

    # Task 2: Uruchomienie testów jednostkowych (pytest)
    run_tests = PythonOperator(
        task_id="run_tests",
        python_callable=run_pytest,
    )

    # Task 3: Sprawdzenie wyników i (opcjonalna) wysyłka maila
    # Ten task będzie zawsze wywołany, nawet gdy poprzednie się sypną – 
    # w standardowym przepływie, jeśli task "evaluate_model" lub "run_tests" 
    # się nie uda, DAG się zatrzyma. 
    # Aby wykonać "check_results_and_send_email" pomimo faila, 
    # można użyć trigger_rule="all_done", jednak wówczas 
    # musimy mieć xcom'y i logi z poprzednich zadań. 
    # Najczęściej wygodniej jest, by ten task wykonał się tylko, 
    # jeśli poprzednie taski się powiodły (bo w razie realnego faila 
    # nie dojdziemy do sprawdzenia i tak).
    check_results = PythonOperator(
        task_id="check_results_and_send_email",
        python_callable=check_results_and_send_email,
        trigger_rule="all_success",  # uruchamiaj się tylko, jeśli oba poprzednie się powiodły
    )

    # Ustawienie kolejności w DAG-u:
    [evaluate_model, run_tests] >> check_results
