from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import torch
from diffusers import EulerDiscreteScheduler, StableDiffusionPipeline
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    r"D:\ai image project\ai project\realismByStableYogi_sd15V9.safetensors",
)
DEVICE = os.getenv("DEVICE", "cuda")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

STYLE_PRESETS = [
    {"id": "none", "name": "None", "prompt_suffix": ""},
    {"id": "cinematic", "name": "Cinematic", "prompt_suffix": "cinematic lighting, film still, high detail"},
    {"id": "photoreal", "name": "Photoreal", "prompt_suffix": "photorealistic, natural light, 8k details"},
    {"id": "anime", "name": "Anime", "prompt_suffix": "anime style, clean lines, vibrant colors"},
]

pipe: StableDiffusionPipeline | None = None


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text prompt for image generation")
    negative_prompt: str | None = Field(default=None)
    num_inference_steps: int = Field(default=30, ge=1, le=150)
    guidance_scale: float = Field(default=3.0, ge=1.0, le=30.0)
    height: int = Field(default=512, ge=256, le=1024)
    width: int = Field(default=512, ge=256, le=1024)
    seed: int | None = Field(default=None, ge=0)


class BatchGenerateRequest(GenerateRequest):
    num_images: int = Field(default=1, ge=1, le=16)


class GenerateResponse(BaseModel):
    image_url: str
    file_name: str
    seed: int


class GeneratedImageItem(BaseModel):
    file_name: str
    image_url: str


class ImageMetadata(BaseModel):
    file_name: str
    image_url: str
    size_bytes: int
    created_time: str
    modified_time: str
    seed: int | None = None


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[str]


def _validate_generate_request(req: GenerateRequest) -> list[str]:
    errors: list[str] = []
    if req.height % 8 != 0 or req.width % 8 != 0:
        errors.append("height and width must be multiples of 8")
    return errors


def _metadata_path_for(file_path: Path) -> Path:
    return file_path.with_suffix(file_path.suffix + ".json")


