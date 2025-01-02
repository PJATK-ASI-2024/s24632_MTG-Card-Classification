# data_processing_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer

# Załaduj zmienne środowiskowe
load_dotenv()

# Ścieżki do danych i raportów
DATASETS_DIR_PATH = os.getenv("DATASETS_DIR_PATH","datasets")
REPORTS_DIR_PATH = os.getenv("REPORTS_DIR_PATH", "reports")
VISUALIZATIONS_DIR_PATH = os.getenv("VISUALIZATIONS_DIR_PATH","visualizations")

Path(REPORTS_DIR_PATH).mkdir(parents=True, exist_ok=True)
Path(DATASETS_DIR_PATH).mkdir(parents=True, exist_ok=True)
Path(VISUALIZATIONS_DIR_PATH).mkdir(parents=True, exist_ok=True)

def load_data():
    """
    Wczytuje surowe dane z pliku CSV.
    """
    raw_data_path = os.path.join(DATASETS_DIR_PATH, 'cards_metadata.csv')
    df = pd.read_csv(raw_data_path)
    # Możesz zapisać surowe dane, jeśli to konieczne
    # df.to_csv(os.path.join(DATASETS_DIR_PATH, 'raw_data.csv'), index=False)
    print("Surowe dane zostały wczytane.")

