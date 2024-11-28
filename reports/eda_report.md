# Analiza Eksploracyjna Danych (EDA)

## 1. Wczytanie i wstępna eksploracja danych

### 1.1. Statystyki opisowe dla zmiennych numerycznych

| Zmienna        |     Liczba |     Średnia |   Odchylenie standardowe |   Min |   25% |   50% |   75% |      Max |
|----------------|------------|-------------|--------------------------|-------|-------|-------|-------|----------|
| **cmc**        | 97,979     |      23.32  |                4,517.99  |     0 |     2 |     3 |     4 | 1,000,000 |
| **num_colors** | 97,979     |       0.92  |                    0.67  |     0 |     1 |     1 |     1 |        5 |
| **year**       | 97,979     |    2,015.57 |                    8.85  |  1993 |  2011 |  2019 |  2022 |     2025 |
| **num_types**  | 97,979     |       1.25  |                    0.48  |     1 |     1 |     1 |     1 |        6 |
| **text_length**| 97,979     |      24.35  |                   16.94  |     0 |    11 |    22 |    35 |      264 |

**Interpretacja:**

- **cmc (Converted Mana Cost):**
  - **Średnia:** 23.32 jest nietypowo wysoka dla tej cechy. Wartości `cmc` w grze **Magic: The Gathering** zazwyczaj mieszczą się w zakresie od 0 do około 15.
  - **Odchylenie standardowe:** 4,517.99 wskazuje na bardzo dużą zmienność danych.
  - **Maksimum:** 1,000,000 sugeruje obecność wartości odstających (outliers), które mogą zakłócać analizę.
  - **Wniosek:** Należy rozważyć usunięcie lub transformację wartości odstających w `cmc`.

- **num_colors (Liczba kolorów):**
  - **Średnia:** 0.92 wskazuje, że większość kart jest jednokolorowa lub bezkolorowa.
  - **Mediana:** 1, co potwierdza dominację kart jednokolorowych.
  - **Wniosek:** Rozkład `num_colors` jest prawostronnie skośny z przewagą mniejszych wartości.

- **year (Rok wydania):**
  - **Zakres lat:** Od 1993 do 2025.
  - **Średnia i mediana:** Około 2015-2019, co sugeruje większą liczbę kart z ostatnich lat.
  - **Wniosek:** Możliwe jest istnienie trendów czasowych w danych, warto to zbadać.

- **num_types (Liczba typów):**
  - **Średnia:** 1.25, mediana 1.
  - **Wniosek:** Większość kart ma jeden typ, ale są też karty z wieloma typami.

- **text_length (Długość tekstu):**
  - **Średnia:** 24.35 znaków.
  - **Maksimum:** 264 znaki.
  - **Wniosek:** Rozkład jest skośny z kilkoma kartami o bardzo długim tekście.

### 1.2. Liczba unikalnych wartości w każdej kolumnie

| Kolumna             | Liczba unikalnych wartości |
|---------------------|----------------------------|
| **image_paths**     | 97,979                     |
| **cmc**             | 19                         |
| **collector_number**| 14,094                     |
| **num_colors**      | 6                          |
| **colors**          | 31                         |
| **year**            | 33                         |
| **num_types**       | 6                          |
| **text_length**     | 112                        |
| **color_identity**  | 31                         |
| **rarity**          | 6                          |
| **supertypes**      | 11                         |
| **types**           | 59                         |
| **subtypes**        | 2,699                      |

**Interpretacja:**

- **image_paths:** Każda karta ma unikalną ścieżkę do obrazu, co jest oczekiwane.
- **cmc:** Tylko 19 unikalnych wartości pomimo dużego maksimum, co sugeruje, że większość kart ma `cmc` w wąskim zakresie.
- **colors** i **color_identity:** 31 unikalnych kombinacji, co odzwierciedla różnorodność kolorystyczną kart.
- **rarity:** 6 kategorii rzadkości, co pozwala na analizę wpływu rzadkości na inne cechy.

