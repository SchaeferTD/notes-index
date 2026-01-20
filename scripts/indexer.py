import time, json, requests, subprocess, os, traceback, hashlib
from pathlib import Path
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from datetime import datetime

def log(message):
    """Logging mit Timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

MEILI_URL = os.environ["MEILI_URL"]
API_KEY = os.environ["MEILI_API_KEY"]
TIKA_URL = os.environ["TIKA_URL"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Maximale Dateigröße (in Bytes) - 250 MB
MAX_FILE_SIZE = 250 * 1024 * 1024

# Ignorierte Ordner
IGNORED_FOLDERS = {'.trash', '.stfolder', '.git', '.obsidian', 'node_modules', '__pycache__', 'Bibeltext', 'zzOrga'}

def should_ignore_path(file_path):
    """Prüft ob ein Pfad ignoriert werden soll"""
    path_parts = Path(file_path).parts
    
    # Versteckte Ordner (beginnen mit .)
    for part in path_parts:
        if part.startswith('.'):
            return True
        if part in IGNORED_FOLDERS:
            return True
    
    return False

def path_to_id(file_path):
    """Wandelt einen Pfad in eine gültige Meilisearch Document-ID um"""
    # MD5-Hash des Pfads (immer gültige ID)
    return hashlib.md5(file_path.encode()).hexdigest()

def create_index():
    """Erstellt den Index, falls er nicht existiert"""
    try:
        response = requests.post(
            f"{MEILI_URL}/indexes",
            headers=HEADERS,
            json={"uid": "files", "primaryKey": "id"},
            timeout=10
        )
        log(f"✅ Index erstellt: {response.status_code}")
    except Exception as e:
        log(f"ℹ️  Index existiert bereits oder Fehler: {e}")

def index_document(file_path):
    """Indexiert ein einzelnes Dokument"""
    try:
        # Ignoriere bestimmte Pfade
        if should_ignore_path(file_path):
            log(f"⏭️  Überspringe (ignorierter Ordner): {file_path}")
            return
        
        # Dateigröße prüfen
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            log(f"⚠️  Datei zu groß ({file_size/1024/1024:.2f} MB), überspringe: {file_path}")
            return
        
        if file_size == 0:
            log(f"⚠️  Leere Datei, überspringe: {file_path}")
            return
        
        ext = file_path.lower().split('.')[-1]
        
        if ext == "md":
            log(f"📝 Verarbeite Markdown ({file_size} bytes): {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(MAX_FILE_SIZE)
                
                if len(content) > 50000:
                    content = content[:50000] + "\n... (gekürzt)"
                    log(f"⚠️  Inhalt gekürzt auf 50000 Zeichen")
                
                # Preview erstellen (erste 500 Zeichen)
                preview = content[:500] + "..." if len(content) > 500 else content
                
                data = {
                    "id": path_to_id(file_path),
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "preview": preview,
                    "content": content,
                    "type": "markdown"
                }
            except Exception as e:
                log(f"❌ Fehler beim Lesen von {file_path}: {e}")
                return
        
        elif ext in ["doc", "docx", "pdf", "txt", "odt", "rtf"]:
            log(f"📄 Verarbeite mit Tika ({file_size} bytes): {file_path}")
            try:
                with open(file_path, 'rb') as f:
                    response = requests.put(TIKA_URL, data=f, timeout=60)
                
                if response.status_code == 200:
                    text = response.text
                    if len(text) > 50000:
                        text = text[:50000] + "\n... (gekürzt)"
                    
                    # Preview erstellen (erste 500 Zeichen)
                    preview = text[:500] + "..." if len(text) > 500 else text
                    
                    data = {
                        "id": path_to_id(file_path),
                        "path": file_path,
                        "filename": os.path.basename(file_path),
                        "preview": preview,
                        "content": text,
                        "type": ext
                    }
                else:
                    log(f"❌ Tika-Fehler für {file_path}: {response.status_code}")
                    return
            except requests.exceptions.Timeout:
                log(f"❌ Timeout bei Tika für {file_path}")
                return
            except Exception as e:
                log(f"❌ Fehler bei Tika für {file_path}: {e}")
                return
        
        elif ext in ["mp3", "wav", "flac", "m4a"]:
            log(f"🎵 Verarbeite Audio ({file_size} bytes): {file_path}")
            try:
                meta = subprocess.check_output(
                    ["exiftool", "-json", file_path], 
                    timeout=30,
                    stderr=subprocess.DEVNULL
                ).decode("utf-8")
                audio_data = json.loads(meta)[0]
                
                # Preview für Audio (Titel, Artist, Album)
                preview_parts = []
                if "Title" in audio_data:
                    preview_parts.append(f"Title: {audio_data['Title']}")
                if "Artist" in audio_data:
                    preview_parts.append(f"Artist: {audio_data['Artist']}")
                if "Album" in audio_data:
                    preview_parts.append(f"Album: {audio_data['Album']}")
                preview = " | ".join(preview_parts) if preview_parts else "Audio-Datei"
                
                data = {
                    "id": path_to_id(file_path),
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "preview": preview,
                    "type": "audio",
                    **audio_data
                }
            except subprocess.TimeoutExpired:
                log(f"❌ Timeout bei ExifTool für {file_path}")
                return
            except Exception as e:
                log(f"❌ Fehler bei ExifTool für {file_path}: {e}")
                return
        
        else:
            return
        
        # Zu Meilisearch senden
        try:
            response = requests.post(
                f"{MEILI_URL}/indexes/files/documents",
                headers=HEADERS,
                json=[data],
                timeout=30
            )
            
            if response.status_code in [200, 202]:
                log(f"✅ Indexiert: {file_path}")
            else:
                log(f"❌ Meilisearch-Fehler bei {file_path}: {response.status_code} - {response.text}")
        except requests.exceptions.Timeout:
            log(f"❌ Timeout bei Meilisearch für {file_path}")
        except Exception as e:
            log(f"❌ Fehler bei Meilisearch für {file_path}: {e}")
    
    except Exception as e:
        log(f"❌ UNERWARTETER Fehler beim Indexieren von {file_path}: {e}")
        log(f"Traceback: {traceback.format_exc()}")

def index_existing_files(base_path="/data"):
    """Indexiert alle vorhandenen Dateien beim Start"""
    log(f"🔍 Scanne vorhandene Dateien in {base_path}...")
    log(f"🚫 Ignoriere Ordner: {', '.join(IGNORED_FOLDERS)}")
    
    supported_extensions = {".md", ".doc", ".docx", ".pdf", ".txt", ".odt", ".rtf", 
                           ".mp3", ".wav", ".flac", ".m4a"}
    
    file_count = 0
    skipped_count = 0
    
    for root, dirs, files in os.walk(base_path):
        # Filtere ignorierte Ordner aus (verhindert os.walk sie zu besuchen)
        dirs[:] = [d for d in dirs if d not in IGNORED_FOLDERS and not d.startswith('.')]
        
        for file in files:
            if Path(file).suffix.lower() in supported_extensions:
                file_path = os.path.join(root, file)
                
                if should_ignore_path(file_path):
                    skipped_count += 1
                    continue
                
                file_count += 1
                
                if file_count % 10 == 0:
                    log(f"📊 Fortschritt: {file_count} Dateien verarbeitet, {skipped_count} übersprungen...")
                
                index_document(file_path)
    
    log(f"✅ Fertig! {file_count} Dateien verarbeitet, {skipped_count} übersprungen!")

def delete_document(file_path):
    """Löscht ein Dokument aus dem Index"""
    doc_id = path_to_id(file_path)
    try:
        response = requests.delete(
            f"{MEILI_URL}/indexes/files/documents/{doc_id}",
            headers=HEADERS,
            timeout=10
        )
        if response.status_code in [200, 202]:
            log(f"🗑️  Aus Index entfernt: {file_path}")
        else:
            log(f"⚠️  Konnte nicht entfernen (evtl. nicht im Index): {file_path}")
    except Exception as e:
        log(f"❌ Fehler beim Löschen aus Index: {e}")

def cleanup_deleted_files():
    """Entfernt Dokumente aus dem Index, deren Dateien nicht mehr existieren"""
    log("🧹 Starte Cleanup für gelöschte Dateien...")

    deleted_count = 0
    offset = 0
    limit = 1000

    while True:
        try:
            response = requests.get(
                f"{MEILI_URL}/indexes/files/documents?limit={limit}&offset={offset}",
                headers=HEADERS,
                timeout=30
            )

            if response.status_code != 200:
                log(f"❌ Fehler beim Abrufen der Dokumente: {response.status_code}")
                break

            data = response.json()
            docs = data.get("results", [])

            if not docs:
                break

            for doc in docs:
                file_path = doc.get("path")
                if file_path and not os.path.exists(file_path):
                    delete_document(file_path)
                    deleted_count += 1

            offset += limit

            # Prüfen ob es weitere Dokumente gibt
            if len(docs) < limit:
                break

        except Exception as e:
            log(f"❌ Fehler beim Cleanup: {e}")
            break

    log(f"🧹 Cleanup fertig! {deleted_count} verwaiste Einträge entfernt.")

class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and not should_ignore_path(event.src_path):
            log(f"📄 Neue Datei erkannt: {event.src_path}")
            index_document(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and not should_ignore_path(event.src_path):
            log(f"📝 Datei geändert: {event.src_path}")
            index_document(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            log(f"🗑️  Datei gelöscht: {event.src_path}")
            delete_document(event.src_path)

# Hauptprogramm
if __name__ == "__main__":
    try:
        log("🚀 Starte Indexer...")
        log(f"⚙️  Maximale Dateigröße: {MAX_FILE_SIZE/1024/1024:.2f} MB")
        
        # 1. Index erstellen
        create_index()
        time.sleep(2)

        # 2. Optional: Cleanup für gelöschte Dateien (via CLEANUP=true in .env)
        if os.environ.get("CLEANUP", "false").lower() == "true":
            cleanup_deleted_files()

        # 3. Alle vorhandenen Dateien indexieren
        index_existing_files("/data")
        
        # 4. Watcher für neue Dateien starten
        observer = PollingObserver(timeout=5)
        observer.schedule(Watcher(), path="/data", recursive=True)
        observer.start()
        
        log("👀 Beobachte /data für neue Änderungen...")
        log("💓 Heartbeat wird alle 60 Sekunden ausgegeben...")
        
        counter = 0
        while True:
            time.sleep(60)
            counter += 1
            log(f"💓 Heartbeat #{counter} - Indexer läuft noch...")
    
    except KeyboardInterrupt:
        log("🛑 Stoppe Indexer...")
        observer.stop()
    except Exception as e:
        log(f"💥 KRITISCHER FEHLER: {e}")
        log(f"Traceback: {traceback.format_exc()}")
        raise
    
    observer.join()
    log("👋 Indexer beendet")