# %% [markdown]
# # **1. Importowanie potrzebnych bibliotek**
# 

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
# # 4.1. Usunięcie kart z 'cmc' > 20

# %%
df = df[df['cmc'] <= 200]

# %% [markdown]
# # 4.2. Przetwarzanie kolumny 'image_paths' do 'image_path'
# 

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
# # 4.3. Konwersja kolumn 'colors' i 'color_identity' do list, obsługa wartości NaN

# %%
def convert_colors_to_list(x):
    if pd.isnull(x) or x == '':
        return ['C']  # Dla bezkolorowych kart
    else:
        return x.split(',')

df['colors'] = df['colors'].apply(convert_colors_to_list)
df['color_identity'] = df['color_identity'].apply(convert_colors_to_list)

# %% [markdown]
# # 4.4. Obliczenie 'num_colors'

# %%
df['num_colors'] = df['colors'].apply(len)

# %% [markdown]
# # 4.5. Konwersja kolumn 'supertypes' i 'types' do list, usunięcie 'subtypes'
# 

# %%
def convert_to_list(x):
    if pd.isnull(x) or x == '':
        return []
    else:
        return x.split(',')

df['supertypes'] = df['supertypes'].apply(convert_to_list)
df['types'] = df['types'].apply(convert_to_list)

# Usunięcie kolumny 'subtypes'
df.drop('subtypes', axis=1, inplace=True)

# %% [markdown]
# # 4.6. One-hot encoding dla 'supertypes' i 'types'

# %%
# One-hot encoding dla 'supertypes'
supertypes_set = set()
for st_list in df['supertypes']:
    supertypes_set.update(st_list)

for supertype in supertypes_set:
    if supertype != '':
        df[f'supertype_{supertype}'] = df['supertypes'].apply(lambda x: 1 if supertype in x else 0)

# One-hot encoding dla 'types'
types_set = set()
for t_list in df['types']:
    types_set.update(t_list)

for typ in types_set:
    if typ != '':
        df[f'type_{typ}'] = df['types'].apply(lambda x: 1 if typ in x else 0)

# %% [markdown]
# # 4.7. Generowanie kodów dla 'colors' i 'color_identity'
# 

# %%
def get_code(colors_list):
    sorted_colors = sorted(colors_list)
    code = ''.join(sorted_colors)
    return code

df['colors_code'] = df['colors'].apply(get_code)
df['color_identity_code'] = df['color_identity'].apply(get_code)

# %% [markdown]
# # 4.8. Tworzenie mapowań i kodowanie 'colors_code' i 'color_identity_code'

# %%
def create_mapping_and_encode(column_name):
    unique_codes = df[column_name].unique()
    code_mapping = {code: idx for idx, code in enumerate(unique_codes)}
    # Zapisanie mapowania do pliku
    mapping_filename = f'{column_name}_mapping.txt'
    with open(mapping_filename, 'w') as f:
        for code, idx in code_mapping.items():
            f.write(f'{idx}: {code}\n')
    # Kodowanie wartości w DataFrame
    df[f'{column_name}_encoded'] = df[column_name].map(code_mapping)
    return code_mapping

# Tworzenie mapowań i kodowanie
colors_code_mapping = create_mapping_and_encode('colors_code')
color_identity_code_mapping = create_mapping_and_encode('color_identity_code')

# %% [markdown]
# # 4.9. Konwersja 'cmc' i 'num_colors' do typu całkowitego

# %%
df['cmc'] = df['cmc'].astype(int)
df['num_colors'] = df['num_colors'].astype(int)

# %% [markdown]
# # 4.10. Mapowanie 'rarity' na wartości numeryczne
# 