def _save_metadata(file_path: Path, seed: int, req: GenerateRequest) -> None:
    payload = {
        "seed": seed,
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt,
        "num_inference_steps": req.num_inference_steps,
        "guidance_scale": req.guidance_scale,
        "height": req.height,
        "width": req.width,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _metadata_path_for(file_path).write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _read_seed_from_metadata(file_path: Path) -> int | None:
    metadata_path = _metadata_path_for(file_path)
    if not metadata_path.exists():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        seed = metadata.get("seed")
        return int(seed) if isinstance(seed, int) else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _list_image_files() -> list[Path]:
    return sorted(
        [p for p in OUTPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _resolve_output_image(file_name: str) -> Path:
    if Path(file_name).name != file_name:
        raise HTTPException(status_code=400, detail="Invalid file_name")
    target = (OUTPUT_DIR / file_name).resolve()
    output_resolved = OUTPUT_DIR.resolve()
    if not str(target).startswith(str(output_resolved)):
        raise HTTPException(status_code=400, detail="Invalid file_name")
    if not target.exists() or not target.is_file() or target.suffix.lower() not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Image not found")
    return target


def _generate_one(req: GenerateRequest) -> GenerateResponse:
    if pipe is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    validation_errors = _validate_generate_request(req)
    if validation_errors:
        raise HTTPException(status_code=400, detail=", ".join(validation_errors))

    seed = req.seed if req.seed is not None else int(torch.seed() % (2**31))
    generator_device = app.state.device if app.state.device != "cpu" else "cpu"
    generator = torch.Generator(device=generator_device).manual_seed(seed)

    with torch.inference_mode():
        result = pipe(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            num_inference_steps=req.num_inference_steps,
            guidance_scale=req.guidance_scale,
            height=req.height,
            width=req.width,
            generator=generator,
        )

    image = result.images[0]
    file_name = f"{uuid.uuid4().hex}.png"
    save_path = OUTPUT_DIR / file_name
    image.save(save_path)
    _save_metadata(save_path, seed, req)

    return GenerateResponse(
        image_url=f"/outputs/{file_name}",
        file_name=file_name,
        seed=seed,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipe

    if not Path(MODEL_PATH).exists():
        raise RuntimeError(f"MODEL_PATH does not exist: {MODEL_PATH}")

    use_fp16 = DEVICE.startswith("cuda") and torch.cuda.is_available()
    dtype = torch.float16 if use_fp16 else torch.float32
    target_device = DEVICE if use_fp16 else "cpu"

    pipe = StableDiffusionPipeline.from_single_file(
        MODEL_PATH,
        torch_dtype=dtype,
        safety_checker=None,
        requires_safety_checker=False,
        local_files_only=True,
    )
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(target_device)

    app.state.device = target_device
    app.state.dtype = str(dtype)

    yield

    pipe = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(title="Stable Diffusion FastAPI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


@app.get("/health")
def health_check():
    loaded = pipe is not None
    return {
        "status": "ok" if loaded else "loading",
        "device": getattr(app.state, "device", None),
        "dtype": getattr(app.state, "dtype", None),
        "model_path": MODEL_PATH,
    }


@app.get("/health/detailed")
def health_detailed():
    cuda_available = torch.cuda.is_available()
    vram = None
    if cuda_available:
        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info()
            vram = {"free_bytes": free_bytes, "total_bytes": total_bytes}
        except RuntimeError:
            vram = None
    return {
        "status": "ok" if pipe is not None else "loading",
        "model_loaded": pipe is not None,
        "model_path": MODEL_PATH,
        "device": getattr(app.state, "device", None),
        "dtype": getattr(app.state, "dtype", None),
        "cuda_available": cuda_available,
        "cuda_device_count": torch.cuda.device_count() if cuda_available else 0,
        "scheduler": pipe.scheduler.__class__.__name__ if pipe is not None else None,
        "vram": vram,
    }


@app.post("/generate", response_model=GenerateResponse)
def generate_image(req: GenerateRequest):
    return _generate_one(req)


@app.post("/generate/batch", response_model=list[GenerateResponse])
def generate_images_batch(req: BatchGenerateRequest):
    base_seed = req.seed if req.seed is not None else int(torch.seed() % (2**31))
    responses: list[GenerateResponse] = []
    for i in range(req.num_images):
        item_req = req.model_copy(update={"seed": base_seed + i})
        responses.append(_generate_one(item_req))
    return responses


@app.post("/generate/validate", response_model=ValidationResponse)
def validate_generate_request(req: GenerateRequest):
    errors = _validate_generate_request(req)
    return ValidationResponse(valid=len(errors) == 0, errors=errors)


@app.get("/generated-images", response_model=list[GeneratedImageItem])
def get_generated_images():
    image_files = _list_image_files()
    return [
        GeneratedImageItem(
            file_name=img.name,
            image_url=f"/outputs/{img.name}",
        )
        for img in image_files
    ]


@app.get("/generated-images/{file_name}", response_model=ImageMetadata)
def get_generated_image(file_name: str):
    image_path = _resolve_output_image(file_name)
    stats = image_path.stat()
    return ImageMetadata(
        file_name=image_path.name,
        image_url=f"/outputs/{image_path.name}",
        size_bytes=stats.st_size,
        created_time=datetime.fromtimestamp(stats.st_ctime, tz=timezone.utc).isoformat(),
        modified_time=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
        seed=_read_seed_from_metadata(image_path),
    )


@app.get("/generated-images/{file_name}/download")
def download_generated_image(file_name: str):
    image_path = _resolve_output_image(file_name)
    return FileResponse(path=image_path, filename=image_path.name, media_type="application/octet-stream")


@app.delete("/generated-images/{file_name}")
def delete_generated_image(file_name: str):
    image_path = _resolve_output_image(file_name)
    metadata_path = _metadata_path_for(image_path)
    image_path.unlink(missing_ok=True)
    metadata_path.unlink(missing_ok=True)
    return {"deleted": True, "file_name": file_name}


@app.delete("/generated-images")
def clear_generated_images():
    deleted = 0
    for image_path in _list_image_files():
        metadata_path = _metadata_path_for(image_path)
        image_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)
        deleted += 1
    return {"deleted": deleted}


@app.get("/models")
def get_models():
    return {"models": [{"id": "default", "name": Path(MODEL_PATH).stem, "path": MODEL_PATH}]}


@app.get("/presets")
def get_presets():
    return {"presets": STYLE_PRESETS}


@app.get("/stats")
def get_stats():
    image_files = _list_image_files()
    total_size = sum(p.stat().st_size for p in image_files)
    last_generated_time = (
        datetime.fromtimestamp(image_files[0].stat().st_mtime, tz=timezone.utc).isoformat()
        if image_files
        else None
    )
    return {
        "count": len(image_files),
        "disk_usage_bytes": total_size,
        "last_generated_time": last_generated_time,
    }
