# %% [markdown]
# # **1. Importowanie potrzebnych bibliotek**

# %%
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from sklearn.model_selection import train_test_split
from collections import Counter
from ydata_profiling import ProfileReport
from dotenv import load_dotenv
from sklearn.preprocessing import MultiLabelBinarizer

# Załaduj zmienne z pliku .env
load_dotenv()

PROCESSED_DATASET_PATH = os.getenv("PROCESSED_DATASET_PATH")
TEST_DATASET_PATH = os.getenv("TEST_DATASET_PATH")
TRAIN_DATASET_PATH = os.getenv("TRAIN_DATASET_PATH")

DATASETS_DIR_PATH = os.getenv("DATASETS_DIR_PATH")
REPORTS_DIR_PATH = os.getenv("REPORTS_DIR_PATH")
EDA_REPORT_PATH = os.getenv("EDA_REPORT_PATH")

if not os.path.exists(REPORTS_DIR_PATH):
    os.makedirs(REPORTS_DIR_PATH)
if not os.path.exists(DATASETS_DIR_PATH):
    os.makedirs(DATASETS_DIR_PATH)

# Ustawienie stylu wykresów
sns.set_theme(style='whitegrid', palette='muted', font_scale=1.2)

# %% [markdown]
# # **2. Wczytanie danych**

# %%
# Wczytanie zbioru danych z pliku CSV
df = pd.read_csv(os.path.join(DATASETS_DIR_PATH, 'cards_metadata.csv'))

# Wyświetlenie przykładowych wierszy
print(df.sample(10))

# %% [markdown]
# # **3. Wstępna eksploracja danych**

# %%
# Sprawdzenie brakujących wartości w kolumnach
print("\nBrakujące wartości w każdej kolumnie:")
print(df.isnull().sum())

# Wyświetlenie statystyk opisowych
print("\nStatystyki opisowe:")
print(df.describe())

# %% [markdown]
# # **4. Przetwarzanie danych**

# %% [markdown]
# ## 4.1. Usunięcie kart z 'cmc' > 20

# %%
df = df[df['cmc'] <= 20]

# %% [markdown]
# ## 4.2. Przetwarzanie kolumny 'image_paths' do 'image_path'

# %%
df['image_path'] = df['image_paths'].apply(lambda x: x.split(';')[0] if pd.notnull(x) else '')

# Usunięcie wierszy z pustymi ścieżkami do obrazów
df = df[df['image_path'] != '']

# Sprawdzenie istnienia plików obrazów i usunięcie wierszy bez obrazów
df['image_exists'] = df['image_path'].apply(lambda x: os.path.exists(x))
df = df[df['image_exists']]
df.drop('image_exists', axis=1, inplace=True)

# Usunięcie wierszy z brakującymi wartościami w kluczowych kolumnach
df.dropna(subset=['cmc', 'year', 'rarity'], inplace=True)

# %% [markdown]
# ## 4.3. Konwersja kolumn 'colors' i 'color_identity' do list, obsługa wartości NaN

# %%
def convert_colors_to_list(x):
    if pd.isnull(x) or x == '':
        return []  # Dla bezkolorowych kart
    else:
        return x.split(',')

df['colors'] = df['colors'].apply(convert_colors_to_list)
df['color_identity'] = df['color_identity'].apply(convert_colors_to_list)

# %% [markdown]
# ## 4.4. Obliczenie 'num_colors'

# %%
df['num_colors'] = df['colors'].apply(len)

# %% [markdown]
# ## 4.5. Konwersja kolumn 'supertypes' i 'types' do list, obsługa wartości NaN

# %%
def convert_to_list(x):
    if pd.isnull(x) or x == '':
        return []
    else:
        return x.split(',')

df['supertypes'] = df['supertypes'].apply(convert_to_list)
df['types'] = df['types'].apply(convert_to_list)

# %% [markdown]
# ## 4.6. Obliczenie 'num_supertypes' i 'num_types'

# %%
df['num_supertypes'] = df['supertypes'].apply(len)
df['num_types'] = df['types'].apply(len)

# %% [markdown]
# ## 4.7. One-Hot Encoding dla 'colors', 'color_identity', 'types' i 'supertypes'

# %%
# One-Hot Encoding dla 'colors'
mlb_colors = MultiLabelBinarizer()
colors_encoded = pd.DataFrame(mlb_colors.fit_transform(df['colors']), columns=['color_' + c for c in mlb_colors.classes_], index=df.index)
df = pd.concat([df, colors_encoded], axis=1)

