import requests
import os
import google.generativeai as genai
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

REQUEST_URL = "https://api.acedata.cloud/suno/audios"
AUTH_TOKEN = "Bearer 93607bddd3ba448aa1eb74fdeaab967c"


client = Groq(api_key=os.getenv("GROQ_API_KEY"))


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
    print("Generating your tones, please wait for 30 seconds...")
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


def genLyrics(r_context: str):
    prompt = f'''
    You are an AI lyricist tasked with creating song lyrics based on educational content. Your input will be a chunk of textbook data, and your output should be emotionally resonant song lyrics that capture the essence of the educational material.

    Instructions:
    1. Analyze the given textbook data for key concepts, themes, and important information.
    2. Identify the emotional undertones or implications of the material.
    3. Create lyrics that convey the educational content in a poetic and musical format.
    4. Ensure that the lyrics are easy to sing and have a catchy melody.
    
    
    5. Structure the lyrics into verses, chorus, and optionally a bridge.
    6. Use metaphors, imagery, and emotional language to make the educational content more engaging and memorable.
    7. Ensure that the lyrics maintain scientific accuracy while being creatively expressed.
    8. Format the output in JSON structure as shown in the example below.
    9. The lyrics should not have complicated scientific jargon, but should be accessible and engaging for a general audience.

    Your lyrics should follow this structure:
    - 2-4 verses
    - A chorus (repeated 1-2 times)
    - Optionally, a bridge
    - An outro (if appropriate)

    Example output format:

    ```json
    [Verse 1]
    (4 lines of verse)

    [Verse 2]
    (4 lines of verse)

    [Chorus]
    (4 lines of chorus)

    [Bridge]
    (4 lines of bridge, if applicable)

    [Chorus]
    (Repeat of chorus)

    [Outro]
    (2-4 lines to conclude the song)
    ```
    TEXTBOOK CONTEXT: {r_context}

    Remember to balance educational content with emotional resonance and musical flow. Your lyrics should be both informative and engaging, suitable for being set to music by a separate AI system.
    '''

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    print(chat_completion.choices[0].message.content)


genLyrics("The laws of thermodynamics are fundamental principles that govern the behavior of energy and heat transfer in physical systems. They describe how energy is conserved, how it can be transformed, and the direction in which processes occur naturally, ensuring that energy moves from more useful forms to less useful ones and that systems progress towards equilibrium.")
