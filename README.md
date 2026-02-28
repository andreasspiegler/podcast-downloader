# Podcast Downloader

Lädt alle Folgen eines Podcasts via RSS-Feed herunter.

## Features

- Lädt alle Episoden eines RSS-Feeds als MP3/Audio-Dateien
- Legt pro Podcast einen eigenen Unterordner an
- Dateinamen mit Datums-Prefix (`YYYY-MM-DD_Titel.mp3`)
- Persistenter Duplikatschutz: bereits heruntergeladene Folgen werden übersprungen (auch nach Neustart)
- Erkennung per GUID oder Audio-URL
- Abschlussbericht mit Anzahl heruntergeladener, übersprungener und fehlgeschlagener Episoden

## Voraussetzungen

```bash
pip install -r requirements.txt
```

## Verwendung

```bash
python3 podcast_downloader.py <RSS_URL> [download_verzeichnis]
```

**Beispiel:**
```bash
python3 podcast_downloader.py https://anchor.fm/s/38a331c/podcast/rss
```

Ohne Angabe eines Verzeichnisses werden die Dateien in `./podcast_episodes/<Podcast-Titel>/` gespeichert.

## Dateistruktur

```
podcast_episodes/
└── Podcast Titel/
    ├── .downloaded.json       # Duplikatschutz-State
    ├── 2024-01-15_Episode 1.mp3
    └── 2024-01-22_Episode 2.mp3
```