# One-Hot Encoding dla 'color_identity'
mlb_color_identity = MultiLabelBinarizer()
color_identity_encoded = pd.DataFrame(mlb_color_identity.fit_transform(df['color_identity']), columns=['color_identity_' + c for c in mlb_color_identity.classes_], index=df.index)
df = pd.concat([df, color_identity_encoded], axis=1)

# One-Hot Encoding dla 'types'
mlb_types = MultiLabelBinarizer()
types_encoded = pd.DataFrame(mlb_types.fit_transform(df['types']), columns=['type_' + t for t in mlb_types.classes_], index=df.index)
df = pd.concat([df, types_encoded], axis=1)

# One-Hot Encoding dla 'supertypes'
mlb_supertypes = MultiLabelBinarizer()
supertypes_encoded = pd.DataFrame(mlb_supertypes.fit_transform(df['supertypes']), columns=['supertype_' + st for st in mlb_supertypes.classes_], index=df.index)
df = pd.concat([df, supertypes_encoded], axis=1)

# %% [markdown]
# ## 4.8. Konwersja 'cmc' i 'num_colors' do typu całkowitego

# %%
df['cmc'] = df['cmc'].astype(int)
df['num_colors'] = df['num_colors'].astype(int)

# %% [markdown]
# ## 4.9. Mapowanie 'rarity' na wartości numeryczne

# %%
rarity_mapping = {'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3, 'special': 4, 'bonus': 5}
df['rarity_numeric'] = df['rarity'].map(rarity_mapping)

# %% [markdown]
# ## 4.10. Usunięcie oryginalnych kolumn po encodingu

# %%
columns_to_drop = ['image_paths', 'colors', 'color_identity', 'types', 'supertypes', 'rarity']
df.drop(columns=columns_to_drop, inplace=True)

# %% [markdown]
# # **5. Generowanie raportu**

# %%
profile = ProfileReport(df, title="Raport EDA dla zbioru danych", explorative=True)
profile.to_file(EDA_REPORT_PATH)

# %% [markdown]
# # **6. Eksploracja i wizualizacja danych**

# %% [markdown]
# ## 6.1. Histogram 'cmc'

# %%
min_cmc = df['cmc'].min()
max_cmc = df['cmc'].max()
bins = np.arange(min_cmc - 0.5, max_cmc + 1.5, 1)

plt.figure(figsize=(12, 6))
sns.histplot(df['cmc'], bins=bins, kde=False, edgecolor='black')
plt.title('Rozkład cmc')
plt.xlabel('cmc (Converted Mana Cost)')
plt.ylabel('Liczba kart')
plt.xticks(np.arange(min_cmc, max_cmc + 1, 1))
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6.2. Wykres słupkowy liczby wystąpień każdego koloru w 'colors'

# %%
color_columns = [col for col in df.columns if col.startswith('color_')]
color_counts = df[color_columns].sum().sort_values(ascending=False)

plt.figure(figsize=(8, 6))
sns.barplot(x=color_counts.index.str.replace('color_', ''), y=color_counts.values)
plt.title('Częstość występowania kolorów')
plt.xlabel('Kolor')
plt.ylabel('Liczba kart')
plt.show()

# %% [markdown]
# ## 6.3. Wykres słupkowy liczby wystąpień każdego koloru w 'color_identity'

# %%
color_identity_columns = [col for col in df.columns if col.startswith('color_identity_')]
color_identity_counts = df[color_identity_columns].sum().sort_values(ascending=False)

plt.figure(figsize=(8, 6))
sns.barplot(x=color_identity_counts.index.str.replace('color_identity_', ''), y=color_identity_counts.values)
plt.title('Częstość występowania kolorów w identyfikacji kolorów')
plt.xlabel('Color Identity')
plt.ylabel('Liczba kart')
plt.show()

# %% [markdown]
# ## 6.4. Wykres słupkowy 'num_colors'

# %%
plt.figure(figsize=(10, 6))
sns.countplot(x='num_colors', data=df)
plt.title('Liczba kolorów kart')
plt.xlabel('Liczba kolorów')
plt.ylabel('Liczba kart')
plt.show()

# %% [markdown]
# ## 6.5. Wykres słupkowy 'num_types'

# %%
plt.figure(figsize=(10, 6))
sns.countplot(x='num_types', data=df)
plt.title('Liczba typów kart')
plt.xlabel('Liczba typów')
plt.ylabel('Liczba kart')
plt.show()

# %% [markdown]
# ## 6.6. Wykres słupkowy 'num_supertypes'

# %%
plt.figure(figsize=(10, 6))
sns.countplot(x='num_supertypes', data=df)
plt.title('Liczba supertypów kart')
plt.xlabel('Liczba supertypów')
plt.ylabel('Liczba kart')
plt.show()

# %% [markdown]
# ## 6.7. Wykres słupkowy 'types'

# %%
type_columns = [col for col in df.columns if col.startswith('type_')]
type_counts = df[type_columns].sum().sort_values(ascending=False)

plt.figure(figsize=(14, 6))
sns.barplot(x=type_counts.index.str.replace('type_', ''), y=type_counts.values)
plt.title('Rozkład types')
plt.xlabel('Types')
plt.ylabel('Liczba kart')
plt.xticks(rotation=45)
plt.show()

# %% [markdown]
# ## 6.8. Wykres słupkowy 'supertypes'

# %%
supertype_columns = [col for col in df.columns if col.startswith('supertype_')]
supertype_counts = df[supertype_columns].sum().sort_values(ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x=supertype_counts.index.str.replace('supertype_', ''), y=supertype_counts.values)
plt.title('Rozkład supertypes')
plt.xlabel('Supertypes')
plt.ylabel('Liczba kart')
plt.xticks(rotation=45)
plt.show()

# %% [markdown]
# ## 6.9. Wykres słupkowy 'rarity_numeric'

# %%
rarity_counts = df['rarity_numeric'].value_counts().sort_index()
rarity_labels = ['common', 'uncommon', 'rare', 'mythic', 'special', 'bonus']

plt.figure(figsize=(8, 6))
sns.barplot(x=rarity_counts.index, y=rarity_counts.values, palette='viridis')
plt.title('Rozkład rzadkości kart')
plt.xlabel('Rarity Numeric')
plt.ylabel('Liczba kart')
plt.xticks(ticks=rarity_counts.index, labels=rarity_labels)
plt.show()

# %% [markdown]
# ## 6.10. Wykres pudełkowy 'cmc'

# %%
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['cmc'])
plt.title('Box Plot of cmc')
plt.show()

