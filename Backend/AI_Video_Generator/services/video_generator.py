import re
import uuid
from pathlib import Path

from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "static" / "videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PALETTES = {
    "cinematic": ((12, 18, 38), (58, 45, 98)),
    "futuristic": ((3, 32, 54), (0, 130, 150)),
    "minimal": ((28, 33, 42), (76, 86, 106)),
    "business": ((12, 45, 53), (25, 117, 103)),
}


def _font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _wrap(text: str, max_chars: int = 34) -> list[str]:
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) + (1 if line else 0) > max_chars and line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines[:5]


def _make_scene(title: str, text: str, style: str, size: tuple[int, int], index: int) -> Path:
    width, height = size
    start, end = PALETTES[style]
    image = Image.new("RGB", size)
    pixels = image.load()
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(start[i] * (1 - ratio) + end[i] * ratio) for i in range(3))
        for x in range(width):
            pixels[x, y] = color

    draw = ImageDraw.Draw(image)
    margin = int(width * 0.09)
    draw.rounded_rectangle((margin, margin, width - margin, height - margin), radius=28, outline=(255, 255, 255), width=2)
    title_font = _font(max(24, int(width * 0.065)))
    body_font = _font(max(17, int(width * 0.032)))
    title_lines = _wrap(title, max(16, int(width / 30)))
    body_lines = _wrap(text, max(20, int(width / 20)))
    y = int(height * 0.33)
    for line in title_lines:
        draw.text((margin + 30, y), line, font=title_font, fill=(255, 255, 255))
        y += int(height * 0.09)
    y += int(height * 0.035)
    for line in body_lines:
        draw.text((margin + 30, y), line, font=body_font, fill=(220, 230, 240))
        y += int(height * 0.055)

    filename = OUTPUT_DIR / f"scene_{uuid.uuid4().hex}_{index}.jpg"
    image.save(filename, quality=90)
    return filename


def generate_video_from_prompt(title: str, prompt: str, duration: int, style: str, orientation: str) -> str:
    dimensions = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (900, 900)}
    size = dimensions[orientation]
    sentences = [part.strip() for part in re.split(r"[.!?\n]+", prompt) if part.strip()]
    scenes_text = sentences[:4] or [prompt]
    scene_duration = duration / len(scenes_text)
    scene_files = []
    clips = []
    audio_path = OUTPUT_DIR / f"voice_{uuid.uuid4().hex}.mp3"
    output_name = f"video_{uuid.uuid4().hex}.mp4"
    output_path = OUTPUT_DIR / output_name

    try:
        for index, scene_text in enumerate(scenes_text):
            scene_path = _make_scene(title if index == 0 else f"{title} · {index + 1}", scene_text, style, size, index)
            scene_files.append(scene_path)
            clips.append(ImageClip(str(scene_path)).set_duration(scene_duration))

        video = concatenate_videoclips(clips, method="compose")
        try:
            # gTTS provides optional spoken narration; video still renders if network/TTS is unavailable.
            gTTS(text=f"{title}. {prompt}", lang="ar").save(str(audio_path))
            audio = AudioFileClip(str(audio_path))
            video = video.set_audio(audio.set_duration(duration))
        except Exception:
            pass
        video.write_videofile(str(output_path), fps=24, codec="libx264", audio_codec="aac", logger=None)
        video.close()
        return output_name
    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        for path in scene_files:
            path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
