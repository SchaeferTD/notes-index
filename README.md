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
MEILI_VERSION=v1.24.0
MD_FILES=/dein/erster/pfad
AUDIO_FILES=/dein/zweiter/pfad
CLEANUP=false
```

| Variable | Beschreibung |
|----------|--------------|
| `MEILI_MASTER_KEY` | API-Key für Meilisearch |
| `MEILI_VERSION` | Meilisearch-Version (z.B. `v1.12.0`, default: `latest`) |
| `MD_FILES` | Pfad zu Markdown/Dokumenten |
| `AUDIO_FILES` | Pfad zu Audio-Dateien |
| `CLEANUP` | `true` = beim Start verwaiste Index-Einträge entfernen |

### 2. Starten

```bash
docker compose up -d
docker compose logs -f indexer
```

### 3. Such-UI öffnen

```
http://localhost:8080
```

Beim ersten Aufruf wird nach dem API-Key gefragt (wird im Browser gespeichert).

**Alternativ:** Meilisearch-Dashboard unter `http://localhost:7700` mit dem Master-Key.

## Weitere Pfade hinzufügen

1. Pfad in der `.env` als neuen Eintrag hinzufügen
2. Den Eintrag im Service `indexer` unter `volumes` eintragen:

```yaml
volumes:
  - ${NEUER_PFAD}:/data/neuer_pfad  # Hier neue Pfade hinzufügen
```

## Cleanup: Verwaiste Index-Einträge entfernen

Wenn Dateien gelöscht werden während der Indexer nicht läuft, bleiben verwaiste Einträge im Index zurück. Mit `CLEANUP=true` werden diese beim Start entfernt:

```bash
# In .env setzen:
CLEANUP=true

# Dann neu starten:
docker compose up -d --build
```

Nach dem Cleanup `CLEANUP=false` wieder setzen (oder weglassen), damit nicht bei jedem Start der gesamte Index geprüft wird.

**Hinweis:** Löschungen werden auch live erkannt, solange der Indexer läuft. Der Cleanup ist nur nötig, wenn Dateien gelöscht wurden während der Container gestoppt war.

## Unterstützte Formate

- **Dokumente**: PDF, DOCX, DOC, TXT, MD, ODT, RTF
- **Audio**: MP3, WAV, FLAC, M4A (Metadaten via ExifTool)

## Sicherheit

Die Such-UI ist für lokale Nutzung konzipiert. Für den Produktiveinsatz:

### Search-Only API-Key erstellen

Statt des Master-Keys einen eingeschränkten Key verwenden:

```bash
curl -X POST 'http://localhost:7700/keys' \
  -H 'Authorization: Bearer DEIN_MASTER_KEY' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "description": "Search-only key for web UI",
    "actions": ["search"],
    "indexes": ["files"],
    "expiresAt": null
  }'
```

### Meilisearch nur lokal erreichbar machen

In `docker-compose.yml` ändern:

```yaml
ports:
  - "127.0.0.1:7700:7700"  # statt 0.0.0.0
```

## Performance & Ressourcen

### Memory-Limit

Meilisearch ist auf 512MB RAM begrenzt. Bei größeren Indizes anpassen:

```yaml
# docker-compose.yml
meilisearch:
  deploy:
    resources:
      limits:
        memory: 1G  # oder 768M
```

### inotify Watch-Limit (Linux/Raspberry Pi)

Bei vielen Dateien kann das inotify-Limit erreicht werden:

```bash
# Aktuelles Limit prüfen
cat /proc/sys/fs/inotify/max_user_watches

# Temporär erhöhen
sudo sysctl fs.inotify.max_user_watches=65536

# Permanent in /etc/sysctl.conf:
# fs.inotify.max_user_watches=65536
```

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

# Meilisearch und Tika aktualisieren
docker compose pull meilisearch tika
docker compose up -d

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
├── web/
│   └── index.html      # Such-UI
└── meili_data/
```

---
