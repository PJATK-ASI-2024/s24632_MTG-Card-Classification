# importy i konfiguracja
import os
import pandas as pd
import numpy as np
from tpot import TPOTClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from dotenv import load_dotenv

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
tpot = TPOTClassifier(generations=3, population_size=20, verbosity=2, random_state=42)
tpot.fit(X_train, y_train)

# Predykcja na zbiorze testowym
y_pred = tpot.predict(X_test)

# Eksport najlepszego modelu do pliku
tpot.export(os.path.join(MODELS_DIR_PATH,'tpot_best_model.py'))

all_evaluated = tpot.evaluated_individuals_

scored_pipelines = []
for pipeline_str, pipeline_data in all_evaluated.items():
    cv_score = pipeline_data['internal_cv_score']
    scored_pipelines.append((pipeline_str, cv_score))


sorted_pipelines = sorted(
    scored_pipelines,
    key=lambda x: x[1],
    reverse=True
)


print("\n=== 3 NAJLEPSZE MODELE  ===")
top_n = 3
for i, (pipeline_str, score) in enumerate(sorted_pipelines[:top_n], start=1):
    print(f"\nModel #{i}")
    print(f"Pipeline string: {pipeline_str}")
    print(f"Internal CV score: {score:.4f}")
