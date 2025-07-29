# Dockerfile - Unsere eigene "Box" mit allem, was wir brauchen

# 1. Wir starten mit einem offiziellen, stabilen Python-Image
FROM python:3.11-slim

# 2. Wir setzen das Arbeitsverzeichnis in der Box
WORKDIR /app

# 3. Wir installieren die Systemabhängigkeiten (der entscheidende Schritt)
#    'apt-get update' aktualisiert die Paketliste
#    'apt-get install -y ffmpeg libasound2' installiert ffmpeg und die Audio-Bibliothek
#    '--no-install-recommends' spart Platz
#    'rm -rf /var/lib/apt/lists/*' räumt danach auf
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libasound2 && \
    rm -rf /var/lib/apt/lists/*

# 4. Wir kopieren die Liste der Python-Pakete in die Box
COPY requirements.txt .

# 5. Wir installieren die Python-Pakete
RUN pip install --no-cache-dir -r requirements.txt

# 6. Wir kopieren unseren gesamten restlichen Code in die Box
COPY . .

# 7. Wir sagen der Box, welcher Befehl beim Start ausgeführt werden soll
CMD ["python", "main.py"]
