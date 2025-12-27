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

## Weitere Pfade hinzufügen

1. Pfad in der `.env` als neuen Eintrag hinzufügen
2. Den Eintrag im Service `indexer` unter `volumes` eintragen:

```yaml
volumes:
  - ${NEUER_PFAD}:/data/neuer_pfad  # Hier neue Pfade hinzufügen
```

## Unterstützte Formate

- **Dokumente**: PDF, DOCX, DOC, TXT, MD, ODT, RTF
- **Audio**: MP3, WAV, FLAC, M4A (Metadaten via ExifTool)

## Nützliche Befehle

```bash
# Services stoppen
docker compose down

# Daten löschen
sudo rm -rf meili_data/*

# Alles neu bauen
docker compose up -d --build

# Logs anzeigen
docker compose logs -f indexer

# Neu indexieren
docker compose restart indexer

# Content-Feld im Dashboard ausblenden
curl -X PATCH 'http://localhost:7700/indexes/files/settings' \
  -H "Authorization: Bearer dein-master-key" \
  -H 'Content-Type: application/json' \
  --data-binary '{
    "displayedAttributes": ["id", "filename", "path", "type", "preview"]
  }'
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
├── .env.example
├── README.md
├── scripts/
│   ├── Dockerfile
│   └── indexer.py
└── meili_data/
```

---
