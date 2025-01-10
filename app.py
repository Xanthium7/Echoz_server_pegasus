import requests
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

REQUEST_URL = "https://api.acedata.cloud/suno/audios"
AUTH_TOKEN = "Bearer 93607bddd3ba448aa1eb74fdeaab967c"


def create_music(prompt: str):
    payload = {
        "action": "generate",
        "prompt": prompt,
        "model": "chirp-v2-xxl-alpha",
        # "lyric": "required lyrics (if any, optional)",
        # "custom": False,
        "instrumental": False,
        "style": "pop, dreamy, ethereal"
        # "style_negative": ""
    }
    headers = {
        "authorization": AUTH_TOKEN,
        "content-type": "application/json"
    }

    response = requests.post(REQUEST_URL, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        video_urls = [item['video_url']
                      for item in data.get('data', []) if 'video_url' in item]
        os.makedirs('videos', exist_ok=True)
        for idx, video_url in enumerate(video_urls):
            video_response = requests.get(video_url)
            if video_response.status_code == 200:
                file_path = os.path.join('videos', f'video_{idx}.mp4')
                with open(file_path, 'wb') as f:
                    f.write(video_response.content)
                print(f"Saved: {file_path}")
            else:
                print(f"Failed to download {video_url}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


create_music("music about helicopter")
