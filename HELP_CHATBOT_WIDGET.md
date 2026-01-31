# Help Chatbot Widget - Dokumentation

## Überblick

Der **Help Chatbot Widget** ist ein kontextsensitiver AI-Assistent, der allen Benutzern (Gäste, Patienten, Ärzte) bei der Navigation und Nutzung der TerminFinder-Plattform hilft.

## Features

### 1. **Floating Widget**
- Fester Button im rechten unteren Ecke
- Immer verfügbar auf allen Seiten
- Smooth Animations und modernes Design
- Responsive für Mobile

### 2. **Kontextsensitiv**
Der Chatbot erkennt:
- **Benutzertyp** (Guest/Patient/Doctor) via JWT Token
- **Aktuelle Seite** (URL path) für spezifische Hilfe
- **Chat History** (letzte 20 Nachrichten)

### 3. **Drei Benutzertypen**

#### A) Gäste (Unregistrierte Benutzer)
**Rolle:** Verkaufsberater
- Erklärt Konzept und Vorteile der Plattform
- Stellt Fragen um Bedürfnisse zu verstehen
- Motiviert zur Registrierung
- Gibt konkrete Beispiele

**Seitenspezifische Tipps:**
- Startseite: Was ist TerminFinder?
- Suche: Wie funktioniert die Arztsuche?
- Login/Register: Vorteile eines Kontos

#### B) Patienten
**Rolle:** Navigations-Assistent
- Hilft bei der Navigation
- Erklärt Patientenfunktionen
- Schritt-für-Schritt Anleitungen

**Seitenspezifische Tipps:**
- Suche: Filter und Terminbuchung
- Meine Termine: Verwaltung von Buchungen
- Dashboard: Überblick aller Features
- Profil: Datenverwaltung

#### C) Ärzte
**Rolle:** Setup-Assistent
- Hilft bei Praxis-Einrichtung
- Erklärt alle Arzt-Features
- Best Practices und Optimierungstipps

**Seitenspezifische Tipps:**
- Praxisprofil: 8 Tabs optimal ausfüllen
- Kalender: Verfügbarkeiten setzen
- Termine: Buchungsverwaltung
- Dashboard: Feature-Übersicht

## Technische Implementierung

### Backend

**Datei:** `app/routes/help_chat.py`

**Endpoints:**
- `POST /api/help-chat` - Chat-Nachricht senden
- `POST /api/help-chat/reset` - Gespräch zurücksetzen

**Request:**
```json
{
  "message": "Wie buche ich einen Termin?",
  "current_page": "/patient/search"
}
```

**Response:**
```json
{
  "reply": "Um einen Termin zu buchen...",
  "user_type": "patient"
}
```

**Funktionen:**
- `get_user_context()` - Erkennt Benutzertyp aus JWT
- `get_system_prompt_for_guest()` - Verkaufs-Prompt
- `get_system_prompt_for_patient()` - Patienten-Hilfe-Prompt
- `get_system_prompt_for_doctor()` - Arzt-Setup-Prompt

### Frontend

**Dateien:**
- `app/templates/base.html` - Widget HTML, CSS, JavaScript
- Funktioniert automatisch auf allen Seiten (inkl. base_dashboard.html)

**JavaScript Funktionen:**
- `toggleHelpChat()` - Öffnet/Schließt Widget
- `sendHelpMessage()` - Sendet Nachricht an API
- `addHelpChatMessage()` - Zeigt Nachricht im Chat
- `resetHelpChat()` - Setzt Gespräch zurück

**CSS-Klassen:**
- `.help-chat-btn` - Floating Button
- `.help-chat-window` - Chat-Fenster
- `.help-chat-header` - Header mit Gradient
- `.help-chat-messages` - Nachrichten-Container
- `.help-chat-input` - Input-Bereich

## Unterschied zu Practice Chatbot

