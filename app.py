import requests
import os
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv, find_dotenv

# Find the .env file
dotenv_path = find_dotenv()
print(f"Loading environment variables from: {dotenv_path}")

# Load the .env file
load_dotenv(dotenv_path)
REQUEST_URL = "https://api.acedata.cloud/suno/audios"
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

print("AUTH_TOKEN: ", AUTH_TOKEN)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
lyrics = []


def create_music(prompt: str, genre: str):
    global lyrics
    payload = {
        "action": "generate",
        "prompt": prompt,
        "model": "chirp-v2-xxl-alpha",
        # "lyric": "required lyrics (if any, optional)",
        # "custom": False,

        "instrumental": False,
        "style": genre,
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
        lyrics = [item['lyric']
                  for item in data.get('data', []) if 'lyric' in item]

        saved_files = []

        os.makedirs('videos', exist_ok=True)
        for idx, video_url in enumerate(video_urls):
            for attempt in range(1, 6):  # Retry up to 5 times
                print(f"Attempt {attempt} to download video {idx}")
                video_response = requests.get(video_url)
                if video_response.status_code == 200:
                    file_path = os.path.join('videos', f'video_{idx}.mp4')
                    with open(file_path, 'wb') as f:
                        f.write(video_response.content)
                    print(f"Saved: {file_path}")
                    saved_files.append(file_path)
                    break  # Exit the retry loop if successful
                else:
                    print(
                        f"Failed to download {video_url} on attempt {attempt}")
                    if attempt == 5:
                        print(
                            f"Giving up on downloading {video_url} after 5 attempts")

        return {
            "videos": saved_files,
            "lyrics": lyrics
        }
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return []


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
    return chat_completion.choices[0].message.content


def gen_image_prompts(lyrics: str):
    # Generate image prompts based on the lyrics
    prompt = f'''
    You are an AI tasked with creating image generation prompts based on song lyrics. Your input will be a set of song lyrics, and your output should be a list of prompts that can be used to generate captivating, satisfying, and attention-grabbing images that visually represent the content and emotions of the lyrics. The goal is to create imagery that is particularly engaging for autistic students, using stunning visuals to draw their attention.

    Instructions:
    1. Analyze the given song lyrics for key themes, imagery, and emotional undertones.
    2. Create a descriptive prompt for each verse, chorus, bridge, and outro (if applicable) that captures the essence of the lyrics.
    3. Ensure that the prompts are detailed enough to guide an image generation model to create visually compelling, satisfying, and accurate representations of the lyrics.
    4. Focus on creating imagery that is visually stunning and captivating, with elements that are likely to grab and hold the attention of autistic students.
    5. Format the output as a JSON array, with each element being a string prompt corresponding to a section of the lyrics.
    IMPORTANT: Return only the OUTPUT Prompts in the output format and do not include any other text.
    IMPORTANT: PREFIX every image prompt with 'IMAGE_PROMPT'
    

    SONG LYRICS: {lyrics}

    Remember to balance descriptive detail with emotional resonance. Your prompts should be both informative and evocative, suitable for guiding an image generation model to create stunning and attention-grabbing visuals.
    '''

    prompts = []

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    output = chat_completion.choices[0].message.content
    # print(output)
    return output


# lyric = genLyrics("Car riding a dog on a sunny day")
# pormpts = gen_image_prompts(lyric)
# print(pormpts)
