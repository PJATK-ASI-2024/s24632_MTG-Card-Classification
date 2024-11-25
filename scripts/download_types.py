import requests
import json
import os
from dotenv import load_dotenv

# Załaduj zmienne z pliku .env
load_dotenv()

# Ścieżki do katalogów
DATA_DIR_PATH = os.getenv("DATA_DIR_PATH")
TYPES_DICT_PATH = os.getenv("TYPES_DICT_PATH")

# Scieżki do plików
BULK_DATA_PATH = os.getenv("BULK_DATA_PATH")

if not os.path.exists(DATA_DIR_PATH):
    os.makedirs(DATA_DIR_PATH)

# Endpointy API Scryfall
endpoints = {
    'supertypes': 'https://api.scryfall.com/catalog/supertypes',
    'types': 'https://api.scryfall.com/catalog/card-types',
    'artifact-types': 'https://api.scryfall.com/catalog/artifact-types',
    'battle-types': 'https://api.scryfall.com/catalog/battle-types',
    'creature-types': 'https://api.scryfall.com/catalog/creature-types',
    'enchantment-types': 'https://api.scryfall.com/catalog/enchantment-types',
    'land-types': 'https://api.scryfall.com/catalog/land-types',
    'planeswalker-types': 'https://api.scryfall.com/catalog/planeswalker-types',
    'spell-types': 'https://api.scryfall.com/catalog/spell-types'
}

# Słownik do przechowywania danych
mtg_types = {
    'supertypes': [],
    'types': [],
    'subtypes': {}
}

# Pobieranie supertypów
response = requests.get(endpoints['supertypes'])
if response.status_code == 200:
    data = response.json()
    mtg_types['supertypes'] = data.get('data', [])
else:
    print("Błąd podczas pobierania supertypów")

# Pobieranie typów kart
response = requests.get(endpoints['types'])
if response.status_code == 200:
    data = response.json()
    mtg_types['types'] = data.get('data', [])
else:
    print("Błąd podczas pobierania typów kart")

# Pobieranie subtypów dla różnych typów kart
subtype_categories = ['artifact-types', 'battle-types', 'creature-types', 'enchantment-types', 'land-types', 'planeswalker-types', 'spell-types']

for category in subtype_categories:
    response = requests.get(endpoints[category])
    if response.status_code == 200:
        data = response.json()
        subtype_list = data.get('data', [])
        # Mapowanie nazw kategorii na klucze w pliku JSON
        if category == 'artifact-types':
            key = 'Artifact'
        elif category == 'battle-types':
            key = 'Battle'
        elif category == 'creature-types':
            key = 'Creature'
        elif category == 'enchantment-types':
            key = 'Enchantment'
        elif category == 'land-types':
            key = 'Land'
        elif category == 'planeswalker-types':
            key = 'Planeswalker'
        elif category == 'spell-types':
            # 'spell-types' obejmuje zarówno 'Instant', jak i 'Sorcery'
            # Pobierz subtypy dla obu typów
            key_instant = 'Instant'
            key_sorcery = 'Sorcery'
            mtg_types['subtypes'][key_instant] = subtype_list
            mtg_types['subtypes'][key_sorcery] = subtype_list
            continue  # Przejdź do następnej kategorii
        else:
            key = category
        mtg_types['subtypes'][key] = subtype_list
    else:
        print(f"Błąd podczas pobierania subtypów dla kategorii {category}")

# Zapis do pliku mtg_types.json
with open(TYPES_DICT_PATH, 'w', encoding='utf-8') as f:
    json.dump(mtg_types, f, ensure_ascii=False, indent=2)

print("Plik mtg_types.json został pomyślnie wygenerowany.")
