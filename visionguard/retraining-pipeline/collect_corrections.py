"""Collect inspector corrections from PostgreSQL into a YOLO training set.

Each unused correction becomes a labeled training example:
  verdict=confirm  -> the model's own boxes are correct; keep them as labels
  verdict=correct  -> use the inspector's corrected boxes/labels
  verdict=reject   -> false detection; emit an empty label (negative example)

Images are pulled from MinIO via the detection's image_ref. After writing,
corrections are marked used_for_training so the next run only sees new feedback.

    python collect_corrections.py            # collect + mark used
    python collect_corrections.py --dry-run  # report counts only
"""
from __future__ import annotations

import argparse
import io
import json

import psycopg
from minio import Minio
from PIL import Image

from config import (
    CLASS_NAMES,
    DATASET_DIR,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    POSTGRES_DSN,
)


def _minio() -> Minio:
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
                 secret_key=MINIO_SECRET_KEY, secure=MINIO_SECURE)


def _fetch_image(client: Minio, image_ref: str) -> Image.Image | None:
    if not image_ref.startswith("minio://"):
        return None
    bucket, _, key = image_ref[len("minio://"):].partition("/")
    try:
        resp = client.get_object(bucket, key)
        return Image.open(io.BytesIO(resp.read())).convert("RGB")
    except Exception:  # noqa: BLE001
        return None


def _yolo_lines(boxes: list[dict], w: int, h: int) -> list[str]:
    """Convert [{class_name, bbox:[x0,y0,x1,y1]}] (pixels) to YOLO label rows."""
    rows = []
    for b in boxes:
        name = b.get("class_name", "none")
        if name == "none" or name not in CLASS_NAMES:
            continue
        cls = CLASS_NAMES.index(name)
        x0, y0, x1, y1 = b["bbox"]
        cx, cy = (x0 + x1) / 2 / w, (y0 + y1) / 2 / h
        bw, bh = (x1 - x0) / w, (y1 - y0) / h
        rows.append(f"{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    return rows


def collect(dry_run: bool = False) -> int:
    img_dir = DATASET_DIR / "images" / "train"
    lbl_dir = DATASET_DIR / "labels" / "train"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    client = _minio()
    written = 0
    with psycopg.connect(POSTGRES_DSN) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.verdict, c.corrected_boxes,
                   d.image_ref, d.detections
            FROM corrections c JOIN detections d ON d.id = c.detection_id
            WHERE c.used_for_training = false
            ORDER BY c.id
        """)
        rows = cur.fetchall()
        print(f"{len(rows)} unused corrections")
        if dry_run:
            return len(rows)

        for cid, verdict, corrected, image_ref, det in rows:
            img = _fetch_image(client, image_ref)
            if img is None:
                print(f"  skip correction {cid}: cannot fetch {image_ref}")
                continue
            w, h = img.size
            if verdict == "confirm":
                boxes = det if isinstance(det, list) else json.loads(det)
            elif verdict == "correct":
                boxes = corrected if isinstance(corrected, list) else json.loads(corrected)
            else:  # reject -> negative example
                boxes = []

            stem = f"corr_{cid}"
            img.save(img_dir / f"{stem}.png")
            (lbl_dir / f"{stem}.txt").write_text("\n".join(_yolo_lines(boxes, w, h)))
            cur.execute("UPDATE corrections SET used_for_training = true WHERE id = %s",
                        (cid,))
            written += 1

        conn.commit()
    print(f"wrote {written} training examples -> {DATASET_DIR}")
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    print(collect(ap.parse_args().dry_run))
