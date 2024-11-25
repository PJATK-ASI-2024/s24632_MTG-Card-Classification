# Przewidywanie cech kart Magic: The Gathering na podstawie obrazów

## Spis treści

- [Opis projektu](#opis-projektu)
- [Źródło danych](#źródło-danych)
  - [Dlaczego Scryfall?](#dlaczego-scryfall)
  - [Użyte endpointy API](#użyte-endpointy-api)
- [Cele projektu](#cele-projektu)
- [Struktura projektu](#struktura-projektu)
- [Użyte skrypty](#użyte-skrypty)
- [Podsumowanie](#podsumowanie)

---

## Opis projektu

Celem tego projektu jest zbudowanie modelu, który na podstawie obrazu karty z gry **Magic: The Gathering** będzie w stanie przewidzieć jej kluczowe cechy:

- **Converted Mana Cost (cmc)**
- **Liczba kolorów (num_colors)**
- **Rzadkość karty (rarity)**
- **Rok wydania (year)**
- **Tożsamość kolorów (color_identity)**

Projekt ten łączy w sobie elementy **wizji komputerowej** oraz **uczenia maszynowego**, wykorzystując głębokie sieci neuronowe do ekstrakcji informacji z obrazów i przewidywania cech kart.

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

## Cele projektu

Główne cele projektu to:

1. **Przygotowanie i przetworzenie danych**:
   - Pobranie danych kart i ich obrazów z API Scryfall.
   - Przetworzenie danych, w tym obsługa brakujących wartości i standaryzacja formatów.
   - Analiza eksploracyjna danych (EDA) w celu zrozumienia ich struktury i charakterystyk.

2. **Budowa modelu predykcyjnego**:
   - Wykorzystanie głębokich sieci neuronowych do ekstrakcji cech z obrazów kart.
   - Trenowanie modelu do przewidywania wybranych cech kart na podstawie obrazów.
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

Projekt ten ma na celu stworzenie modelu zdolnego do przewidywania kluczowych cech kart **Magic: The Gathering** na podstawie samych obrazów. Wykorzystanie API Scryfall jako źródła danych zapewnia dostęp do bogatego i aktualnego zestawu informacji, co zwiększa jakość i wiarygodność wyników.

Dzięki zastosowaniu technik przetwarzania obrazów i uczenia maszynowego, projekt ten może znaleźć praktyczne zastosowanie w automatycznej kategoryzacji kart, wspomaganiu kolekcjonerów czy tworzeniu aplikacji mobilnych zdolnych do rozpoznawania kart na podstawie zdjęć.

---
