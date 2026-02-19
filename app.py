from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response
from PIL import Image, ImageOps, ImageDraw
import io
import os

app = FastAPI()

EMBLEM_PATH = os.environ.get("SOCIAL_HOUSE_EMBLEM_PATH", "social_house_emblem.png")

def circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    return mask

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/compose")
async def compose(
    input_image: UploadFile = File(...),
    output_size: int = Form(1024),
    fit: str = Form("cover"),
):
    user_bytes = await input_image.read()
    user_img = Image.open(io.BytesIO(user_bytes)).convert("RGBA")

    emblem = Image.open(EMBLEM_PATH).convert("RGBA")
    emblem = emblem.resize((output_size, output_size), Image.Resampling.LANCZOS)

    if fit == "contain":
        face = ImageOps.contain(user_img, (output_size, output_size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
        x = (output_size - face.size[0]) // 2
        y = (output_size - face.size[1]) // 2
        canvas.paste(face, (x, y))
        face = canvas
    else:
        face = ImageOps.fit(
            user_img,
            (output_size, output_size),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.35),
        )

    mask = circle_mask(output_size)
    face_circle = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    face_circle.paste(face, (0, 0), mask)

    out = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    out.alpha_composite(face_circle)
    out.alpha_composite(emblem)

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
