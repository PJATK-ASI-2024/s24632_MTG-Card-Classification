import os
import re
import json
import ijson
import pandas as pd
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Katalogi do zapisu 
log_dir = "logs"
cards_dir = "cards"
data_dir = "data"
dataset_dir = "datasets"

# Tworzenie katalogu jeżeli jeszcze ich nie ma
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
if not os.path.exists(dataset_dir):
    os.makedirs(dataset_dir)

# Konfiguracja loggera
logging.basicConfig(
    filename=os.path.join(log_dir, 'process_cards.log'),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    encoding='utf-8'
)


# Ścieżki do plików
json_file_path = os.path.join(data_dir, 'data/default-cards.json')  
mtg_types_file = os.path.join(data_dir, 'data/mtg_types.json')  

# Wczytaj listy z pliku mtg_types.json
with open(mtg_types_file, 'r', encoding='utf-8') as f:
    mtg_types = json.load(f)

supertypes_list = mtg_types['supertypes']
types_list = mtg_types['types']
subtypes_dict = mtg_types['subtypes']

# Funkcja parsująca pole type_line
def parse_type_line(type_line):
    
    # Zastąpienie wszystkich rodzajów myślników standardowym em dashem z odstępami
    type_line = re.sub(r'\s*[-–—]\s*', ' — ', type_line.strip())
    
    # Obsługa kart podzielonych (split cards) z '//' w type_line
    parts = re.split(r'\s*//\s*', type_line)
    supertypes = []
    types = []
    subtypes = []
    
    for part in parts:
        # Podział na część przed i po myślniku
        if '—' in part:
            pre_dash, post_dash = map(str.strip, part.split('—', 1))
        else:
            pre_dash = part.strip()
            post_dash = ''
        
        
        # Inicjalizacja tymczasowych list dla aktualnej części
        temp_supertypes = []
        temp_types = []
        temp_subtypes = []
        
        # Podział części przed myślnikiem na słowa
        words = pre_dash.split()
        
        # Rozpoznawanie supertypów i typów
        for word in words:
            if word in supertypes_list:
                temp_supertypes.append(word)
            elif word in types_list:
                temp_types.append(word)
            else:
                logging.debug(f"Nierozpoznane słowo w supertypach lub typach: {word}")
        
        # Przetwarzanie subtypów tylko jeśli istnieje post_dash
        if post_dash:
            subtype_words = post_dash.split()
            idx = 0
            while idx < len(subtype_words):
                word = subtype_words[idx]
                # Sprawdzamy, czy następne słowo tworzy dwuwyrazowy subtyp
                if idx + 1 < len(subtype_words):
                    two_word_subtype = f"{word} {subtype_words[idx + 1]}"
                    found = False
                    for subtype_list in subtypes_dict.values():
                        if two_word_subtype in subtype_list:
                            temp_subtypes.append(two_word_subtype)
                            idx += 2
                            found = True
                            break
                    if found:
                        continue
                # Sprawdzamy pojedyncze słowo
                found = False
                for subtype_list in subtypes_dict.values():
                    if word in subtype_list:
                        temp_subtypes.append(word)
                        found = True
                        break
                if not found:
                    logging.debug(f"Nierozpoznane słowo w subtypach: {word}")
                idx += 1
        else:
            # Brak subtypów do przetworzenia
            pass
        
        # Dodajemy tymczasowe listy do głównych list, unikając duplikatów
        supertypes.extend([st for st in temp_supertypes if st not in supertypes])
        types.extend([t for t in temp_types if t not in types])
        subtypes.extend([st for st in temp_subtypes if st not in subtypes])
    
    return supertypes, types, subtypes


