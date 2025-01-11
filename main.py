from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from fastapi.responses import JSONResponse
from langchain_helper import get_relevent_context_from_db
from generate_embeddings import gen_embd
from app import create_music, genLyrics, gen_image_prompts

import os

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/music", StaticFiles(directory="music"), name="music")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/uploads", StaticFiles(directory="uploads"),
          name="uploads")  # Mount uploads directory


class MusicRequest(BaseModel):
    prompt: str


@app.get("/")
def read_root():
    return {"message": "Welcome to the Music Generation API!"}


@app.post("/create-music")
def generate_music(music_request: MusicRequest):
    print("Received request for music generation.")
    try:
        result = create_music(music_request.prompt)
        if not result["videos"]:
            raise HTTPException(
                status_code=500, detail="Music generation failed.")

        video_urls = [
            f"/videos/{os.path.basename(file)}" for file in result["videos"]]
        lyrics = result["lyrics"]
        prompts = gen_image_prompts(lyrics)

        return JSONResponse(content={"message": "Music generation initiated.", "videos": video_urls, "img_prompts": prompts}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    try:

        os.makedirs('uploads', exist_ok=True)

        file_location = os.path.join('uploads', file.filename)

        with open(file_location, "wb") as f:
            contents = await file.read()
            f.write(contents)
        with open(file_location, "r", encoding="utf-8") as f:
            r_context = f.read()

        # Generate lyrics
        lyrics = genLyrics(r_context)

        return JSONResponse(content={"lyrics": lyrics}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"message": "File upload failed", "error": str(e)}, status_code=500)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