| Feature | Help Chatbot Widget | Practice Chatbot |
|---------|---------------------|------------------|
| **Zweck** | Hilfe zur Plattform-Nutzung | Fragen zur konkreten Praxis |
| **Sichtbarkeit** | Auf allen Seiten | Nur auf Arzt-Details-Seite |
| **Benutzer** | Alle (Guest/Patient/Doctor) | Nur Patienten |
| **Kontext** | Aktuelle Seite + Benutzertyp | Praxis-Daten + Custom Instructions |
| **Prompts** | 3 verschiedene (Guest/Patient/Doctor) | 1 Basis + Custom vom Arzt |
| **Endpoint** | `/api/help-chat` | `/api/chat/<practice_id>` |

## OpenAI Konfiguration

**Model:** GPT-4-turbo-preview (konfigurierbar)
**Max Tokens:** 500
**Temperature:** 0.7
**Context Length:** Bis zu 20 vorherige Nachrichten

**Proxy-Fix für Render.com:**
```python
# Temporär proxy env vars entfernen
proxy_vars = {}
for key in ['HTTP_PROXY', 'HTTPS_PROXY', ...]:
    if key in os.environ:
        proxy_vars[key] = os.environ[key]
        del os.environ[key]

# OpenAI Client erstellen
client = OpenAI(api_key=..., http_client=httpx.Client(...))

# Proxy vars wiederherstellen
for key, value in proxy_vars.items():
    os.environ[key] = value
```

## Session Management

**Session Keys:**
- `help_chat_history_guest` - Chat für Gäste
- `help_chat_history_patient` - Chat für Patienten
- `help_chat_history_doctor` - Chat für Ärzte

Jeder Benutzertyp hat separate History.

## Styling

**Farben:**
- Gradient: `#667eea` → `#764ba2` (Lila)
- User Messages: `#667eea` (Lila)
- Assistant Messages: Weiß
- Background: `#f8f9fa` (Hell-Grau)

**Animationen:**
- Slide-up beim Öffnen
- Pulse-Effekt am Button
- Fade-in für Nachrichten

## Deployment

**Requirements:**
- `openai==1.12.0` (bereits in requirements.txt)
- `httpx` (Dependency von OpenAI)

**Environment Variables:**
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview  # optional
```

## Testing

**Manuell testen:**

1. Als Gast (ohne Login):
```bash
# Öffne Startseite
# Klicke auf Help Widget
# Frage: "Was ist TerminFinder?"
```

2. Als Patient:
```bash
# Login als Patient
# Gehe zu /patient/search
# Frage: "Wie buche ich einen Termin?"
```

3. Als Arzt:
```bash
# Login als Arzt
# Gehe zu /practice/profile
# Frage: "Wie fülle ich das Praxisprofil aus?"
```

**API testen:**
```bash
curl -X POST http://localhost:5000/api/help-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hallo",
    "current_page": "/"
  }'
```

## Best Practices für System Prompts

1. **Klar definierte Rolle** - Verkäufer/Navigator/Setup-Assistent
2. **Konkrete Beispiele** - Nicht nur Theorie
3. **Aktionsaufforderungen** - "Möchtest du...", "Soll ich..."
4. **Seitenspezifisch** - Unterschiedlicher Kontext pro Seite
5. **Freundlich aber professionell** - Du-Form, höflich

## Erweiterungsmöglichkeiten

1. **Analytics:** Tracking welche Fragen gestellt werden
2. **FAQ Integration:** Automatische Verlinkung zu FAQ
3. **Multilingualität:** Englisch/Deutsch detection
4. **Voice Input:** Spracheingabe für Nachrichten
5. **Proaktive Tipps:** Automatische Hints bei bestimmten Aktionen
6. **Admin Dashboard:** Statistiken über Chatbot-Nutzung

## Kosten

**Geschätzte Kosten:**
- Pro Nachricht: ~$0.002-0.008 (abhängig von Länge)
- 1000 Nachrichten: ~$2-8
- Alternative: gpt-3.5-turbo für günstigere Option (~10x billiger)

## Support

Bei Fragen oder Problemen:
- Logs prüfen: `/var/log/app.log` (Render.com)
- OpenAI Dashboard: usage.openai.com
- GitHub Issues: [Projektname]/issues
