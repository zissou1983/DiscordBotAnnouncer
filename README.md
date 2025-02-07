# 📢 Discord Bot für Twitch- und YouTube-Benachrichtigungen

Ein Discord-Bot, der Benachrichtigungen sendet, wenn abonnierte Twitch-Streamer online gehen oder neue YouTube-Videos veröffentlicht werden. Zudem integriert er ein LLM für interaktive Konversationen.

## 🚀 Funktionen

- 🔴 **Twitch-Überwachung**: Erkennt, wenn abonnierte Streamer online gehen oder das Spiel wechseln, und sendet eine Nachricht in einen Discord-Kanal.
- 🎥 **YouTube-Benachrichtigungen**: Überprüft regelmäßig abonnierte Kanäle auf neue Videos und informiert über Veröffentlichungen.
- 🤖 **Ollama LLM-Integration**: Ermöglicht interaktive Konversationen mit einem lokal gehosteten KI-Modell.

## 🔧 Installation

### 1️⃣ Projekt klonen  
```bash
git clone https://github.com/zissou1983/DiscordBotAnnouncer.git
cd DiscordBotAnnouncer
```

### 2️⃣ Abhängigkeiten installieren  
```bash
pip install -r requirements.txt
```

### 3️⃣ Umgebungsvariablen setzen  
Erstelle eine `.env` Datei und setze die API-Keys:
```
DISCORD_TOKEN=dein_discord_token
TWITCH_CLIENT_ID=dein_twitch_client_id
TWITCH_ACCESS_TOKEN=dein_twitch_access_token
TWITCH_USER_ID=dein_twitch_user_id
YOUTUBE_API_KEY=dein_youtube_api_key
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=dein_llm
```

### 4️⃣ Bot starten  
```bash
python discordbot.py
```

## 🛠️ Geplante Features

- ✅ **Verbesserte Fehlerbehandlung** für Twitch- und YouTube-Anfragen  
- 🔄 **Automatische Neustarts des Bots** bei Fehlern oder Verbindungsabbrüchen  
- 📢 **Anpassbare Benachrichtigungen** mit konfigurierbaren Kanal-IDs  
- 🗣 **Sprachausgabe für KI-Antworten**  
- 🔍 **Erweiterte Filter für YouTube-Videos** (z. B. bestimmte Keywords bevorzugen)  

---

🚀 Viel Spaß mit deinem Discord-Bot! 🎉

