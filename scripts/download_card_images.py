import os
import json
import requests
import ijson
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Załaduj zmienne z pliku .env
load_dotenv()

# Ścieżki do plików
BULK_DATA_PATH = os.getenv("BULK_DATA_PATH")
DOWNLOAD_LOGS_PATH = os.getenv("DOWNLOAD_LOGS_PATH")

# Katalogi do zapisu 
CARDS_DIR_PATH = os.getenv("CARDS_DIR_PATH")
LOGS_DIR_PATH = os.getenv("LOGS_DIR_PATH")

# Tworzenie katalogów jeżeli jeszcze ich nie ma
if not os.path.exists(CARDS_DIR_PATH):
    os.makedirs(CARDS_DIR_PATH)
if not os.path.exists(LOGS_DIR_PATH):
    os.makedirs(LOGS_DIR_PATH)

# Konfiguracja loggera
logging.basicConfig(
    filename=DOWNLOAD_LOGS_PATH,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  
)
 
# Licznik przetworzonych kart
total_cards = 0

# Pierwsze przejście przez plik, aby policzyć liczbę kart do przetworzenia
with open(BULK_DATA_PATH, 'r', encoding='utf-8') as json_file:
    objects = ijson.items(json_file, 'item')
    for card in objects:
        if card.get('lang', '') == 'en' and card.get('layout', '') != "art_series":
            total_cards += 1

# Inicjalizacja liczników
success_count = 0
failure_count = 0
counts_per_size = {'small': 0, 'normal': 0, 'large': 0}

# Funkcja do pobierania obrazka jednej karty
def download_card_image(card):
    global success_count, failure_count
    card_name = card['name']
    if card.get('lang', '') != 'en' or card.get('layout', '') == "art_series":
        return (0, 0, None) 

    # Zamiana niedozwolonych znaków w nazwie folderu
    safe_card_name = ''.join(c for c in card_name if c.isalnum() or c in (' ', '_', '-')).rstrip()

    # Ścieżka do folderu z nazwą karty
    card_dir = os.path.join(CARDS_DIR_PATH, safe_card_name)

    # Tworzenie folderu dla karty, jeśli nie istnieje
    if not os.path.exists(card_dir):
        os.makedirs(card_dir)

    set_code = card.get('set', 'unknown_set')
    collector_number = card.get('collector_number', 'unknown_number')

    images_downloaded = 0
    images_failed = 0
    sizes_downloaded = []

    # Sprawdzenie, czy karta ma obrazki w 'image_uris'
    if 'image_uris' in card:
        image_url = None
        size_downloaded = None
        for size in ['small', 'normal', 'large']:
            if size in card['image_uris']:
                image_url = card['image_uris'][size]
                size_downloaded = size
                break  # Znaleziono dostępny rozmiar, przerywamy pętlę

        if image_url:
            # Logowanie URL-a obrazka
            logging.debug(f"Karta '{card_name}' - URL obrazka: {image_url} (rozmiar: {size_downloaded})")

            # Wyodrębnienie rozszerzenia pliku z URL
            file_extension = os.path.splitext(image_url)[1].split('?')[0]  # Usuwa parametry URL po '?'

            file_name = f"{set_code}_{collector_number}{file_extension}"

            # Ścieżka do pliku obrazka
            image_path = os.path.join(card_dir, file_name)

            # Sprawdzenie, czy plik już istnieje, aby uniknąć ponownego pobierania
            if not os.path.exists(image_path):
                try:
                    # Pobranie obrazka
                    response = requests.get(image_url, timeout=10)

                    if response.status_code == 200:
                        # Jeżeli obrazek jest większy niż 'small', skaluj go
                        if size_downloaded in ['normal', 'large']:
                            # Odczytaj obrazek z odpowiedzi
                            img = Image.open(BytesIO(response.content))
                            # Skaluj obrazek do 146x204
                            img = img.resize((146, 204), Image.ANTIALIAS)
                            # Zapisz obrazek do pliku
                            img.save(image_path)
                        else:
                            # Zapisanie obrazka do pliku bez skalowania
                            with open(image_path, 'wb') as img_file:
                                img_file.write(response.content)
                        logging.info(f"Pobrano obraz karty '{card_name}' jako '{file_name}' (rozmiar: {size_downloaded})")
                        images_downloaded += 1
                        sizes_downloaded.append(size_downloaded)
                    else:
                        error_msg = f"Błąd podczas pobierania obrazka dla karty '{card_name}': Status {response.status_code}"
                        logging.error(error_msg)
                        images_failed += 1
                except Exception as e:
                    error_msg = f"Błąd podczas pobierania obrazka dla karty '{card_name}': {str(e)}"
                    logging.error(error_msg)
                    images_failed += 1
            else:
                logging.info(f"Plik '{file_name}' już istnieje, pomijanie.")
                images_downloaded += 1
                sizes_downloaded.append(size_downloaded)
        else:
            logging.warning(f"Karta '{card_name}' nie posiada obrazu w dostępnych rozmiarach.")
            images_failed += 1
    # Sprawdzenie, czy karta ma 'card_faces' z 'image_uris'
    elif 'card_faces' in card:
        face_number = 1
        for face in card['card_faces']:
            face_name = face.get('name', f'face{face_number}')
            safe_face_name = ''.join(c for c in face_name if c.isalnum() or c in (' ', '_', '-')).rstrip()

            if 'image_uris' in face:
                image_url = None
                size_downloaded = None
                for size in ['small', 'normal', 'large']:
                    if size in face['image_uris']:
                        image_url = face['image_uris'][size]
                        size_downloaded = size
                        break  # Znaleziono dostępny rozmiar, przerywamy pętlę

                if image_url:
                    # Logowanie URL-a obrazka
                    logging.debug(f"Karta '{card_name}' - Face '{face_name}' - URL obrazka: {image_url} (rozmiar: {size_downloaded})")

                    # Wyodrębnienie rozszerzenia pliku z URL
                    file_extension = os.path.splitext(image_url)[1].split('?')[0]  # Usuwa parametry URL po '?'

                    file_name = f"{set_code}_{collector_number}_{safe_face_name}{file_extension}"

                    # Ścieżka do pliku obrazka
                    image_path = os.path.join(card_dir, file_name)

                    # Sprawdzenie, czy plik już istnieje, aby uniknąć ponownego pobierania
                    if not os.path.exists(image_path):
                        try:
                            # Pobranie obrazka
                            response = requests.get(image_url, timeout=10)

                            if response.status_code == 200:
                                # Jeżeli obrazek jest większy niż 'small', skaluj go
                                if size_downloaded in ['normal', 'large']:
                                    # Odczytaj obrazek z odpowiedzi
                                    img = Image.open(BytesIO(response.content))
                                    # Skaluj obrazek do 146x204
                                    img = img.resize((146, 204), Image.ANTIALIAS)
                                    # Zapisz obrazek do pliku
                                    img.save(image_path)
                                else:
                                    # Zapisanie obrazka do pliku bez skalowania
                                    with open(image_path, 'wb') as img_file:
                                        img_file.write(response.content)
                                logging.info(f"Pobrano obraz karty '{card_name}' - Strona '{face_name}' jako '{file_name}' (rozmiar: {size_downloaded})")
                                images_downloaded += 1
                                sizes_downloaded.append(size_downloaded)
                            else:
                                error_msg = f"Błąd podczas pobierania obrazka dla karty '{card_name}' - Strona '{face_name}': Status {response.status_code}"
                                logging.error(error_msg)
                                images_failed += 1
                        except Exception as e:
                            error_msg = f"Błąd podczas pobierania obrazka dla karty '{card_name}' - Strona '{face_name}': {str(e)}"
                            logging.error(error_msg)
                            images_failed += 1
                    else:
                        logging.info(f"Plik '{file_name}' już istnieje, pomijanie.")
                        images_downloaded += 1
                        sizes_downloaded.append(size_downloaded)
                else:
                    logging.warning(f"Karta '{card_name}' - Strona '{face_name}' nie posiada obrazu w dostępnych rozmiarach.")
                    images_failed += 1
            else:
                logging.warning(f"Karta '{card_name}' - Strona '{face_name}' nie posiada 'image_uris'.")
                images_failed += 1
            face_number += 1
    else:
        logging.warning(f"Karta '{card_name}' nie posiada 'image_uris' ani 'card_faces'.")
        images_failed += 1

    return (images_downloaded, images_failed, sizes_downloaded)