def preprocess_data():
    """
    Przeprowadza przetwarzanie danych zgodnie z dostarczonym skryptem.
    """
    raw_data_path = os.path.join(DATASETS_DIR_PATH, 'cards_metadata.csv')
    df = pd.read_csv(raw_data_path)
    
    # Usunięcie kart z 'cmc' > 20
    df = df[df['cmc'] <= 20]
    
    # Przetwarzanie kolumny 'image_paths' do 'image_path'
    df['image_path'] = df['image_paths'].apply(lambda x: x.split(';')[0] if pd.notnull(x) else '')
    
    # Usunięcie wierszy z pustymi ścieżkami do obrazów
    df = df[df['image_path'] != '']
    
    # Usunięcie wierszy z brakującymi wartościami w kluczowych kolumnach
    df.dropna(subset=['cmc', 'year', 'rarity'], inplace=True)
    
    # Konwersja kolumn 'colors' i 'color_identity' do list
    def convert_colors_to_list(x):
        if pd.isnull(x) or x == '':
            return []
        else:
            return x.split(',')
    
    df['colors'] = df['colors'].apply(convert_colors_to_list)
    df['color_identity'] = df['color_identity'].apply(convert_colors_to_list)
    
    # Obliczenie 'num_colors'
    df['num_colors'] = df['colors'].apply(len)
    
    # Konwersja kolumn 'supertypes' i 'types' do list
    def convert_to_list(x):
        if pd.isnull(x) or x == '':
            return []
        else:
            return x.split(',')
    
    df['supertypes'] = df['supertypes'].apply(convert_to_list)
    df['types'] = df['types'].apply(convert_to_list)
    
    # Obliczenie 'num_supertypes' i 'num_types'
    df['num_supertypes'] = df['supertypes'].apply(len)
    df['num_types'] = df['types'].apply(len)
    
    # One-Hot Encoding dla 'colors', 'color_identity', 'types' i 'supertypes'
    mlb_colors = MultiLabelBinarizer()
    colors_encoded = pd.DataFrame(mlb_colors.fit_transform(df['colors']), 
                                  columns=['color_' + c for c in mlb_colors.classes_], 
                                  index=df.index)
    df = pd.concat([df, colors_encoded], axis=1)
    
    mlb_color_identity = MultiLabelBinarizer()
    color_identity_encoded = pd.DataFrame(mlb_color_identity.fit_transform(df['color_identity']), 
                                         columns=['color_identity_' + c for c in mlb_color_identity.classes_], 
                                         index=df.index)
    df = pd.concat([df, color_identity_encoded], axis=1)
    
    mlb_types = MultiLabelBinarizer()
    types_encoded = pd.DataFrame(mlb_types.fit_transform(df['types']), 
                                 columns=['type_' + t for t in mlb_types.classes_], 
                                 index=df.index)
    df = pd.concat([df, types_encoded], axis=1)
    
    mlb_supertypes = MultiLabelBinarizer()
    supertypes_encoded = pd.DataFrame(mlb_supertypes.fit_transform(df['supertypes']), 
                                     columns=['supertype_' + st for st in mlb_supertypes.classes_], 
                                     index=df.index)
    df = pd.concat([df, supertypes_encoded], axis=1)
    
    # Konwersja 'cmc' i 'num_colors' do typu całkowitego
    # Jeśli 'cmc' powinien być float, usuń poniższą linię lub przekształć inaczej
    # df['cmc'] = df['cmc'].astype(int)
    df['num_colors'] = df['num_colors'].astype(int)
    
    # Mapowanie 'rarity' na wartości numeryczne
    rarity_mapping = {'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3, 'special': 4, 'bonus': 5}
    df['rarity_numeric'] = df['rarity'].map(rarity_mapping)
    
    # Usunięcie oryginalnych kolumn po encodingu
    columns_to_drop = ['image_paths', 'colors', 'color_identity', 'types', 'supertypes', 'rarity']
    df.drop(columns=columns_to_drop, inplace=True)
    
    # Zapisanie przetworzonych danych
    processed_data_path = os.path.join(DATASETS_DIR_PATH, 'processed_data.csv')
    df.to_csv(processed_data_path, index=False)
    print("Dane zostały przetworzone i zapisane jako processed_data.csv")

def generate_plots():
    """
    Generuje podstawowe wykresy EDA.
    """
    processed_data_path = os.path.join(DATASETS_DIR_PATH, 'processed_data.csv')
    df = pd.read_csv(processed_data_path)
    
    sns.set_theme(style='whitegrid', palette='muted', font_scale=1.2)
    
    # Histogram 'cmc'
    plt.figure(figsize=(12, 6))
    sns.histplot(
        df['cmc'], 
        bins=np.arange(df['cmc'].min(), df['cmc'].max() + 2, 1),  # Użycie np.arange z krokiem 1
        kde=False, 
        edgecolor='black'
    )
    plt.title('Rozkład cmc')
    plt.xlabel('cmc (Converted Mana Cost)')
    plt.ylabel('Liczba kart')
    plt.xticks(range(int(df['cmc'].min()), int(df['cmc'].max()) + 1))
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'histogram_cmc.png'))
    plt.close()
    
    # Wykres słupkowy liczby wystąpień każdego koloru w 'colors'
    color_columns = [col for col in df.columns if col.startswith('color_')]
    color_counts = df[color_columns].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x=color_counts.index.str.replace('color_', ''), y=color_counts.values)
    plt.title('Częstość występowania kolorów')
    plt.xlabel('Kolor')
    plt.ylabel('Liczba kart')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'barplot_colors.png'))
    plt.close()
    
    # Wykres słupkowy liczby wystąpień każdego koloru w 'color_identity'
    color_identity_columns = [col for col in df.columns if col.startswith('color_identity_')]
    color_identity_counts = df[color_identity_columns].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x=color_identity_counts.index.str.replace('color_identity_', ''), y=color_identity_counts.values)
    plt.title('Częstość występowania kolorów w identyfikacji kolorów')
    plt.xlabel('Color Identity')
    plt.ylabel('Liczba kart')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'barplot_color_identity.png'))
    plt.close()
    
    # Wykres słupkowy 'num_colors'
    plt.figure(figsize=(10, 6))
    sns.countplot(x='num_colors', data=df)
    plt.title('Liczba kolorów kart')
    plt.xlabel('Liczba kolorów')
    plt.ylabel('Liczba kart')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'countplot_num_colors.png'))
    plt.close()
    
    # Wykres słupkowy 'num_types'
    plt.figure(figsize=(10, 6))
    sns.countplot(x='num_types', data=df)
    plt.title('Liczba typów kart')
    plt.xlabel('Liczba typów')
    plt.ylabel('Liczba kart')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'countplot_num_types.png'))
    plt.close()
    
    # Wykres słupkowy 'num_supertypes'
    plt.figure(figsize=(10, 6))
    sns.countplot(x='num_supertypes', data=df)
    plt.title('Liczba supertypów kart')
    plt.xlabel('Liczba supertypów')
    plt.ylabel('Liczba kart')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'countplot_num_supertypes.png'))
    plt.close()
    
    # Wykres słupkowy 'types'
    type_columns = [col for col in df.columns if col.startswith('type_')]
    type_counts = df[type_columns].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(14, 6))
    sns.barplot(x=type_counts.index.str.replace('type_', ''), y=type_counts.values)
    plt.title('Rozkład types')
    plt.xlabel('Types')
    plt.ylabel('Liczba kart')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'barplot_types.png'))
    plt.close()
    
    # Wykres słupkowy 'supertypes'
    supertype_columns = [col for col in df.columns if col.startswith('supertype_')]
    supertype_counts = df[supertype_columns].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=supertype_counts.index.str.replace('supertype_', ''), y=supertype_counts.values)
    plt.title('Rozkład supertypes')
    plt.xlabel('Supertypes')
    plt.ylabel('Liczba kart')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'barplot_supertypes.png'))
    plt.close()
    
    # Wykres słupkowy 'rarity_numeric'
    rarity_counts = df['rarity_numeric'].value_counts().sort_index()
    rarity_labels = ['common', 'uncommon', 'rare', 'mythic', 'special', 'bonus']
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x=rarity_counts.index, y=rarity_counts.values, palette='viridis')
    plt.title('Rozkład rzadkości kart')
    plt.xlabel('Rarity Numeric')
    plt.ylabel('Liczba kart')
    plt.xticks(ticks=rarity_counts.index, labels=rarity_labels)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'barplot_rarity_numeric.png'))
    plt.close()
    
    # Wykres pudełkowy 'cmc'
    plt.figure(figsize=(8, 6))
    sns.boxplot(x=df['cmc'])
    plt.title('Box Plot of cmc')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'boxplot_cmc.png'))
    plt.close()
    
    # Wykres pudełkowy 'num_colors'
    plt.figure(figsize=(8, 6))
    sns.boxplot(x=df['num_colors'])
    plt.title('Box Plot of Number of Colors')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'boxplot_num_colors.png'))
    plt.close()
    
    # Wykres pudełkowy 'text_length'
    plt.figure(figsize=(8, 6))
    sns.boxplot(x=df['text_length'])
    plt.title('Box Plot of Text Length')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'boxplot_text_length.png'))
    plt.close()
    
    # Generowanie macierzy korelacji
    numerical_cols = ['cmc', 'num_colors', 'text_length', 'year', 'num_types', 'num_supertypes', 'rarity_numeric']
    color_columns = [col for col in df.columns if col.startswith('color_')]
    color_identity_columns = [col for col in df.columns if col.startswith('color_identity_')]
    type_columns = [col for col in df.columns if col.startswith('type_')]
    supertype_columns = [col for col in df.columns if col.startswith('supertype_')]
    
    corr_matrix = df[numerical_cols + color_columns + color_identity_columns + type_columns + supertype_columns].corr()
    
    plt.figure(figsize=(20, 16))
    sns.heatmap(corr_matrix, cmap='viridis', annot=True, fmt=".2f")
    plt.title('Correlation Matrix')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR_PATH, 'correlation_matrix.png'))
    plt.close()
    
    print("Wykresy EDA zostały wygenerowane i zapisane w folderze reports.")

