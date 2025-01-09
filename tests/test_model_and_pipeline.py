import pytest
import pandas as pd
import joblib
import os


@pytest.fixture
def model_path():
    """
    Zwraca ścieżkę do pliku z modelem .joblib.
    Dostosuj do swojej struktury katalogów i nazwy modelu.
    """
    return os.path.join("models", "random_forest_model.joblib")


@pytest.fixture
def loaded_model(model_path):
    """
    Próbuje wczytać model z pliku .joblib.
    """
    model = joblib.load(model_path)
    return model


@pytest.fixture
def sample_data():
    """
    Przykładowy DataFrame z kolumną rarity_numeric (target).
    Pipeline usuwa: image_path, rarity_numeric, collector_number, subtypes.
    """
    data = {
        "cmc": [2.0, 3.0],
        "collector_number": [453, 60],
        "num_colors": [1, 1],
        "year": [2022, 2001],
        "num_types": [2, 1],
        "text_length": [49, 10],
        "subtypes": ["Equipment,Demon", None],
        "image_path": [
            "cards\\Blade of the Oni\\neo_453.jpg",
            "cards\\Arcane Laboratory\\7ed_60.jpg"
        ],
        "num_supertypes": [0, 0],
        "color_B": [1, 0],
        "color_G": [0, 0],
        "color_R": [0, 0],
        "color_U": [0, 1],
        "color_W": [0, 0],
        "color_identity_B": [1, 0],
        "color_identity_G": [0, 0],
        "color_identity_R": [0, 0],
        "color_identity_U": [0, 1],
        "color_identity_W": [0, 0],
        "type_Artifact": [1, 0],
        "type_Battle": [0, 0],
        "type_Conspiracy": [0, 0],
        "type_Creature": [1, 0],
        "type_Dungeon": [0, 0],
        "type_Emblem": [0, 0],
        "type_Enchantment": [0, 0],
        "type_Hero": [0, 0],
        "type_Instant": [0, 0],
        "type_Kindred": [0, 0],
        "type_Land": [0, 0],
        "type_Phenomenon": [0, 0],
        "type_Plane": [0, 0],
        "type_Planeswalker": [0, 0],
        "type_Scheme": [0, 0],
        "type_Sorcery": [0, 0],
        "type_Vanguard": [0, 0],
        "supertype_Basic": [0, 0],
        "supertype_Elite": [0, 0],
        "supertype_Legendary": [0, 0],
        "supertype_Ongoing": [0, 0],
        "supertype_Snow": [0, 0],
        "supertype_Token": [0, 0],
        "supertype_World": [0, 0],
        "rarity_numeric": [3, 1],
    }
    return pd.DataFrame(data)


def test_model_load_and_predict(loaded_model, sample_data):
    """
    Sprawdza, czy model poprawnie ładuje się i zwraca predykcję
    dla 'rarity_numeric' po usunięciu zbędnych kolumn.
    """
    target_variable = 'rarity_numeric'
    X = sample_data.drop(columns=['image_path', target_variable, 'collector_number', 'subtypes'])
    y = sample_data[target_variable]

    y_pred = loaded_model.predict(X)
    assert len(y_pred) == len(y), "Liczba przewidywań nie zgadza się z liczbą próbek"


def compute_metrics(y_true, y_pred):
    """
    Prosta funkcja do liczenia accuracy.
    Jeśli y_true jest puste, rzucamy ValueError.
    """
    if len(y_true) == 0:
        raise ValueError("y_true is empty.")
    accuracy = (y_true == y_pred).mean()
    return accuracy


def test_metrics_calculation():
    """
    Sprawdza, czy compute_metrics działa poprawnie
    przy znanych danych (oczekiwana accuracy = 0.8).
    """
    y_true = pd.Series([0, 1, 1, 1, 0])
    y_pred = pd.Series([0, 1, 0, 1, 0])

    expected_acc = 0.8
    acc = compute_metrics(y_true, y_pred)
    assert abs(acc - expected_acc) < 1e-9, (
        f"Niepoprawna accuracy. Otrzymano {acc}, oczekiwano {expected_acc}"
    )


def validate_dataset(df):
    """
    Przykładowa funkcja walidująca: jeśli df jest pusty
    albo nie ma kolumny rarity_numeric, rzuca ValueError.
    """
    if df.empty:
        raise ValueError("Dataset is empty.")
    if 'rarity_numeric' not in df.columns:
        raise ValueError("Brak kolumny 'rarity_numeric' w zbiorze danych.")
    return True


def test_pipeline_with_no_data():
    """
    Test sprawdzający, czy walidacja rzuca błąd
    w przypadku pustego DataFrame.
    """
    df_empty = pd.DataFrame()
    with pytest.raises(ValueError) as exc_info:
        validate_dataset(df_empty)
    assert "Dataset is empty." in str(exc_info.value)


def test_pipeline_missing_target():
    """
    Test sprawdzający, czy walidacja rzuca błąd
    w przypadku braku kolumny 'rarity_numeric'.
    """
    df_no_target = pd.DataFrame({
        "cmc": [2.0],
        "collector_number": [453],
        # Brak 'rarity_numeric'
    })
    with pytest.raises(ValueError) as exc_info:
        validate_dataset(df_no_target)
    assert "Brak kolumny 'rarity_numeric'" in str(exc_info.value)