# Otwórz plik JSON ponownie do właściwego przetwarzania
with open(BULK_DATA_PATH, 'r', encoding='utf-8') as json_file:
    objects = ijson.items(json_file, 'item')

    # Lista zadań do wykonania
    tasks = []

    # Tworzymy pulę wątków
    max_workers = 25  # Zmniejszono liczbę wątków, aby uniknąć przeciążenia
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Użyj tqdm do wyświetlenia paska postępu
        with tqdm(total=total_cards, desc='Przetwarzanie kart', unit='kart') as pbar:
            for card in objects:
                if card.get('lang', '') != 'en' or card.get('layout', '') == "art_series":
                    continue
                # Dodajemy zadanie do puli
                future = executor.submit(download_card_image, card)
                tasks.append(future)

            # Iterujemy po zakończonych zadaniach
            for future in as_completed(tasks):
                images_downloaded, images_failed, sizes_downloaded = future.result()
                success_count += images_downloaded
                failure_count += images_failed
                for size in sizes_downloaded:
                    if size:
                        counts_per_size[size] += 1
                pbar.set_postfix({'Pobrano': f"{success_count}"})
                pbar.update(1)

# Generowanie raportu
report_file = 'raport.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("Raport pobierania kart\n")
    f.write("======================\n\n")
    f.write("+--------------------------------+---------+\n")
    f.write("| Metryka                        | Wartość |\n")
    f.write("+--------------------------------+---------+\n")
    f.write(f"| Liczba kart do przetworzenia   | {total_cards}       |\n")
    f.write(f"| Liczba obrazów pobranych       | {success_count}       |\n")
    f.write(f"| Liczba obrazów nieudanych      | {failure_count}       |\n")
    f.write("+--------------------------------+---------+\n\n")
    f.write("Obrazy pobrane w rozmiarach:\n")
    f.write("+---------+-------+\n")
    f.write("| Rozmiar | Ilość |\n")
    f.write("+---------+-------+\n")
    for size in ['small', 'normal', 'large']:
        f.write(f"| {size.ljust(7)} | {str(counts_per_size[size]).ljust(5)} |\n")
    f.write("+---------+-------+\n")

print("Raport został zapisany w pliku 'raport.txt'")