## 2. Przetwarzanie danych

### 2.1. Usunięcie wartości odstających w `cmc`

- **Działanie:** Usunięto karty o `cmc` większym niż 20.
- **Liczba kart po usunięciu:** 97,977.

**Interpretacja:**

- Usunięcie 2 kart z ekstremalnie wysokim `cmc` poprawi jakość analizy, eliminując wpływ wartości odstających.

## 3. Analiza korelacji

### 3.1. Silne korelacje między zmiennymi

| Zmienna 1           | Zmienna 2             | Korelacja |
|---------------------|-----------------------|-----------|
| **num_supertypes**  | **supertype_Legendary** | 0.7720    |
| **color_B**         | **color_identity_B**    | 0.8921    |
| **color_G**         | **color_identity_G**    | 0.8987    |
| **color_R**         | **color_identity_R**    | 0.8938    |
| **color_U**         | **color_identity_U**    | 0.8924    |
| **color_W**         | **color_identity_W**    | 0.8994    |

**Interpretacja:**

- **Kolory i identyfikacja kolorów:**
  - Wysoka korelacja między `color_*` a `color_identity_*` jest logiczna, ponieważ obie cechy są ze sobą powiązane.
  - **Wniosek:** Można rozważyć usunięcie jednej grupy zmiennych w celu redukcji redundancji.

- **`num_supertypes` i `supertype_Legendary`:**
  - Korelacja 0.7720 sugeruje, że karty z supertypem "Legendary" często mają więcej supertypów.
  - **Wniosek:** Supertyp "Legendary" jest dominujący wśród kart z wieloma supertypami.

## 4. Analiza niezrównoważonych cech

### 4.1. Niezrównoważone cechy binarne

Cechy z ekstremalnie niską proporcją wartości "1":

| Cechy                | Proporcja "1" (%) |
|----------------------|-------------------|
| **supertype_Elite**      | 0.0041          |
| **type_Dungeon**         | 0.0051          |
| **type_Hero**            | 0.0214          |
| **supertype_Ongoing**    | 0.0225          |
| **type_Phenomenon**      | 0.0286          |
| **type_Conspiracy**      | 0.0306          |
| **type_Battle**          | 0.0551          |
| **supertype_World**      | 0.0592          |
| **type_Scheme**          | 0.1123          |
| **type_Vanguard**        | 0.1215          |
| **type_Emblem**          | 0.1296          |
| **type_Kindred**         | 0.1500          |
| **type_Plane**           | 0.2613          |
| **supertype_Snow**       | 0.2980          |
| **type_Planeswalker**    | 1.4759          |
| **supertype_Token**      | 2.4587          |
| **supertype_Basic**      | 3.9785          |

**Interpretacja:**

- **Niska reprezentacja:** Wiele cech binarnych ma mniej niż 0.5% wartości "1".
- **Wpływ na modelowanie:** Modele mogą mieć trudności z nauką wzorców z tak rzadkich cech.
- **Wniosek:** Rozważyć usunięcie tych cech lub ich agregację.

## 5. Analiza brakujących danych

### 5.1. Brakujące wartości

| Kolumna    | Liczba brakujących wartości | Procent braków (%) |
|------------|-----------------------------|---------------------|
| **subtypes** | 37,486                      | 38.3                |

**Interpretacja:**

- **`subtypes`:** Znaczna liczba brakujących danych.
- **Wniosek:** Należy zdecydować, czy imputować brakujące wartości, usunąć kolumnę lub przeprowadzić dalszą analizę braków.

## 6. Analiza wartości zerowych

### 6.1. Liczba zer w zmiennych numerycznych

| Zmienna           | Liczba zer | Procent zer (%) |
|-------------------|------------|------------------|
| **cmc**           | 14,867     | 15.2             |
| **num_colors**    | 22,449     | 22.9             |
| **num_types**     | 591        | 0.6              |
| **num_supertypes**| 79,101     | 80.8             |
| **text_length**   | 4,227      | 4.3              |
| **rarity_numeric**| 30,787     | 31.4             |