# %% [markdown]
# ## 6.11. Wykres pudełkowy 'num_colors'

# %%
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['num_colors'])
plt.title('Box Plot of Number of Colors')
plt.show()

# %% [markdown]
# ## 6.12. Wykres pudełkowy 'text_length'

# %%
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['text_length'])
plt.title('Box Plot of Text Length')
plt.show()

# %% [markdown]
# ## 6.13. Generowanie macierzy korelacji

# %%
# Wybór zmiennych numerycznych i binarnych do korelacji
numerical_cols = ['cmc', 'num_colors', 'text_length', 'year', 'num_types', 'num_supertypes', 'rarity_numeric']

corr_matrix = df[numerical_cols + color_columns + color_identity_columns + type_columns + supertype_columns].corr()

# Wyświetlenie macierzy korelacji
plt.figure(figsize=(20, 16))
sns.heatmap(corr_matrix, cmap='viridis')
plt.title('Correlation Matrix')
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.show()

# %% [markdown]
# # **7. Podział danych na zbiory treningowe i testowe**

# %%
train_df, test_df = train_test_split(df, test_size=0.3, random_state=42, stratify=df['rarity_numeric'])

print(f"Liczba kart w zbiorze treningowym: {len(train_df)}")
print(f"Liczba kart w zbiorze testowym: {len(test_df)}")

# %% [markdown]
# # **8. Wyświetlenie przykładowego obrazu karty**

# %%
sample_image_path = train_df.iloc[1]['image_path']
image = Image.open(sample_image_path)
plt.figure(figsize=(6, 8))
plt.imshow(image)
plt.axis('off')
plt.show()

# %% [markdown]
# # **9. Zapisanie przetworzonych danych**

# %% [markdown]
# ## 9.1. Zapis plików

# %%
df.to_csv(PROCESSED_DATASET_PATH, index=False)
train_df.to_csv(TRAIN_DATASET_PATH, index=False)
test_df.to_csv(TEST_DATASET_PATH, index=False)
