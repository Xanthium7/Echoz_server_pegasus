from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import json
import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from langchain_helper import get_relevent_context_from_db
from generate_embeddings import gen_embd


# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/music", StaticFiles(directory="music"), name="music")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/images", StaticFiles(directory="images"), name="images")

# Constants
url = "http://localhost:3000/api/generate"
api_key = os.environ.get("GROQ_KEY")
openai_api_key = os.environ.get("OPEN_AI_KEY")
ele_ids = []

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)


class MusicPrompt(BaseModel):
    prompt: str


def create_music(prompt: str):
    print("PORMPTT:!!", prompt)
    l = []
    payload = {
        "prompt": prompt,
        "make_instrumental": False,
        "wait_audio": True
    }
    headers = {
        "Content-Type": "application/json"
    }
    print("Generating your tones, please wait for 30 seconds...")
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        data = response.json()
        audio_urls = [item['audio_url']
                      for item in data if 'audio_url' in item]

        if not os.path.exists('music'):
            os.makedirs('music')

        for idx, audio_url in enumerate([audio_urls[0]]):
            print(f"Downloading {audio_url}")
            item_id = audio_url.split('=')[-1]
            ele_ids.append(item_id)
            audio_response = requests.get(audio_url)
            if audio_response.status_code == 200:
                file_path = os.path.join('music', f'audio_{idx}.mp3')
                with open(file_path, 'wb') as audio_file:
                    audio_file.write(audio_response.content)
                print(f"Accessed: {file_path}")
                l.append(file_path)
            else:
                print(f"Failed to download {audio_url}")
    else:
        print("Error:", response.status_code)
        print(response.text)

    return l


def get_req():
    global lyric
    global video_url
    print(ele_ids)
    if ele_ids:
        req_url = f"http://localhost:3000/api/get?ids={ele_ids[0]}"
        response = requests.get(req_url, verify=False)
        if response.status_code == 200:
            data = response.json()
            print(data)
            if data and isinstance(data, list):
                if 'video_url' in data[0]:
                    video_url = f"https://cdn1.suno.ai/{ele_ids[0]}.mp4"
                else:
                    print("Video URL not found in the response.")

                if 'lyric' in data[0]:
                    lyric = data[0]['lyric']
                    print("Lyric:", lyric)
                else:
                    print("Lyric not found in the response.")
            else:
                print("Unexpected data format.")
        else:
            print("Error:", response.status_code)
            print(response.text)
    else:
        print("No audio files were generated.")


def get_image_prompts(lyrics: str):
    print("lyrics: ", lyrics)
    prompt = f"Generate a list of one image prompts each, for each verse in the following lyrics: {lyrics}, (prefix every image prompt with 'IMAGE_PROMPT')"
    prompts = []
    client = Groq(api_key=api_key)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant",
    )
    output = chat_completion.choices[0].message.content
    print(output)

    for line in output.split('\n'):
        if 'IMAGE_PROMPT' in line:
            prompts.append(line)

    return prompts


def genImage(prompt: str):
    response = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="512x512",
        quality="standard",
        n=1,
    )
    return response.data[0].url


def genLyrics(r_context):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f'''
            You are an AI lyricist tasked with creating song lyrics based on educational content. Your input will be a chunk of textbook data, and your output should be emotionally resonant song lyrics that capture the essence of the educational material.

    Instructions:
    1. Analyze the given textbook data for key concepts, themes, and important information.
    2. Identify the emotional undertones or implications of the material.
    3. Create lyrics that convey the educational content in a poetic and musical format.
    4. Structure the lyrics into verses, chorus, and optionally a bridge.
    5. Use metaphors, imagery, and emotional language to make the educational content more engaging and memorable.
    6. Ensure that the lyrics maintain scientific accuracy while being creatively expressed.
    7. Format the output in JSON structure as shown in the example below.
             
    

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
    '''},


        ]

    )
    print(response)


@app.post("/generate")
def generate(music_prompt: MusicPrompt):
    print("triggered")
    prompt = music_prompt.prompt

    # Step 1: Create music
    create_music(prompt)

    # Step 2: Get lyrics
    get_req()

    # Step 3: Generate image prompts
    prompts = get_image_prompts(lyric)
    print("Extracted Prompts:", prompts)

    # Step 4: Generate images
    image_urls = []
    for prompt in prompts:
        image_urls.append(genImage(prompt))
        # image_urls.append("ads")

    os.makedirs('images', exist_ok=True)
    for i, url in enumerate(image_urls):
        response = requests.get(url)
        with open(f'images/image_{i}.jpg', 'wb') as f:
            f.write(response.content)
    print("Completed!")
    return {
        "audio_files": [f'music/audio_{i}.mp3' for i in range(len(ele_ids))],
        "video_files": [video_url],
        "image_files": [f'images/image_{i}.jpg' for i in range(len(image_urls))]
    }


@app.get('/')
def hellow():
    return {"response": "Hello World"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), context: str = Form(...)):
    try:
        # Save the uploaded file
        contents = await file.read()
        file_path = f"uploads/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(contents)

        # Generate embeddings
        doc_count = gen_embd(file_path)

        # Retrieve relevant context using the provided context parameter
        retrieved_context = get_relevent_context_from_db(context)

        # GENRATE SONG LYRIC USING THIS CONTEXT
        genLyrics(retrieved_context)

        # Print the provided context

        return JSONResponse(content={
            "message": "File uploaded successfully",
            "doc_count": doc_count,
            "retrieved_context": retrieved_context
        }, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": "File upload failed", "error": str(e)}, status_code=500)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
