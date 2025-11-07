# Meilisearch Dokumenten-Indexierung

Durchsuchbarer Index für lokale Dokumente (PDF, DOCX, MD, Audio-Metadaten) mit Meilisearch und Apache Tika.

## Schnellstart

### 1. .env Datei erstellen

Kopiere `.env.example` nach `.env` und passe die Werte an:

```bash
cp .env.example .env
nano .env
```

Trage ein:

```bash
MEILI_MASTER_KEY=dein-sicherer-key-hier
MD_FILES=/dein/erster/pfad
AUDIO_FILES=/dein/zweiter/pfad
```

Weitere Pfade müssen in der `.env` und in der `docker-compose.yml` eingefügt werden.

### 2. Starten

```bash
docker compose up -d
docker compose logs -f indexer
```

### 3. Dashboard öffnen

```
http://localhost:7700
```

Login mit deinem `MEILI_MASTER_KEY`.

## Unterstützte Formate

- **Dokumente**: PDF, DOCX, DOC, TXT, MD, ODT, RTF
- **Audio**: MP3, WAV, FLAC, M4A (Metadaten via ExifTool)

## Nützliche Befehle

```bash
# Logs anzeigen
docker compose logs -f indexer

# Neu indexieren
docker compose restart indexer

# Services stoppen
docker compose down

# Alles neu bauen
docker compose up -d --build
```

## Troubleshooting

**Keine Dateien gefunden?**

```bash
docker exec -it indexer ls -la /data
```

**Permission denied?**

```bash
chmod -R 755 /pfad/zu/dokumenten
```

**Index leer?**

```bash
docker compose logs indexer
```

## Projektstruktur

```
notes-index/
├── docker-compose.yml
├── .env
├── README.md
├── scripts/
│   ├── Dockerfile
│   └── indexer.py
└── meili_data/
```

---
