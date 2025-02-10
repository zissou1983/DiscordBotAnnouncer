import os
import requests
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Lade die .env Datei
load_dotenv()

# Lade Token und API-Keys aus der .env Datei
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN')
TWITCH_USER_ID = os.getenv('TWITCH_USER_ID')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_ACCESS_TOKEN = os.getenv('YOUTUBE_ACCESS_TOKEN')
YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN')
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
OLLAMA_URL = os.getenv('OLLAMA_URL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')

# Discord Intents festlegen
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Globale Variable für den aktuellen Zustand der Live-Kanäle
current_live_channels = {}

# Funktion, um den YouTube Access Token mit dem Refresh Token zu erneuern
def refresh_youtube_access_token():
    global YOUTUBE_ACCESS_TOKEN  # Aktualisiere den globalen Access Token
    
    data = {
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET,
        'refresh_token': YOUTUBE_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }

    response = requests.post('https://oauth2.googleapis.com/token', data=data)

    if response.status_code == 200:
        new_tokens = response.json()
        YOUTUBE_ACCESS_TOKEN = new_tokens['access_token']  # Aktualisiere den Access Token
        print("YouTube Access Token erfolgreich erneuert!")
    else:
        print(f"Fehler beim Erneuern des YouTube Access Tokens: {response.status_code}, {response.text}")

