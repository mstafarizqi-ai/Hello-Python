import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from services.replicate import ReplicateError, create_prediction, get_prediction

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="AI Video Studio",
    description="Create videos with a configured video-generation model on Replicate.",
    version="2.0.0",
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class VideoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=8, max_length=2000)
    style: str = Field(default="cinematic", max_length=30)
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16|1:1)$")
    duration: int = Field(default=5, ge=3, le=15)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "configured": bool(os.getenv("REPLICATE_API_TOKEN") and os.getenv("REPLICATE_MODEL")),
        },
    )


@app.get("/api/config")
async def config():
    return {"configured": bool(os.getenv("REPLICATE_API_TOKEN") and os.getenv("REPLICATE_MODEL"))}


@app.post("/api/videos", status_code=202)
async def create_video(request: VideoRequest):
    if not os.getenv("REPLICATE_API_TOKEN"):
        raise HTTPException(503, "أضف REPLICATE_API_TOKEN إلى ملف .env لتفعيل توليد الفيديو.")
    if not os.getenv("REPLICATE_MODEL"):
        raise HTTPException(503, "أضف اسم نموذج الفيديو إلى REPLICATE_MODEL في ملف .env.")

    styles = {
        "cinematic": "cinematic lighting, polished film composition",
        "commercial": "premium commercial, crisp product-focused composition",
        "anime": "expressive anime illustration, dynamic composition",
        "documentary": "natural documentary cinematography, realistic details",
    }
    if request.style not in styles:
        raise HTTPException(422, "النمط المحدد غير صالح.")

    enhanced_prompt = (
        f"{request.prompt.strip()}. Visual direction: {styles[request.style]}. "
        "High quality, coherent motion, no subtitles or watermarks."
    )
    try:
        prediction = await create_prediction(
            prompt=enhanced_prompt,
            aspect_ratio=request.aspect_ratio,
            duration=request.duration,
        )
    except ReplicateError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc

    return {
        "id": prediction["id"],
        "status": prediction.get("status", "starting"),
        "title": request.title.strip(),
        "status_url": f"/api/videos/{prediction['id']}",
    }


@app.get("/api/videos/{prediction_id}")
async def video_status(prediction_id: str):
    if not prediction_id or len(prediction_id) > 100 or not all(c.isalnum() or c in "-_" for c in prediction_id):
        raise HTTPException(400, "معرّف المهمة غير صالح.")
    try:
        prediction = await get_prediction(prediction_id)
    except ReplicateError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc

    output = prediction.get("output")
    video_url = output if isinstance(output, str) else next(
        (item for item in output or [] if isinstance(item, str) and item.startswith("https://")), None
    )
    return {
        "id": prediction.get("id"),
        "status": prediction.get("status"),
        "video_url": video_url,
        "error": prediction.get("error"),
    }
