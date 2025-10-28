from ultralytics import YOLO
from PIL import Image
import io
import numpy as np
import asyncio
import os
from pathlib import Path

model = YOLO("AI/yolo11n.pt")
BASE_DIR = Path(__file__).resolve().parents[1]  # 프로젝트 루트(예: .../Edu-Community-FastAPI-BE)

async def generate_ai_response(image_input) -> str:
    def _run(img_in):
        # bytes 입력 처리
        if isinstance(img_in, (bytes, bytearray)):
            img = Image.open(io.BytesIO(img_in)).convert("RGB")

        # 문자열/Path 입력 처리
        elif isinstance(img_in, (str, os.PathLike)):
            p = str(img_in)

            # URL 스타일 경로 → 파일시스템 경로로 매핑
            if p.startswith("/public/"):
                fs_path = BASE_DIR / p.lstrip("/")
            else:
                fs_path = Path(p)
                if not fs_path.is_absolute():
                    fs_path = BASE_DIR / fs_path

            if not fs_path.exists():
                raise FileNotFoundError(f"Image file not found: {fs_path}")

            img = Image.open(fs_path).convert("RGB")

        else:
            raise TypeError(f"Unsupported image_input type: {type(img_in)}")

        arr = np.array(img)
        if arr.dtype != np.uint8:
            arr = arr.astype(np.uint8)

        results = model(arr)

        detections = []
        design_str = None
        for r in results:
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue
            xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes, "xyxy") else np.array([])
            conf = boxes.conf.cpu().numpy() if hasattr(boxes, "conf") else np.array([])
            cls = boxes.cls.cpu().numpy() if hasattr(boxes, "cls") else np.array([])

            for b, c, cl in zip(xyxy, conf, cls):
                label = model.names.get(int(cl), str(int(cl))) if hasattr(model, "names") else str(int(cl))
                detections.append({
                    "bbox": [float(b[0]), float(b[1]), float(b[2]), float(b[3])],
                    "confidence": float(c),
                    "class_id": int(cl),
                    "label": label
                })
                design_str = f"""
                                confidence: {float(c)},
                                class_id: {int(cl)},
                                label: {label},
                            """

        return design_str

    return await asyncio.to_thread(_run, image_input)