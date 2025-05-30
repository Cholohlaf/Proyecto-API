import os
import csv
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise Exception("No se encontró API_KEY en el archivo .env")

youtube = build('youtube', 'v3', developerKey=API_KEY)

CHANNEL_ID = 'UCRijo3ddMTht_IHyNSNXpNQ'  # Luisito Comunica

def get_uploads_playlist_id(channel_id):
    res = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    return res['items'][0]['contentDetails']['relatedPlaylists']['uploads']

def get_videos_from_playlist(playlist_id, max_videos=1):
    videos = []
    next_page_token = None

    while len(videos) < max_videos:
        res = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in res['items']:
            video_id = item['snippet']['resourceId']['videoId']
            videos.append(video_id)
            if len(videos) >= max_videos:
                break

        next_page_token = res.get('nextPageToken')
        if not next_page_token:
            break

    return videos

def get_comments(video_id, max_total, already_collected):
    comments = []
    next_page_token = None

    while len(comments) + already_collected < max_total:
        try:
            res = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat='plainText'
            ).execute()
        except Exception as e:
            print(f"⚠️ No se pudieron obtener comentarios para el video {video_id}: {e}")
            break

        for item in res['items']:
            snippet = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'video_id': video_id,
                'published_at': snippet['publishedAt'],
                'comment': snippet['textDisplay']
            })
            if len(comments) + already_collected >= max_total:
                break

        next_page_token = res.get('nextPageToken')
        if not next_page_token:
            break

    return comments

def save_to_csv(data, filename="comments.csv"):
    # Obtener la ruta al directorio padre del archivo actual (fuera de /code)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(parent_dir, "data")

    # Crear la carpeta si no existe
    os.makedirs(data_dir, exist_ok=True)

    filepath = os.path.join(data_dir, filename)
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["video_id", "published_at", "comment"])
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Archivo CSV guardado como: {filepath}")

def main():
    max_comments = 500
    collected = []

    print("🔍 Buscando videos del canal Luisito Comunica...")
    playlist_id = get_uploads_playlist_id(CHANNEL_ID)
    videos = get_videos_from_playlist(playlist_id, max_videos=50)

    for video_id in videos:
        if len(collected) >= max_comments:
            break
        print(f"📥 Extrayendo comentarios de video {video_id}...")
        comments = get_comments(video_id, max_total=max_comments, already_collected=len(collected))
        collected.extend(comments)

    print(f"\n📊 Total de comentarios recolectados: {len(collected)}")
    save_to_csv(collected)

if __name__ == "__main__":
    main()