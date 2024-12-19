import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error, classification_report
from dotenv import load_dotenv

# Załadowanie zmiennych środowiskowych z pliku .env
load_dotenv()
PROCESSED_DATASET_PATH = os.getenv("PROCESSED_DATASET_PATH")

# Ścieżki do plików z danymi
df = pd.read_csv(PROCESSED_DATASET_PATH)

target_variable = 'rarity_numeric'
features = df.drop(columns=['image_path', target_variable, 'collector_number', 'subtypes']).columns.tolist()

X = df[features]
y = df[target_variable]

# Podział danych na zbiór treningowy (70%) i walidacyjny (30%)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

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

# Dokładność (accuracy)
accuracy = accuracy_score(y_val, y_pred)

mae = mean_absolute_error(y_val, y_pred)

# Pełny raport klasyfikacji
report = classification_report(y_val, y_pred)

# Wyświetlenie metryk
print("Metryki jakości prototypowego modelu:")
print(f"Accuracy: {accuracy:.4f}")
print(f"Mean Absolute Error (MAE): {mae:.4f}")
print("Raport klasyfikacji:")
print(report)
