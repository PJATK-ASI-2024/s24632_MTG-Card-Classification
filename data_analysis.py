import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from sklearn.model_selection import train_test_split
from collections import Counter

data_dir = "datasets"

# Ustawienie stylu wykresów
sns.set_theme(style='whitegrid', palette='muted', font_scale=1.2)

# Wczytanie zbioru danych z pliku CSV
df = pd.read_csv(os.path.join(data_dir, 'cards_metadata.csv'))

# Wyświetlenie przykładowych wierszy
print(df.sample(10))

# Sprawdzenie brakujących wartości w kolumnach
print("\nBrakujące wartości w każdej kolumnie:")
print(df.isnull().sum())

# Wyświetlenie statystyk opisowych
print("\nStatystyki opisowe:")
print(df.describe())

df = df[df['cmc'] <= 20]

df['image_path'] = df['image_paths'].apply(lambda x: x.split(';')[0] if pd.notnull(x) else '')

# Usunięcie wierszy z pustymi ścieżkami do obrazów
df = df[df['image_path'] != '']

# Sprawdzenie istnienia plików obrazów i usunięcie wierszy bez obrazów
df['image_exists'] = df['image_path'].apply(lambda x: os.path.exists(x))
df = df[df['image_exists']]
df.drop('image_exists', axis=1, inplace=True)

# Usunięcie wierszy z brakującymi wartościami w kluczowych kolumnach
df.dropna(subset=['cmc', 'year', 'rarity'], inplace=True)

def convert_colors_to_list(x):
    if pd.isnull(x) or x == '':
        return ['C']  # Dla bezkolorowych kart
    else:
        return x.split(',')

df['colors'] = df['colors'].apply(convert_colors_to_list)
df['color_identity'] = df['color_identity'].apply(convert_colors_to_list)

df['num_colors'] = df['colors'].apply(len)

def convert_to_list(x):
    if pd.isnull(x) or x == '':
        return []
    else:
        return x.split(',')

df['supertypes'] = df['supertypes'].apply(convert_to_list)
df['types'] = df['types'].apply(convert_to_list)

# Usunięcie kolumny 'subtypes'
df.drop('subtypes', axis=1, inplace=True)

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
        
def get_code(colors_list):
    sorted_colors = sorted(colors_list)
    code = ''.join(sorted_colors)
    return code

df['colors_code'] = df['colors'].apply(get_code)
df['color_identity_code'] = df['color_identity'].apply(get_code)

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

df['cmc'] = df['cmc'].astype(int)
df['num_colors'] = df['num_colors'].astype(int)

rarity_mapping = {'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3, 'special': 4, 'bonus': 5}
df['rarity_numeric'] = df['rarity'].map(rarity_mapping)

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

plt.figure(figsize=(10, 6))
sns.countplot(x='num_colors', data=df)
plt.title('Liczba kolorów kart')
plt.xlabel('Liczba kolorów')
plt.ylabel('Liczba kart')
plt.show()

plt.figure(figsize=(14, 6))
sns.countplot(x='year', data=df)
plt.xticks(rotation=90)
plt.title('Rozkład roku wydania')
plt.xlabel('Rok')
plt.ylabel('Liczba kart')
plt.tight_layout()
plt.show()


color_combination_counts = df['color_identity_code'].value_counts()

plt.figure(figsize=(14, 8))
sns.barplot(x=color_combination_counts.index, y=color_combination_counts.values)
plt.title('Rozkład kombinacji kolorów')
plt.xlabel('Kombinacja kolorów')
plt.ylabel('Liczba kart')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

supertype_columns = [col for col in df.columns if col.startswith('supertype_')]
supertype_counts = df[supertype_columns].sum().sort_values(ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x=supertype_counts.index.str.replace('supertype_', ''), y=supertype_counts.values)
plt.title('Rozkład supertypes')
plt.xlabel('Supertypes')
plt.ylabel('Liczba kart')
plt.xticks(rotation=45)
plt.show()

type_columns = [col for col in df.columns if col.startswith('type_')]
type_counts = df[type_columns].sum().sort_values(ascending=False)

plt.figure(figsize=(14, 6))
sns.barplot(x=type_counts.index.str.replace('type_', ''), y=type_counts.values)
plt.title('Rozkład types')
plt.xlabel('Types')
plt.ylabel('Liczba kart')
plt.xticks(rotation=45)
plt.show()

rarity_counts = df['rarity'].value_counts()
rarity_order = ['common', 'uncommon', 'rare', 'mythic', 'special', 'bonus']
rarity_counts = rarity_counts.reindex(rarity_order)

plt.figure(figsize=(8, 6))
sns.barplot(x=rarity_counts.index, y=rarity_counts.values, palette='viridis')
plt.title('Rozkład rzadkości kart')
plt.xlabel('Rzadkość')
plt.ylabel('Liczba kart')
plt.show()

train_df, test_df = train_test_split(df, test_size=0.3, random_state=42, stratify=df['rarity_numeric'])

print(f"Liczba kart w zbiorze treningowym: {len(train_df)}")
print(f"Liczba kart w zbiorze do doszkalania: {len(test_df)}")

sample_image_path = train_df.iloc[1]['image_path']
image = Image.open(sample_image_path)
plt.figure(figsize=(6, 8))
plt.imshow(image)
plt.axis('off')
plt.show()

columns_to_drop = ['image_paths', 'colors', 'color_identity', 'colors_code', 'color_identity_code',
                   'supertypes', 'types']
df.drop(columns=columns_to_drop, inplace=True)

datasets_dir = 'datasets'

if not os.path.exists(datasets_dir):
    os.makedirs(datasets_dir)


df.to_csv(os.path.join(datasets_dir,'processed_data.csv'), index=False)
train_df.to_csv(os.path.join(datasets_dir,'train_data.csv'), index=False)
test_df.to_csv(os.path.join(datasets_dir,'test_df.csv'), index=False)