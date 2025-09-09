# Starvincis TinderBot Deployment Pipeline

## Übersicht

Die Deployment-Pipeline ermöglicht es dir, den TinderBot während des Betriebs zu aktualisieren und neue Versionen sicher zu deployen.

## Features

###  **Hot-Reload System**
- Bot läuft weiter während der Entwicklung
- Konfigurationsänderungen werden sofort übernommen
- Keine Downtime bei Updates

###  **Automatische Tests**
- Konfigurations-Tests
- Import-Tests
- Phase-Manager-Tests
- Storage-Tests

###  **Backup-System**
- Automatische Backups vor jedem Deployment
- Rollback-Funktionalität
- Versionierung

###  **Sicheres Deployment**
- Tests vor Deployment
- Graceful Restart
- Fehlerbehandlung

## Verwendung

### 1. **Deployment Manager starten**
```bash
python deployment.py
```

### 2. **Bot starten (läuft automatisch)**
```bash
Deployment > start_bot
```

**Oder direkt:**
```bash
python tinderbot.py  # Startet Bot direkt
```

### 3. **Tests ausführen**
```bash
Deployment > test
```

### 4. **Neue Version deployen**
```bash
Deployment > deploy 2.0.0
```

### 5. **Hot-Reload (Unix)**
```bash
Deployment > hot_reload
```

### 6. **Status prüfen**
```bash
Deployment > status
```

### 7. **Rollback bei Problemen**
```bash
Deployment > rollback
```

## Workflow

### **Entwicklung während Bot läuft:**

1. **Bot starten**: `start_bot` (oder direkt `python tinderbot.py`)
2. **Code ändern**: Bearbeite Dateien
3. **Tests laufen**: `test`
4. **Deployen**: `deploy [version]`
5. **Bot läuft weiter**: Automatischer Restart

### **Bot-Verwaltung:**

1. **Chat ausschließen**: `exclude_chat [name]`
2. **Chat hinzufügen**: `include_chat [name]`
3. **Status prüfen**: `list_active`
4. **Debug-Modus**: `debug_chats`
5. **Debug-Ausgaben**: `show_debug`

### **Schnelle Änderungen:**

1. **Config ändern**: Bearbeite `config.json`
2. **Hot-Reload**: `hot_reload` (nur Unix)
3. **Änderungen aktiv**: Sofort übernommen

## Befehle

| Befehl | Beschreibung |
|--------|-------------|
| `start_bot` | Bot starten |
| `stop_bot` | Bot stoppen |
| `deploy [version]` | Neue Version deployen |
| `hot_reload` | Konfiguration neu laden |
| `status` | Deployment-Status anzeigen |
| `rollback [backup]` | Zurück zu Backup |
| `test` | Tests ausführen |
| `backup` | Backup erstellen |
| `exclude_chat [name]` | Chat ausschließen |
| `include_chat [name]` | Chat wieder hinzufügen |
| `list_excluded` | Ausgeschlossene Chats anzeigen |
| `list_active` | Aktive Chats anzeigen |
| `debug_chats` | Debug-Modus starten |
| `show_debug` | Bot Debug-Ausgaben anzeigen |
| `exit` | Beenden |

## Dateien

### **Core-Dateien:**
- `tinderbot.py` - Hauptprogramm
- `chat.py` - Chat-Management
- `storage.py` - Datenspeicherung
- `config.json` - Konfiguration

### **Deployment-Dateien:**
- `deployment.py` - Deployment Manager
- `test_deployment.py` - Test Suite
- `version.json` - Versionsinfo
- `backups/` - Backup-Verzeichnis

## Sicherheit

### **Backup-Strategie:**
- Automatische Backups vor jedem Deployment
- Timestamp-basierte Backup-Namen
- Vollständige Datei-Backups

### **Rollback:**
- Sofortiger Rollback bei Problemen
- Automatische Wiederherstellung
- Bot-Restart nach Rollback

### **Tests:**
- Konfigurations-Validierung
- Import-Tests
- Funktionalitäts-Tests
- Storage-Tests

## Troubleshooting

### **Bot startet nicht:**
1. `test` ausführen
2. Fehler in Logs prüfen
3. `rollback` bei Problemen

### **Hot-Reload funktioniert nicht:**
- Nur auf Unix-Systemen verfügbar
- Windows: `deploy` verwenden

### **Tests schlagen fehl:**
1. Konfiguration prüfen
2. Dependencies installieren
3. Fehler beheben

## Best Practices

### **Entwicklung:**
1. Immer `test` vor `deploy`
2. Sinnvolle Versionsnummern verwenden
3. Backups regelmäßig prüfen

### **Deployment:**
1. Bot läuft lassen während Entwicklung
2. Kleine, häufige Deployments
3. Rollback-Plan haben

### **Monitoring:**
1. `status` regelmäßig prüfen
2. Logs überwachen
3. Performance beobachten

## Beispiel-Workflow

```bash
# 1. Deployment Manager starten
python deployment.py

# 2. Bot starten
Deployment > start_bot

# 3. Entwicklung (in anderem Terminal)
# - Code ändern
# - Tests schreiben

# 4. Tests ausführen
Deployment > test

# 5. Neue Version deployen
Deployment > deploy 1.1.0

# 6. Status prüfen
Deployment > status

# 7. Debug-Ausgaben anzeigen
Deployment > show_debug

# 8. Bei Problemen rollback
Deployment > rollback
```