# Funkcja do przetwarzania jednej karty
def process_card(card):
    if card.get('lang', '') != 'en' or card.get('layout', '') == "art_series":
        return None  # Pomijamy karty w innym języku

    try:
        card_name = card['name']
        set_code = card.get('set', 'unknown_set')
        collector_number = card.get('collector_number', 'unknown_number')

        # Zamiana niedozwolonych znaków w nazwie karty
        safe_card_name = ''.join(c for c in card_name if c.isalnum() or c in (' ', '_', '-', '★')).rstrip()

        # Ścieżka do folderu z nazwą karty
        card_dir = os.path.join(cards_dir, safe_card_name)

        # Inicjalizacja listy ścieżek do obrazów
        image_paths = []

        if 'image_uris' in card:
            # Karta jednostronna
            image_uris = card['image_uris']
            # Wyodrębnienie rozszerzenia pliku
            if 'normal' in image_uris:
                image_url = image_uris['normal']
                file_extension = os.path.splitext(image_url)[1].split('?')[0]
            else:
                file_extension = '.jpg'

            file_name = f"{set_code}_{collector_number}{file_extension}"
            image_path = os.path.join(card_dir, file_name)
            image_paths.append(image_path)

        elif 'card_faces' in card:
            # Karta dwustronna
            face_number = 1
            for face in card['card_faces']:
                face_name = face.get('name', f'face{face_number}')
                safe_face_name = ''.join(c for c in face_name if c.isalnum() or c in (' ', '_', '-', '★')).rstrip()

                if 'image_uris' in face:
                    image_uris = face['image_uris']
                    if 'normal' in image_uris:
                        image_url = image_uris['normal']
                        file_extension = os.path.splitext(image_url)[1].split('?')[0]
                    else:
                        file_extension = '.jpg'

                    file_name = f"{set_code}_{collector_number}_{safe_face_name}{file_extension}"
                    image_path = os.path.join(card_dir, file_name)
                    image_paths.append(image_path)
                else:
                    logging.warning(f"Karta '{card_name}' - Strona '{face_name}' nie posiada 'image_uris'.")
                face_number += 1
        else:
            logging.warning(f"Karta '{card_name}' nie posiada 'image_uris' ani 'card_faces'.")
            return None

        # Usunięcie duplikatów ścieżek
        image_paths = list(set(image_paths))

        # Sprawdzenie, czy pliki istnieją
        existing_image_paths = []
        for img_path in image_paths:
            if os.path.exists(img_path):
                existing_image_paths.append(img_path)
            else:
                logging.warning(f"Plik obrazu nie istnieje: {img_path}")

        if not existing_image_paths:
            logging.warning(f"Brak istniejących obrazów dla karty '{card_name}'.")
            return None

        cmc = card.get('cmc', 0)
        collector_number = card.get('collector_number', 0)
        color_identity = card.get('color_identity', [])
        colors = card.get('colors', [])
        num_colors = len(colors)
        year = int(card.get('released_at', '2000-01-01')[:4])
        type_line = card.get('type_line', '')
        num_types = len(type_line.split('—')[0].strip().split(' '))
        text_length = len(card.get('oracle_text', '').split())
        rarity = card.get('rarity', '')

        # Parsowanie type_line
        supertypes, types, subtypes = parse_type_line(type_line)

        # Przygotowanie danych
        data = {
            'image_paths': ';'.join(existing_image_paths),
            'cmc': cmc,
            'collector_number': collector_number,
            'num_colors': num_colors,
            'colors': ','.join(colors),
            'year': year,
            'num_types': num_types,
            'text_length': text_length,
            'color_identity': ','.join(color_identity),
            'rarity': rarity,
            'supertypes': ','.join(supertypes),
            'types': ','.join(types),
            'subtypes': ','.join(subtypes)
        }

        return data
    except Exception as e:
        logging.error(f"Błąd podczas przetwarzania karty {card.get('name', 'Nieznana')}: {str(e)}")
        return None

# Główna funkcja przetwarzania
def main():
    # Lista do przechowywania danych przetworzonych kart
    data_list = []

    # Liczenie całkowitej liczby kart do przetworzenia
    total_cards = 0
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        objects = ijson.items(json_file, 'item')
        for card in objects:
            if card.get('lang', '') == 'en':
                total_cards += 1

    # Przetwarzanie kart
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        objects = ijson.items(json_file, 'item')

        # Ustawienie paska postępu
        pbar = tqdm(total=total_cards, desc='Przetwarzanie kart', unit='karta')

        # Użycie ThreadPoolExecutor do wielowątkowości
        max_workers = 20
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for card in objects:
                if card.get('lang', '') != 'en':
                    continue
                # Przekazujemy kopię karty do funkcji
                future = executor.submit(process_card, card)
                futures.append(future)

            # Gdy zadania się zakończą, zbieramy wyniki
            for future in as_completed(futures):
                result = future.result()
                if result:
                    data_list.append(result)
                pbar.update(1)

        pbar.close()

    # Tworzenie DataFrame i zapis do CSV
    if data_list:
        df = pd.DataFrame(data_list)
        df.to_csv(os.path.join(dataset_dir,'cards_metadata.csv'), index=False)
        logging.info("Pomyślnie zapisano cards_metadata.csv")
    else:
        logging.error("Brak danych do zapisania.")

if __name__ == '__main__':
    main()