# %%
rarity_mapping = {'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3, 'special': 4, 'bonus': 5}
df['rarity_numeric'] = df['rarity'].map(rarity_mapping)

# %% [markdown]
# # **5. Eksploracja i wizualizacja danych**
# 

# %% [markdown]
# # 5.1. Histogram 'cmc'
# 

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
# # 5.2. Wykres słupkowy 'num_colors'
# 

# %%
plt.figure(figsize=(10, 6))
sns.countplot(x='num_colors', data=df)
plt.title('Liczba kolorów kart')
plt.xlabel('Liczba kolorów')
plt.ylabel('Liczba kart')
plt.show()

# %% [markdown]
# # 5.3. Wykres słupkowy 'year'
# 

# %%
plt.figure(figsize=(14, 6))
sns.countplot(x='year', data=df)
plt.xticks(rotation=90)
plt.title('Rozkład roku wydania')
plt.xlabel('Rok')
plt.ylabel('Liczba kart')
plt.tight_layout()
plt.show()

# %% [markdown]
# # 5.4. Wykres słupkowy kombinacji kolorów w 'color_identity_code'
# 

# %%

color_combination_counts = df['color_identity_code'].value_counts()

plt.figure(figsize=(14, 8))
sns.barplot(x=color_combination_counts.index, y=color_combination_counts.values)
plt.title('Rozkład kombinacji kolorów')
plt.xlabel('Kombinacja kolorów')
plt.ylabel('Liczba kart')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()


# %% [markdown]
# # 5.5. Wykres słupkowy 'supertypes'
# 

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
# # 5.6. Wykres słupkowy 'types'
# 

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
# # 5.7. Wykres słupkowy 'rarity'
# 

# %%
rarity_counts = df['rarity'].value_counts()
rarity_order = ['common', 'uncommon', 'rare', 'mythic', 'special', 'bonus']
rarity_counts = rarity_counts.reindex(rarity_order)

plt.figure(figsize=(8, 6))
sns.barplot(x=rarity_counts.index, y=rarity_counts.values, palette='viridis')
plt.title('Rozkład rzadkości kart')
plt.xlabel('Rzadkość')
plt.ylabel('Liczba kart')
plt.show()

# %% [markdown]
# # 5.8 Wykres pudełkowy 'cmc'

# %%
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['cmc'])
plt.title('Box Plot of cmc')
plt.show()

# %% [markdown]
# # 5.9 Wykres pudełkowy 'num_colors'

# %%
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['num_colors'])
plt.title('Box Plot of Number of Colors')
plt.show()

# %% [markdown]
# # 5.10 Wykres pudełkowy 'text_length'

# %%
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['text_length'])
plt.title('Box Plot of Text Length')
plt.show()

# %% [markdown]
# # 5.11 Wykres pudełkowy 'color_identity_code'

# %%
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['color_identity_code_encoded'])
plt.title('Box Plot of Lolor Identity Code')
plt.show()

# %% [markdown]
# # 5.8 Generowanie macierzy korelacji #

# %%
numerical_cols = ['cmc', 'num_colors', 'text_length', 'rarity_numeric', 'year', 'num_types', 'color_identity_code_encoded', 'colors_code_encoded']

corr_matrix = df[numerical_cols].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='viridis')
plt.title('Correlation Matrix')
plt.xticks(rotation=45)
plt.show()


# %% [markdown]
# # **6. Podział danych na zbiory treningowe i testowe**
# 

# %%
columns_to_drop = ['image_paths', 'colors', 'color_identity', 'colors_code', 'color_identity_code',
                   'supertypes', 'types', 'rarity']
df.drop(columns=columns_to_drop, inplace=True)

train_df, test_df = train_test_split(df, test_size=0.3, random_state=42, stratify=df['rarity_numeric'])

print(f"Liczba kart w zbiorze treningowym: {len(train_df)}")
print(f"Liczba kart w zbiorze do doszkalania: {len(test_df)}")

# %% [markdown]
# # **7. Wyświetlenie przykładowego obrazu karty**

# %%
sample_image_path = train_df.iloc[1]['image_path']
image = Image.open(sample_image_path)
plt.figure(figsize=(6, 8))
plt.imshow(image)
plt.axis('off')
plt.show()

# %% [markdown]
# # **8. Zapisanie przetworzonych danych**

# %% [markdown]
# ## 8.1 Zapis plików ##

# %%
datasets_dir = 'datasets'

if not os.path.exists(datasets_dir):
    os.makedirs(datasets_dir)


df.to_csv(PROCESSED_DATASET_PATH, index=False)
train_df.to_csv(TRAIN_DATASET_PATH, index=False)
test_df.to_csv(TEST_DATASET_PATH, index=False)

# %% [markdown]
# # 9. Generowanie raportu

# %%

profile = ProfileReport(df, title="Raport EDA dla zbioru danych", explorative=True)

profile.to_notebook_iframe()

profile.to_file(EDA_REPORT_PATH)



