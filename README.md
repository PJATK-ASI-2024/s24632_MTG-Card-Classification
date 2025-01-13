# Przewidywanie rzadkości kart Magic: The Gathering na podstawie obrazów

## Spis treści

- [Opis projektu](#opis-projektu)
  - [Cel projektu](#cel-projektu)
- [Źródło danych](#źródło-danych)
  - [Dlaczego Scryfall?](#dlaczego-scryfall)
  - [Użyte endpointy API](#użyte-endpointy-api)
- [Opis modelu](#opis-modelu)
  - [Wybór modelu](#wybór-modelu)
  - [Raport TPOT](#raport-tpot)
- [Cele projektu](#cele-projektu)
- [Struktura projektu](#struktura-projektu)
- [Użyte skrypty](#użyte-skrypty)
- [Podsumowanie](#podsumowanie)

---

## Opis projektu

Celem tego projektu jest zbudowanie modelu, który na podstawie metadanych obrazu karty z gry **Magic: The Gathering** będzie w stanie przewidzieć jej **rzadkość** (`rarity`). Projekt ten wykorzystuje **uczenia maszynowego**, ekstrakcji informacji z metadanych i przewidywania rzadkości kart.

### Cel projektu

Projekt został stworzony w celu automatyzacji procesu kategoryzacji kart **Magic: The Gathering** na podstawie ich obrazów, co może znaleźć zastosowanie w różnych dziedzinach, takich jak zarządzanie kolekcjami, wsparcie dla kolekcjonerów czy tworzenie aplikacji mobilnych umożliwiających rozpoznawanie kart.

---

## Źródło danych

### Dlaczego Scryfall?

**Scryfall** to jedno z najbardziej kompletnych i aktualnych źródeł danych dotyczących kart **Magic: The Gathering**. Zapewnia publiczne API, które umożliwia dostęp do:

- Szczegółowych informacji o kartach, w tym ich cechach i obrazach.
- Pełnych zbiorów danych (bulk data), co ułatwia pobieranie dużych ilości informacji w efektywny sposób.
- Katalogów typów i podtypów kart, co jest niezbędne do analizy i kategoryzacji danych.

Wybór Scryfall jako źródła danych pozwala na dostęp do aktualnych i historycznych danych kart, co zwiększa jakość i zakres analizy.

### Użyte endpointy API

Do pobrania danych i obrazów kart wykorzystano następujące endpointy API Scryfall:

- **Bulk Data**:
  - `https://api.scryfall.com/bulk-data` - Endpoint umożliwiający pobranie pełnego zestawu danych kart.

- **Katalogi typów i podtypów**:
  - `https://api.scryfall.com/catalog/supertypes` - Supertypy kart.
  - `https://api.scryfall.com/catalog/card-types` - Typy kart.
  - `https://api.scryfall.com/catalog/artifact-types` - Typy artefaktów.
  - `https://api.scryfall.com/catalog/battle-types` - Typy bitew.
  - `https://api.scryfall.com/catalog/creature-types` - Typy stworzeń.
  - `https://api.scryfall.com/catalog/enchantment-types` - Typy enchantmentów.
  - `https://api.scryfall.com/catalog/land-types` - Typy lądów.
  - `https://api.scryfall.com/catalog/planeswalker-types` - Typy planeswalkerów.
  - `https://api.scryfall.com/catalog/spell-types` - Typy czarów.

---

## Opis modelu

### Wybór modelu

Do przewidywania rzadkości kart użyto modelu **RandomForestClassifier**, wybranego za pomocą narzędzia AutoML **TPOT**. RandomForestClassifier został wybrany ze względu na swoją skuteczność w zadaniach klasyfikacyjnych oraz zdolność radzenia sobie z dużą ilością cech i interakcji między nimi.

### Raport TPOT

Szczegółowy raport z wyboru modelu oraz wyników znajduje się w pliku [reports/tpot_report.md](reports/tpot_report.md).

**Najlepszy wybrany pipeline:**

- **RandomForestClassifier** z następującymi hiperparametrami:
  - `bootstrap=True`
  - `criterion=gini`
  - `max_features=0.5`
  - `min_samples_leaf=1`
  - `min_samples_split=4`
  - `n_estimators=100`

**Raport klasyfikacji:**

| Klasa | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| 0     | 0.72      | 0.74   | 0.73     | 9236    |
| 1     | 0.61      | 0.56   | 0.58     | 7020    |
| 2     | 0.73      | 0.77   | 0.75     | 10583   |
| 3     | 0.82      | 0.75   | 0.78     | 2434    |
| 4     | 0.24      | 0.05   | 0.08     | 118     |
| 5     | 0.00      | 0.00   | 0.00     | 3       |

**Accuracy:** 0.71  
**Macro avg:**  
- Precision: 0.52  
- Recall: 0.48  
- F1-score: 0.49  

**Weighted avg:**  
- Precision: 0.70  
- Recall: 0.71  
- F1-score: 0.70  

**Interpretacja wyników:**

- Model osiągnął **dokładność 71%**.
- Klasy 0, 2 oraz 3 zostały sklasyfikowane stosunkowo dobrze, z F1-score powyżej 0.7.
- Klasy 4 i 5 są rzadkie i trudne do przewidzenia, co znajduje odzwierciedlenie w bardzo niskich wynikach (F1-score: 0.08 i 0.00). Możliwe, że do poprawy tych wyników konieczne będzie:
  - Zwiększenie liczby próbek tych klas.
  - Użycie metod oversamplingu lub undersamplingu.

**Podsumowanie:**

Najlepszy model Random Forest osiągnął przyzwoite wyniki, zwłaszcza dla dominujących klas (0, 2, 3). Istnieje jednak potrzeba dalszego dostrojenia modelu lub zmiany strategii przetwarzania danych w celu poprawy jakości predykcji dla mniej licznych klas. W następnych krokach warto rozważyć:

- Analizę ważności cech, aby zrozumieć, które zmienne mają największy wpływ na predykcje.
- Zastosowanie technik balansu zbioru danych (np. SMOTE, class weights).
- Przetestowanie innych algorytmów lub bardziej złożonych pipeline’ów pod kątem poprawy wyników dla trudniejszych klas.

---

## Cele projektu

Główne cele projektu to:

1. **Przygotowanie i przetworzenie danych**:
   - Pobranie danych kart i ich obrazów z API Scryfall.
   - Przetworzenie danych, w tym obsługa brakujących wartości i standaryzacja formatów.
   - Analiza eksploracyjna danych (EDA) w celu zrozumienia ich struktury i charakterystyk.

2. **Budowa modelu predykcyjnego**:
   - Wykorzystanie głębokich sieci neuronowych do ekstrakcji cech z obrazów kart.
   - Trenowanie modelu do przewidywania rzadkości kart na podstawie obrazów.
   - Ocena wydajności modelu i optymalizacja jego parametrów.

3. **Dokumentacja i wizualizacja wyników**:
   - Przygotowanie czytelnej dokumentacji projektu.
   - Wizualizacja wyników analizy i działania modelu.
   - Przedstawienie wniosków i potencjalnych kierunków dalszego rozwoju.

---

## Struktura projektu

Poniżej przedstawiono ogólną strukturę pracy nad projektem:

1. **Pobranie danych**:
   - Wykorzystanie skryptu `download_bulk_data.py` do pobrania pełnego zestawu danych kart.
   - Użycie skryptu `download_card_images.py` do pobrania obrazów kart.

2. **Przygotowanie danych**:
   - Przetworzenie pobranych danych za pomocą skryptu `make_metadata_csv.py`, tworząc ujednolicony plik CSV z informacjami o kartach.
   - Obsługa brakujących wartości i standaryzacja formatów danych.

3. **Analiza eksploracyjna danych (EDA)**:
   - Wykorzystanie notebooka `data_analysis.ipynb` do przeprowadzenia EDA.
   - Wizualizacja rozkładów cech, analiza korelacji i identyfikacja potencjalnych problemów w danych.

4. **Przetwarzanie i kodowanie danych**:
   - Konwersja kolumn tekstowych na odpowiednie formaty (np. listy, kody).
   - One-hot encoding dla zmiennych kategorycznych o ograniczonej liczbie unikalnych wartości.
   - Przygotowanie danych do trenowania modelu.

5. **Budowa i trenowanie modelu**:
   - Wybór odpowiedniej architektury sieci neuronowej do analizy obrazów (np. CNN).
   - Trenowanie modelu na zbiorze treningowym i walidacja na zbiorze testowym.
   - Optymalizacja parametrów modelu.

6. **Ewaluacja modelu i wnioski**:
   - Ocena wydajności modelu na podstawie wybranych metryk.
   - Wizualizacja wyników i analiza błędów.
   - Sformułowanie wniosków i propozycje dalszych usprawnień.

---

## Użyte skrypty

W projekcie wykorzystano następujące skrypty:

1. **`download_bulk_data.py`**:
   - Służy do pobrania pełnego zestawu danych kart z endpointu bulk data Scryfall.
   - Umożliwia efektywne i szybkie pobranie wszystkich niezbędnych informacji o kartach.

2. **`download_card_images.py`**:
   - Pobiera obrazy kart na podstawie linków zawartych w danych bulk.
   - Upewnia się, że wszystkie obrazy są poprawnie zapisane i skatalogowane.

3. **`make_metadata_csv.py`**:
   - Przetwarza pobrane dane kart i tworzy ujednolicony plik CSV z kluczowymi informacjami.
   - Obsługuje brakujące wartości i standaryzuje formaty danych.

4. **`data_analysis.ipynb`**:
   - Notebook Jupyter zawierający kod do analizy eksploracyjnej danych.
   - Zawiera wizualizacje, statystyki opisowe i przetwarzanie danych niezbędne do przygotowania ich do modelowania.

---

## Podsumowanie

Projekt ten ma na celu stworzenie modelu zdolnego do przewidywania rzadkości kart **Magic: The Gathering** na podstawie samych obrazów. Wykorzystanie API Scryfall jako źródła danych zapewnia dostęp do bogatego i aktualnego zestawu informacji, co zwiększa jakość i wiarygodność wyników.

Dzięki zastosowaniu technik przetwarzania obrazów i uczenia maszynowego, projekt ten może znaleźć praktyczne zastosowanie w automatycznej kategoryzacji kart, wspomaganiu kolekcjonerów czy tworzeniu aplikacji mobilnych zdolnych do rozpoznawania kart na podstawie zdjęć.

### Dodatkowe materiały

- **Raport TPOT**: [reports/tpot_report.md](reports/tpot_report.md)
- **Dokumentacja Airflow DAG-ów**: [docs/airflow_dags.md](docs/airflow_dags.md) *(jeśli istnieje)*

---

## Instalacja i uruchomienie

1. **Klonowanie repozytorium**:
   ```bash
   git clone https://github.com/PJATK-ASI-2024/s24632_MTG-Card-Classification.git
   cd s24632_MTG-Card-Classification
   ```
2. **Konfiguracja środowiska**:

- Upewnij się, że masz zainstalowane Docker i Docker Compose.
- Skonfiguruj plik `.env` z odpowiednimi zmiennymi środowiskowymi.

3. **Budowanie i uruchamianie kontenerów**:
```bash
docker compose build
docker compose up airflow-init
docker compose up -d
```
4. **Dostęp do interfejsu Airflow**:

- Otwórz przeglądarkę i przejdź pod adres `http://localhost:8080`.