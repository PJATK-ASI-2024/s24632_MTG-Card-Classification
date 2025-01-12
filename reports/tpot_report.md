# Raport z wyników modelu

## 1. Wprowadzenie

W ramach projektu wykorzystano narzędzie **TPOT (AutoML)** do automatycznego wyszukania najlepszego modelu predykcyjnego dla zbioru danych z cechą docelową `rarity_numeric`. Dane wejściowe zostały uprzednio przetworzone i oczyszczone, a następnie rozdzielone na zbiór treningowy (70%) i testowy (30%). Metryką oceny modelu jest **Accuracy**.

---

## 2. Najlepszy wybrany pipeline

W wyniku przeprowadzonej optymalizacji za pomocą narzędzia AutoML, najlepszym pipeline’em okazał się:

**RandomForestClassifier** z następującymi hiperparametrami:

- `bootstrap=True`
- `criterion=gini`
- `max_features=0.5`
- `min_samples_leaf=1`
- `min_samples_split=4`
- `n_estimators=100`

### Raport klasyfikacji

Poniżej przedstawiono metryki jakości modelu na zbiorze testowym dla poszczególnych klas. Wartości `precision`, `recall` oraz `f1-score` zostały wyliczone dla każdej klasy, natomiast `support` oznacza liczbę próbek danej klasy w zbiorze testowym.

| Klasa | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| **0** | 0.72      | 0.74   | 0.73     | 9236    |
| **1** | 0.60      | 0.55   | 0.58     | 7020    |
| **2** | 0.73      | 0.77   | 0.75     | 10583   |
| **3** | 0.81      | 0.75   | 0.78     | 2434    |
| **4** | 0.24      | 0.05   | 0.08     | 118     |
| **5** | 0.00      | 0.00   | 0.00     | 3       |

**Accuracy:** 0.7046  

**Macro avg:**  
- Precision: 0.52  
- Recall: 0.48  
- F1-score: 0.49  

**Weighted avg:**  
- Precision: 0.70  
- Recall: 0.70  
- F1-score: 0.70  

### Interpretacja wyników

- Model osiągnął **dokładność 70.46%** na zbiorze testowym.
- Klasy 0, 2 oraz 3 zostały sklasyfikowane stosunkowo dobrze, z F1-score w okolicach 0.7–0.8.  
- Klasy 4 i 5 są bardzo rzadkie i trudne do przewidzenia, co znajduje odzwierciedlenie w niskich wynikach. Możliwe, że do poprawy tych wyników konieczne będzie:
  - Zwiększenie liczby próbek tych klas,  
  - Użycie metod oversamplingu (np. SMOTE) lub odpowiednie ważenie klas,  
  - Dalsza inżynieria cech (feature engineering).

---

## 3. Pozostałe rekomendacje (top 3 pipeline’y wg TPOT)

Poza najlepszym pipeline’em, TPOT wskazał również **dwa inne modele**, jednak podczas automatycznej optymalizacji nie zapisano ich definicji jako `'pipeline'` (zabrakło klucza `'pipeline'` w `tpot.evaluated_individuals_`). Oznacza to, że:

- Nie mogłem wygenerować pełnego raportu klasyfikacji w ten sam sposób.  
- Wiemy jednak, że także bazują na **RandomForestClassifier**, lecz z nieco innymi hiperparametrami (np. inną wartością `max_features` i użyciem `MinMaxScaler`).

### Model #2

- **Nazwa pipeline**:  
`RandomForestClassifier(MinMaxScaler(input_matrix), RandomForestClassifier__bootstrap=True, RandomForestClassifier__criterion=gini, RandomForestClassifier__max_features=0.9500000000000001, RandomForestClassifier__min_samples_leaf=1, RandomForestClassifier__min_samples_split=4, RandomForestClassifier__n_estimators=100)`

- **Internal CV score (TPOT)**: ~0.6927  
- Różni się od najlepszego modelu np. `max_features=0.95` i wstępnym skalowaniem `MinMaxScaler`.
- Ze względu na brak klucza `'pipeline'`, nie oceniono go na zbiorze testowym.

### Model #3

- **Nazwa pipeline**:  
`RandomForestClassifier(MinMaxScaler(input_matrix), RandomForestClassifier__bootstrap=True, RandomForestClassifier__criterion=gini, RandomForestClassifier__max_features=0.2, RandomForestClassifier__min_samples_leaf=1, RandomForestClassifier__min_samples_split=4, RandomForestClassifier__n_estimators=100)`

- **Internal CV score (TPOT)**: ~0.6883  
- Podobny do #2, ale z `max_features=0.2`.  
- Również brak `'pipeline'`, więc brak raportu testowego.

---

## 4. Uzasadnienie wyboru najlepszego modelu

Wszystkie trzy rekomendowane modele okazały się **RandomForestClassifier** z różnymi ustawieniami. Już na podstawie wewnętrznego score’u CV (i faktu, że model #1 został poprawnie wyeksportowany) uznano go za najlepszy. Model #1 miał nieco wyższy **internal_cv_score** (~0.6936) od pozostałych (~0.6927 i ~0.6883).

Z tego względu **finalnie wybrałem pipeline #1** jako najbardziej obiecujący pod kątem dalszego doskonalenia i wdrożenia.

---

## 5. Podsumowanie i dalsze kroki

Najlepszy model **Random Forest** osiągnął dokładność ~70.46% na zbiorze testowym, co jest przyzwoitym wynikiem, szczególnie dla głównych klas (0, 2, 3). Nadal warto rozważyć:

1. **Balansowanie danych**  w celu poprawy wyników rzadkich klas (4, 5).  
2. **Rozbudowę** zbioru danych lub analiza cech w celu lepszej separacji klas.  
3. **Zwiększenie** liczby generacji w TPOT, aby przetestować więcej algorytmów .  
4. **Analizę ważności cech** i interpretację modelu, by zrozumieć, które zmienne najmocniej wpływają na predykcję.

---

## 6. Wnioski dotyczące AutoML

Narzędzie **TPOT** pozwoliło w krótkim czasie wygenerować, przetestować i porównać kilka wariantów pipeline’ów.  
Przy tak ograniczonej liczbie pokoleń i populacji widać, że TPOT skupił się głównie na **RandomForestClassifier**. Aby uzyskać większą różnorodność modeli, należy zwiększyć parametry `generations` i `population_size`.