# Funktion, um die gefolgten Twitch-Kanäle zu überprüfen und Änderungen zu melden
def get_twitch_live_followed_channels():
    headers = {
        'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID
    }

    params = {
        'user_id': TWITCH_USER_ID
    }

    response = requests.get('https://api.twitch.tv/helix/streams/followed', headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        streams = data['data']
        return streams  # Gib die Liste der aktuellen Streams zurück
    else:
        print(f"Fehler: {response.status_code}, {response.text}")
        return None

# Funktion, um die Änderungen zu erkennen und Discord-Nachrichten zu senden
async def check_twitch_updates():
    global current_live_channels
    new_live_channels = get_twitch_live_followed_channels()  # Aktuelle Streams abfragen

    if new_live_channels is None:
        return

    # Umwandlung der Liste von Streams in ein Dictionary für einfachere Handhabung
    new_live_dict = {stream['user_name']: stream for stream in new_live_channels}
    changes = []  # Liste für Änderungen

    # Überprüfe auf neue Streamer oder Spielwechsel
    for user_name, stream in new_live_dict.items():
        if user_name not in current_live_channels:
            # Neuer Streamer ist live gegangen
            changes.append(f"• **{user_name}** ist jetzt live und spielt **{stream['game_name']}**.")
        elif stream['game_name'] != current_live_channels[user_name]['game_name']:
            # Streamer hat das Spiel gewechselt
            changes.append(f"• **{user_name}** spielt jetzt **{stream['game_name']}** (vorher: {current_live_channels[user_name]['game_name']}).")

    # Überprüfe auf Streamer, die offline gegangen sind
    for user_name in list(current_live_channels):
        if user_name not in new_live_dict:
            changes.append(f"• **{user_name}** ist jetzt offline.")  # Streamer ist offline gegangen

    # Wenn es Änderungen gibt, sende nur die Änderungen an den Discord-Kanal
    if changes:
        discord_channel_id = 1192236339727450183  # Ersetze dies durch deine Discord-Channel-ID
        channel = bot.get_channel(discord_channel_id)
        if channel:
            await channel.send("\n".join(changes))
        else:
            print(f"Fehler: Konnte den Channel mit ID {discord_channel_id} nicht finden.")
    
    # Aktualisiere den aktuellen Live-Status
    current_live_channels = new_live_dict

# Task: Überprüfe Twitch alle 5 Minuten
@tasks.loop(minutes=5)
async def check_twitch():
    await check_twitch_updates()

# Funktion, um die abonnierten Kanäle des Nutzers zu erhalten (YouTube)
def get_subscribed_channels():
    refresh_youtube_access_token()  # Stelle sicher, dass der Token vor jeder Abfrage erneuert wird

    headers = {
        'Authorization': f'Bearer {YOUTUBE_ACCESS_TOKEN}',
        'Accept': 'application/json'
    }

    params = {
        'part': 'snippet',
        'mine': 'true',  # Hiermit wird sichergestellt, dass nur die eigenen Abos zurückgegeben werden
        'maxResults': 50  # Maximale Anzahl der abonnierten Kanäle pro Abfrage
    }

    response = requests.get('https://www.googleapis.com/youtube/v3/subscriptions', headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        channels = []
        if 'items' in data:
            for item in data['items']:
                channels.append(item['snippet']['resourceId']['channelId'])  # Kanal-IDs speichern
        return channels
    else:
        print(f"Fehler beim Abrufen der abonnierten Kanäle: {response.status_code}, {response.text}")
        return []

# Funktion, um die neuesten Videos der abonnierten Kanäle abzurufen
def get_latest_videos_from_channels(channel_ids):
    refresh_youtube_access_token()

    headers = {
        'Authorization': f'Bearer {YOUTUBE_ACCESS_TOKEN}',
        'Accept': 'application/json'
    }

    # Setze das Datum auf die letzten 24 Stunden
    published_after = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    all_videos = []
    for channel_id in channel_ids:
        params = {
            'part': 'snippet',
            'channelId': channel_id,  # Kanal-ID
            'publishedAfter': published_after,  # Nur Videos der letzten 24 Stunden
            'maxResults': 5,  # Maximale Anzahl der zurückgegebenen Videos
            'order': 'date',  # Sortiere nach Veröffentlichungsdatum
            'type': 'video',
            'key': YOUTUBE_API_KEY
        }

        response = requests.get('https://www.googleapis.com/youtube/v3/search', headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if 'items' in data and data['items']:
                for item in data['items']:
                    video_title = item['snippet']['title']
                    video_id = item['id']['videoId']
                    channel_title = item['snippet']['channelTitle']
                    published_at = item['snippet']['publishedAt']
                    video_link = f"<https://www.youtube.com/watch?v={video_id}>"
                    all_videos.append(f" - **{channel_title}**: [{video_title}]({video_link}) (Veröffentlicht am {published_at})\n")
        else:
            print(f"Fehler beim Abrufen der Videos für Kanal {channel_id}: {response.status_code}, {response.text}")

    return all_videos

# Task: Überprüfe YouTube alle 144 Minuten
@tasks.loop(minutes=144)
async def check_youtube_updates():
    print("Überprüfe YouTube-Kanäle auf Updates...")

    # Verwende die richtige Discord-Channel-ID
    discord_channel_id = 1192236339727450183  # Ersetze dies durch deine Discord-Channel-ID
    channel = bot.get_channel(discord_channel_id)

    if channel is None:
        print(f"Fehler: Konnte den Channel mit ID {discord_channel_id} nicht finden.")
        return

    # Abonnierte Kanäle abrufen
    subscribed_channels = get_subscribed_channels()

    if not subscribed_channels:
        await channel.send("Keine abonnierten Kanäle gefunden.")
        return

    # Neueste Videos der abonnierten Kanäle abrufen
    latest_videos = get_latest_videos_from_channels(subscribed_channels)

    if latest_videos:
        message = "Neue Videos von abonnierten Kanälen:\n" + ''.join(latest_videos)
        await send_long_message(channel, message)
    else:
        await channel.send("Keine neuen Videos von abonnierten Kanälen.")

# Funktion, um die Nachricht in Teile zu zerlegen, wenn sie zu lang ist
async def send_long_message(channel, message):
    max_length = 2000  # Discord Nachrichtenlänge ist maximal 2000 Zeichen pro Nachricht
    if len(message) <= max_length:
        await channel.send(message)
    else:
        # Teile die Nachricht in kleinere Blöcke auf
        for i in range(0, len(message), max_length):
            await channel.send(message[i:i + max_length])

# Event: Der Bot empfängt eine Nachricht
@bot.event
async def on_message(message):
    # Ignoriere Nachrichten vom Bot selbst
    if message.author == bot.user:
        return

    # Wenn die Nachricht mit '!aiden' beginnt, sende sie an den Ollama-Server
    if message.content.startswith("!aiden"):
        user_message = message.content[len("!aiden "):]  # Entferne das Präfix '!aiden'
        await message.channel.send("Verarbeite Anfrage...")

        # Sende die Nachricht an den Ollama-Server
        response = send_to_ollama(user_message)

        # Überprüfe, ob die Antwort leer ist
        if response.strip():  # Nur senden, wenn die Antwort nicht leer ist
            await message.channel.send(response)
        else:
            print("Leere Antwort vom Ollama-Server erhalten, Nachricht wird nicht gesendet.")

# Funktion, um eine Anfrage an den Ollama-Server zu senden
def send_to_ollama(user_message):
    try:
        # Überprüfe, ob OLLAMA_URL korrekt ist und keine Kommentare enthält
        if not OLLAMA_URL:
            return "Fehler: Ollama-Server-URL nicht konfiguriert."
        
        # Definiere den Bot-Prompt mit Namen, Verhalten und der Anweisung, auf Deutsch zu antworten
        bot_identity = (
            "Du heißt Bot. Du bist ein freundlicher und hilfsbereiter Assistent mit viel Humor. "
            "Du antwortest immer auf Deutsch."
        )
        
        # Kombiniere den Identitäts-Prompt mit der Benutzernachricht
        prompt = f"{bot_identity}\nBenutzer: {user_message}\nAiden:"
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",  # Füge die URL korrekt zusammen
            json={"model": OLLAMA_MODEL, "prompt": prompt},
            stream=True  # Wir aktivieren das Streaming, um stückweise die Antwort zu bekommen
        )
        response.raise_for_status()

        # Hier speichern wir die gesamte zusammengesetzte Antwort
        full_response = ""

        # Antwort stückweise verarbeiten
        for line in response.iter_lines():
            if line:  # Überspringe leere Zeilen
                line_data = line.decode('utf-8')
                print(f"Empfangene Zeile: {line_data}")  # Debugging: Zeige jede empfangene Zeile

                # Versuche, jede Zeile als JSON zu parsen
                try:
                    data = json.loads(line_data)  # Verwende das Standard-JSON-Modul
                    if 'response' in data:
                        full_response += data['response']  # Füge den Text der Antwort hinzu
                except ValueError as e:
                    print(f"Fehler beim Verarbeiten von JSON: {e}")
        
        # Gib die gesamte Antwort zurück
        return full_response.strip() if full_response else "Keine Antwort erhalten."
        
    except requests.exceptions.RequestException as e:
        return f"Fehler bei der Anfrage an den Ollama-Server: {e}"

# Event: Bot ist bereit
@bot.event
async def on_ready():
    print(f'Bot {bot.user} ist bereit!')
    check_twitch.start()  # Starte die regelmäßige Überprüfung von Twitch
    check_youtube_updates.start()  # Starte die regelmäßige Abfrage für YouTube

# Starte den Bot
bot.run(DISCORD_TOKEN)
