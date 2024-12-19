# Importowanie potrzebnych bibliotek
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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Inicjalizacja klasyfikatora TPOT
tpot = TPOTClassifier(generations=3, population_size=20, verbosity=2, random_state=42)
tpot.fit(X_train, y_train)

# Predykcja na zbiorze testowym
y_pred = tpot.predict(X_test)

# Wyświetlenie raportu klasyfikacji
print("Raport klasyfikacji:")
print(classification_report(y_test, y_pred))

# Eksport najlepszego modelu
tpot.export(os.path.join(MODELS_DIR_PATH,'tpot_best_model.py'))
