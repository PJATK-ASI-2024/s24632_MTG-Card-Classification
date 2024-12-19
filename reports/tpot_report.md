# Raport z wyników modelu

## Najlepszy wybrany pipeline

W wyniku przeprowadzonej optymalizacji za pomocą narzędzi AutoML najlepszym pipeline’em okazał się:

**RandomForestClassifier** z następującymi hiperparametrami:

- `bootstrap=True`
- `criterion=gini`
- `max_features=0.5`
- `min_samples_leaf=1`
- `min_samples_split=4`
- `n_estimators=100`


## Raport klasyfikacji

Poniżej przedstawiono metryki jakości modelu na zbiorze testowym dla poszczególnych klas. Wartości `precision`, `recall` oraz `f1-score` zostały wyliczone dla każdej klasy, natomiast `support` oznacza liczbę próbek danej klasy w zbiorze testowym.

| Klasa | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|----------|
| 0     | 0.72      | 0.74   | 0.73     | 9236     |
| 1     | 0.61      | 0.56   | 0.58     | 7020     |
| 2     | 0.73      | 0.77   | 0.75     | 10583    |
| 3     | 0.82      | 0.75   | 0.78     | 2434     |
| 4     | 0.24      | 0.05   | 0.08     | 118      |
| 5     | 0.00      | 0.00   | 0.00     | 3        |

**Accuracy:** 0.71  
**Macro avg:**  
- Precision: 0.52  
- Recall: 0.48  
- F1-score: 0.49  

**Weighted avg:**  
- Precision: 0.70  
- Recall: 0.71  
- F1-score: 0.70  

## Interpretacja wyników

- Model osiągnął **dokładność 71%**.
- Klasy 0, 2 oraz 3 zostały sklasyfikowane stosunkowo dobrze, z F1-score powyżej 0.7.
- Klasy 4 i 5 są rzadkie i trudne do przewidzenia, co znajduje odzwierciedlenie w bardzo niskich wynikach (F1-score: 0.08 i 0.00). Możliwe, że do poprawy tych wyników konieczne będzie:
  - Zwiększenie liczby próbek tych klas,
  - Użycie metod oversamplingu lub undersamplingu,

## Podsumowanie

Najlepszy model Random Forest osiągnął przyzwoite wyniki, zwłaszcza dla dominujących klas (0, 2, 3). Istnieje jednak potrzeba dalszego dostrojenia modelu lub zmiany strategii przetwarzania danych w celu poprawy jakości predykcji dla mniej licznych klas. W następnych krokach warto rozważyć:

- Analizę ważności cech, aby zrozumieć, które zmienne mają największy wpływ na predykcje.
- Zastosowanie technik balansu zbioru danych (np. SMOTE, class weights).
- Przetestowanie innych algorytmów lub bardziej złożonych pipeline’ów pod kątem poprawy wyników dla trudniejszych klas.
