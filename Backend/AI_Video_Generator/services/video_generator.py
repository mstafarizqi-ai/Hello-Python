# AI Video Generator
# ------------------
# This simple application creates a short AI-style promotional video based on a text prompt.
# It uses FastAPI for the web UI and gTTS + MoviePy to generate the video locally.

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from services.video_generator import generate_video_from_prompt

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
VIDEOS_DIR = STATIC_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AI Video Creator",
    description="Create short AI-powered videos from a text prompt.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_video(
    title: str = Form(...),
    prompt: str = Form(...),
    duration: int = Form(15),
    style: str = Form("cinematic"),
    orientation: str = Form("16:9"),
):
    if not title.strip():
        return JSONResponse(status_code=400, content={"detail": "El título es obligatorio."})

    if not prompt.strip():
        return JSONResponse(status_code=400, content={"detail": "La descripción del video es obligatoria."})

    if duration < 5 or duration > 60:
        return JSONResponse(
            status_code=400,
            content={"detail": "La duración debe estar entre 5 y 60 segundos."},
        )

    video_name = generate_video_from_prompt(
        title=title,
        prompt=prompt,
        duration=duration,
        style=style,
        orientation=orientation,
    )

    return {
        "success": True,
        "title": title,
        "video_url": f"/static/videos/{video_name}",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
