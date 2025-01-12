# Importowanie potrzebnych bibliotek
import os
import pandas as pd
import numpy as np

from tpot import TPOTClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from dotenv import load_dotenv
from pprint import pprint

# Załadowanie zmiennych środowiskowych z pliku .env
load_dotenv()

# Ścieżki do plików z danymi
PROCESSED_DATASET_PATH = os.getenv("PROCESSED_DATASET_PATH")
MODELS_DIR_PATH = os.getenv("MODELS_DIR_PATH")

# Załadowanie danych
df = pd.read_csv(PROCESSED_DATASET_PATH)

# Definiowanie cechy celu i cech predykcyjnych
target_variable = 'rarity_numeric'
features = df.drop(columns=['image_path', target_variable, 'collector_number', 'subtypes']).columns.tolist()

X = df[features]
y = df[target_variable]

# Podział danych na zbiory treningowy i testowy
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# Inicjalizacja klasyfikatora TPOT
tpot = TPOTClassifier(
    generations=3,
    population_size=20,
    verbosity=2,
    random_state=42,
    scoring='accuracy'
)
tpot.fit(X_train, y_train)

# --------------------------------------------------------------------------
# 1. Predykcja i raport najlepszym modelem (TPOT wybiera zwycięzcę)
# --------------------------------------------------------------------------
y_pred = tpot.predict(X_test)

print("\n============================")
print("NAJLEPSZY WYBRANY PIPELINE:")
print("============================")
print(f"Classification report for the best pipeline:\n{classification_report(y_test, y_pred)}")

best_accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy (best pipeline): {best_accuracy:.4f}")

# Eksport najlepszego modelu do pliku .py
best_model_file = os.path.join(MODELS_DIR_PATH, 'tpot_best_model.py')
tpot.export(best_model_file)
print(f"[INFO] Najlepszy pipeline wyeksportowany do: {best_model_file}")

# --------------------------------------------------------------------------
# 2. Znajdź top 3 najlepsze modele w tpot.evaluated_individuals_
# --------------------------------------------------------------------------
print("\n=======================================")
print("TOP 3 PIPELINE’Y WG TPOT (internal_cv_score)")
print("=======================================")

all_models = tpot.evaluated_individuals_
if not all_models:
    print("Brak innych osobników w evaluated_individuals_.")
else:
    # Sortujemy po 'internal_cv_score' malejąco
    sorted_models = sorted(
        all_models.items(),
        key=lambda x: x[1]['internal_cv_score'],
        reverse=True
    )

    # Weź pierwsze 3
    top_3 = sorted_models[:3]

    for rank_idx, (model_name, model_info) in enumerate(top_3, start=1):
        pipeline_score = model_info['internal_cv_score']

        print(f"\n--- MODEL #{rank_idx} ---")
        print(f"Pipeline name: {model_name}")
        print(f"Internal CV score (TPOT): {pipeline_score:.4f}")

        # Bezpiecznie pobieramy ewentualny pipeline:
        pipeline_obj = model_info.get('pipeline', None)
        if pipeline_obj is None:
            print("UWAGA: Ten osobnik nie ma klucza 'pipeline'. Pomijam.")
            continue

        # Wyświetlamy kroki pipeline’u (jesli to scikit-learn Pipeline)
        if hasattr(pipeline_obj, 'steps'):
            pprint(pipeline_obj.steps)
        else:
            print("To prawdopodobnie pojedynczy model.")

        # Trenujemy ten pipeline/model na zbiorze treningowym
        temp_model = pipeline_obj.fit(X_train, y_train)
        temp_pred = temp_model.predict(X_test)

        test_acc = accuracy_score(y_test, temp_pred)
        print(f"Accuracy on TEST: {test_acc:.4f}")

        # Raport klasyfikacji
        clf_report = classification_report(y_test, temp_pred)
        print("Classification report:\n", clf_report)

        # Zapisujemy wyniki do pliku tekstowego
        report_str = f"""
=== MODEL #{rank_idx} ===
Pipeline name: {model_name}
Internal CV score (TPOT): {pipeline_score:.4f}
Accuracy (TEST): {test_acc:.4f}

Classification report:
{clf_report}
"""
        report_file = os.path.join(MODELS_DIR_PATH, f"tpot_model_{rank_idx}_report.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_str)
        print(f"[INFO] Zapisano raport: {report_file}")