**Interpretacja:**

- **`cmc`:** Wartości zero mogą odpowiadać kartom typu Land, które nie mają kosztu many.
- **`num_colors`:** Wysoka liczba zer wskazuje na karty bezkolorowe.
- **`num_supertypes`:** Większość kart nie posiada supertypów.
- **Wniosek:** Warto rozważyć dodanie cech binarnych lub transformację tych zmiennych.

## 7. Wizualizacje

**Uwaga:** Ze względu na format tekstowy raportu, wykresy nie są załączone. Opisy wizualizacji zostały przedstawione poniżej.

### 7.1. Rozkład `cmc`

**Opis wykresu:**

- Histogram `cmc` pokazuje, że większość kart ma koszt many w zakresie od 0 do 5.
- Rozkład jest prawostronnie skośny z długim ogonem wartości wyższych.

**Interpretacja:**

- **Dominacja niższych wartości `cmc`:** Sugeruje, że karty o niższym koszcie many są częstsze.
- **Wartości odstające:** Mimo usunięcia ekstremalnych wartości, nadal istnieją karty z wysokim `cmc`.

### 7.2. Rozkład `num_colors`

**Opis wykresu:**

- Wykres słupkowy `num_colors` pokazuje, że największą grupę stanowią karty jednokolorowe.
- Znaczna liczba kart jest bezkolorowa (`num_colors` = 0).

**Interpretacja:**

- **Przewaga kart jednokolorowych i bezkolorowych:** Może to wpływać na strategie modelowania i wymaga uwzględnienia w analizie.

### 7.3. Rozkład `rarity_numeric`

**Opis wykresu:**

- Wykres słupkowy `rarity_numeric` przedstawia liczbę kart w każdej kategorii rzadkości.
- Kategoriom przypisano wartości od 0 do 5.

**Interpretacja:**

- **Najwięcej kart w kategoriach "common" i "uncommon":** Stanowią one większość danych.
- **Niewielka liczba kart w kategoriach "mythic", "special", "bonus":** Może to wpływać na zdolność modelu do przewidywania tych klas.

### 7.4. Macierz korelacji

**Opis wykresu:**

- Macierz korelacji pokazuje zależności między wszystkimi zmiennymi numerycznymi i binarnymi.
- Silne korelacje zostały wcześniej zidentyfikowane.

**Interpretacja:**

- **Brak innych znaczących korelacji:** Większość zmiennych nie jest ze sobą silnie skorelowana.
- **Wniosek:** Modele mogą korzystać z tych zmiennych bez obawy o multikolinearność.

## 8. Wnioski

- **Wartości odstające w `cmc`:** Pomimo usunięcia ekstremalnych wartości, nadal istnieją karty z wysokim kosztem many. Może to wymagać dalszej analizy lub transformacji.
- **Redundancja zmiennych:** Wysoka korelacja między `color_*` a `color_identity_*` sugeruje możliwość usunięcia jednej grupy cech.
- **Niezrównoważone cechy binarne:** Wiele cech jest silnie niezrównoważonych, co może negatywnie wpłynąć na modele. Rozważenie ich usunięcia lub agregacji.
- **Brakujące dane w `subtypes`:** Decyzja o zachowaniu, imputacji lub usunięciu tej cechy powinna być podjęta w kontekście jej znaczenia dla modelu.
- **Wartości zerowe w zmiennych numerycznych:** Warto zbadać, czy wartości zerowe mają specyficzne znaczenie i jak mogą wpłynąć na modelowanie.

## 9. Rekomendacje

- **Przygotowanie danych do modelowania:**
  - Rozważyć usunięcie lub transformację niezrównoważonych i redundantnych cech.
  - Przeprowadzić standaryzację lub normalizację zmiennych numerycznych.
- **Dalsza analiza cech:**
  - Przeprowadzić analizę wpływu poszczególnych cech na zmienną docelową.
  - Wykorzystać techniki selekcji cech.