from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services.video_generator import generate_video_from_prompt

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
VIDEO_DIR = STATIC_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Video Creator", description="Create short videos from a text prompt.")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate(
    title: str = Form(...),
    prompt: str = Form(...),
    duration: int = Form(15),
    style: str = Form("cinematic"),
    orientation: str = Form("16:9"),
):
    title, prompt = title.strip(), prompt.strip()
    if not title or not prompt:
        return JSONResponse(status_code=400, content={"detail": "أدخل العنوان ووصف الفيديو."})
    if not 5 <= duration <= 60:
        return JSONResponse(status_code=400, content={"detail": "المدة يجب أن تكون من 5 إلى 60 ثانية."})
    if style not in {"cinematic", "futuristic", "minimal", "business"}:
        return JSONResponse(status_code=400, content={"detail": "النمط غير صالح."})
    if orientation not in {"16:9", "9:16", "1:1"}:
        return JSONResponse(status_code=400, content={"detail": "التنسيق غير صالح."})

    try:
        filename = generate_video_from_prompt(title, prompt, duration, style, orientation)
    except Exception as exc:
        return JSONResponse(status_code=500, content={"detail": f"تعذر إنشاء الفيديو: {exc}"})
    return {"success": True, "title": title, "video_url": f"/static/videos/{filename}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