def split_data():
    """
    Dzieli dane na zbiory treningowy i testowy oraz zapisuje je do plików CSV.
    """
    processed_data_path = os.path.join(DATASETS_DIR_PATH, 'processed_data.csv')
    df = pd.read_csv(processed_data_path)
    
    train_df, test_df = train_test_split(df, test_size=0.3, random_state=42, stratify=df['rarity_numeric'])
    
    train_df.to_csv(os.path.join(DATASETS_DIR_PATH, 'train_df.csv'), index=False)
    test_df.to_csv(os.path.join(DATASETS_DIR_PATH, 'test_df.csv'), index=False)
    print(f"Liczba kart w zbiorze treningowym: {len(train_df)}")
    print(f"Liczba kart w zbiorze testowym: {len(test_df)}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    dag_id='data_processing_dag',
    default_args=default_args,
    description='DAG odpowiedzialny za przetwarzanie danych',
    schedule_interval=None,  # Ręczne uruchamianie
    start_date=days_ago(1),
    catchup=False,
) as dag:

    load_data_task = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
    )

    preprocess_data_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_data,
    )

    generate_plots_task = PythonOperator(
        task_id='generate_plots',
        python_callable=generate_plots,
    )

    split_data_task = PythonOperator(
        task_id='split_data',
        python_callable=split_data,
    )

    load_data_task >> preprocess_data_task  >> generate_plots_task >> split_data_task
