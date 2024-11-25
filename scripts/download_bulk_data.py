import requests
import json
import os
from dotenv import load_dotenv

# Załaduj zmienne z pliku .env
load_dotenv()
DATA_DIR_PATH = os.getenv("DATA_DIR_PATH")
BULK_DATA_PATH = os.getenv("BULK_DATA_PATH")

if not os.path.exists(DATA_DIR_PATH):
    os.makedirs(DATA_DIR_PATH)

def download_default_cards():
    # Endpoint do pobrania informacji o danych masowych
    bulk_data_url = "https://api.scryfall.com/bulk-data"

    try:
        # Pobierz listę dostępnych danych masowych
        response = requests.get(bulk_data_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print(f"Błąd HTTP: {errh}")
        return
    except requests.exceptions.ConnectionError as errc:
        print(f"Błąd połączenia: {errc}")
        return
    except requests.exceptions.Timeout as errt:
        print(f"Przekroczono czas połączenia: {errt}")
        return
    except requests.exceptions.RequestException as err:
        print(f"Błąd podczas żądania: {err}")
        return

    bulk_data = response.json()

    # Znajdź wpis dla 'default_cards'
    default_cards_entry = None
    for entry in bulk_data.get('data', []):
        if entry.get('type') == 'default_cards':
            default_cards_entry = entry
            break

    if not default_cards_entry:
        print("Nie znaleziono 'default_cards' w danych masowych")
        return

    download_uri = default_cards_entry.get('download_uri')
    if not download_uri:
        print("Brak 'download_uri' dla 'default_cards'")
        return

    print("Pobieranie danych 'default_cards'...")
    try:
        # Pobierz dane 'default_cards'
        download_response = requests.get(download_uri, stream=True)
        download_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print(f"Błąd HTTP podczas pobierania: {errh}")
        return
    except requests.exceptions.ConnectionError as errc:
        print(f"Błąd połączenia podczas pobierania: {errc}")
        return
    except requests.exceptions.Timeout as errt:
        print(f"Przekroczono czas połączenia podczas pobierania: {errt}")
        return
    except requests.exceptions.RequestException as err:
        print(f"Błąd podczas żądania pobierania: {err}")
        return

    # Zapisz dane do pliku
    with open(BULK_DATA_PATH, 'wb') as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Dane 'default_cards' zostały pobrane i zapisane jako {BULK_DATA_PATH}")


if __name__ == "__main__":
    download_default_cards()
