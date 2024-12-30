# Użyj oficjalnego obrazu Apache Airflow jako bazowego
FROM apache/airflow:2.7.1-python3.10

# Przejście na użytkownika root do instalacji zależności systemowych
USER root

# Aktualizacja pakietów i instalacja zależności systemowych
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Przełączenie na użytkownika airflow
USER airflow

# Aktualizacja pip
RUN pip install --upgrade pip

# Instalacja wymaganych pakietów
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Skopiowanie reszty plików projektu
COPY --chown=airflow: . /opt/airflow/

# Ustawienie katalogu roboczego
WORKDIR /opt/airflow