#!/usr/bin/env python3
"""
Podcast Downloader - Lädt alle Folgen aus einem RSS-Feed herunter.
Usage: python3 podcast_downloader.py <RSS_URL> [download_directory]
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import re
import json
from email.utils import parsedate_to_datetime

def sanitize_filename(filename):
    """Bereinigt Dateinamen von ungültigen Zeichen."""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename[:200]

def download_podcast_episodes(rss_url, download_dir="podcast_episodes"):
    """Lädt alle Podcast-Folgen aus dem RSS-Feed herunter."""
    
    print(f"Lade RSS-Feed von: {rss_url}")
    
    # RSS-Feed laden
    try:
        response = requests.get(rss_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Fehler beim Laden des RSS-Feeds: {e}")
        return
    
    # XML parsen
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"Fehler beim Parsen des RSS-Feeds: {e}")
        return
    
    # Podcast-Informationen extrahieren
    channel = root.find('.//channel')
    podcast_title = channel.find('title').text if channel.find('title') is not None else "Unbekannter Podcast"
    print(f"Podcast: {podcast_title}")

    # Unterordner pro Podcast-Titel
    podcast_folder_name = sanitize_filename(podcast_title) or "podcast"
    podcast_dir = os.path.join(download_dir, podcast_folder_name)
    os.makedirs(podcast_dir, exist_ok=True)

    # Persistenter Duplikat-Schutz (.downloaded.json basierend auf GUID/URL)
    state_path = os.path.join(podcast_dir, ".downloaded.json")
    downloaded_keys = set()
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    downloaded_keys = set(data)
                elif isinstance(data, dict) and "items" in data:
                    downloaded_keys = set(data.get("items", []))
        except Exception:
            pass
    
    # Alle Folgen finden
    episodes = root.findall('.//item')
    print(f"Gefundene Folgen: {len(episodes)}")
    
    for i, episode in enumerate(episodes, 1):
        # Episode-Informationen extrahieren
        title_elem = episode.find('title')
        title = title_elem.text if title_elem is not None else f"Episode {i}"
        
        pub_date_elem = episode.find('pubDate')
        pub_date = pub_date_elem.text if pub_date_elem is not None else ""
        # Datum in YYYY-MM-DD umwandeln, falls möglich
        date_prefix = None
        if pub_date:
            try:
                dt = parsedate_to_datetime(pub_date)
                date_prefix = dt.strftime('%Y-%m-%d')
            except Exception:
                date_prefix = None
        
        # Audio-URL finden
        enclosure = episode.find('enclosure')
        if enclosure is None:
            print(f"Keine Audio-Datei für Episode {i}: {title}")
            continue
            
        audio_url = enclosure.get('url')
        if not audio_url:
            print(f"Keine gültige Audio-URL für Episode {i}: {title}")
            continue
        # Key für Duplikatprüfung: GUID bevorzugt, sonst Audio-URL
        guid_elem = episode.find('guid')
        guid_text = guid_elem.text.strip() if guid_elem is not None and guid_elem.text else None
        episode_key = guid_text or audio_url
        if episode_key in downloaded_keys:
            print(f"Überspringe {i}/{len(episodes)}: {title} (bereits heruntergeladen)")
            continue
        
        # Dateiname erstellen
        parsed_url = urlparse(audio_url)
        file_extension = os.path.splitext(parsed_url.path)[1] or '.mp3'
        safe_title = sanitize_filename(title)
        if date_prefix:
            base_filename = f"{date_prefix}_{safe_title}{file_extension}"
        else:
            base_filename = f"{safe_title}{file_extension}"

        # Falls Datei bereits existiert, Suffix anhängen (-1, -2, ...)
        filename = base_filename
        filepath = os.path.join(podcast_dir, filename)
        counter = 1
        while os.path.exists(filepath):
            name_without_ext, ext = os.path.splitext(base_filename)
            filename = f"{name_without_ext}-{counter}{ext}"
            filepath = os.path.join(podcast_dir, filename)
            counter += 1
        
        # Prüfen ob Datei bereits existiert
        # (existiert durch obige Schleife nicht mehr, aber doppelt gemoppelt schadet nicht)
        if os.path.exists(filepath):
            print(f"Überspringe {i}/{len(episodes)}: {title} (bereits vorhanden)")
            continue
        
        print(f"Lade {i}/{len(episodes)}: {title}")
        
        # Audio-Datei herunterladen
        try:
            headers = {"User-Agent": "podcast-downloader/1.0"}
            audio_response = requests.get(audio_url, stream=True, headers=headers, timeout=30)
            audio_response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in audio_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  ✓ Gespeichert: {filename} ({file_size:.1f} MB)")
            # Erfolgreich: Key persistieren
            downloaded_keys.add(episode_key)
            try:
                with open(state_path, 'w', encoding='utf-8') as f:
                    json.dump(sorted(list(downloaded_keys)), f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            
        except requests.RequestException as e:
            print(f"  ✗ Fehler beim Herunterladen: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"  ✗ Unerwarteter Fehler: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
    
    print(f"\nDownload abgeschlossen! Dateien gespeichert in: {os.path.abspath(download_dir)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 podcast_downloader.py <RSS_URL> [download_directory]")
        print("Beispiel: python3 podcast_downloader.py https://anchor.fm/s/38a331c/podcast/rss")
        sys.exit(1)
    
    rss_url = sys.argv[1]
    download_dir = sys.argv[2] if len(sys.argv) > 2 else "podcast_episodes"
    
    print("=== Podcast Downloader ===")
    download_podcast_episodes(rss_url, download_dir)