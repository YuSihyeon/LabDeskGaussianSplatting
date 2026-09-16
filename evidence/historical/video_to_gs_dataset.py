#!/usr/bin/env python3
"""
Video -> frames -> COLMAP SfM -> undistort -> Gaussian Splatting dataset folder

Output layout:
OUT/
  frames/                 (raw extracted frames)
  colmap/
    database.db
    sparse/0/             (COLMAP sparse model)
    dense/                (undistorted images + sparse)
  gs_dataset/
    images/               (undistorted images)
    sparse/               (COLMAP sparse model; contains cameras.bin/images.bin/points3D.bin)
"""

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple


def run(cmd: List[str], cwd: Optional[Path] = None) -> None:
    print("\n$", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def ensure_empty_dir(p: Path) -> None:
    if p.exists():
        shutil.rmtree(str(p))
    p.mkdir(parents=True, exist_ok=True)


def extract_frames_ffmpeg(video: Path, out_dir: Path, fps: float, max_frames: int = 0) -> None:
    """
    Extract frames from a video using ffmpeg.
    - fps: frames per second to sample
    - max_frames: if >0, stops after max_frames using -frames:v
    """
    ensure_empty_dir(out_dir)

    out_pattern = out_dir / "%06d.png"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-vf",
        "fps={}".format(fps),
    ]
    if max_frames > 0:
        cmd += ["-frames:v", str(max_frames)]
    cmd += [str(out_pattern)]
    run(cmd)


def write_colmap_camera_params(out_dir: Path, params: str) -> Path:
    """
    Create a COLMAP camera params file (plain text). We keep this as a convenience,
    but COLMAP expects the params string via --ImageReader.camera_params.

    params format depends on camera_model:
      - PINHOLE: fx, fy, cx, cy
      - SIMPLE_PINHOLE: f, cx, cy
      - OPENCV: fx, fy, cx, cy, k1, k2, p1, p2
      - FULL_OPENCV: fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6
      - SIMPLE_RADIAL: f, cx, cy, k
      - RADIAL: f, cx, cy, k1, k2
    """
    out_path = out_dir / "colmap_camera_params.txt"
    out_path.write_text(params.strip() + "\n", encoding="utf-8")
    print("[INFO] Wrote camera params file: {}".format(out_path))
    return out_path


def colmap_sfm(
    images_dir: Path,
    work_dir: Path,
    camera_model: str,
    use_gpu: bool,
    single_camera: bool,
    camera_params: Optional[str],
) -> Tuple[Path, Path]:
    """
    Runs COLMAP:
      1) feature_extractor
      2) exhaustive_matcher
      3) mapper
      4) image_undistorter

    Returns:
      sparse_model_dir = work_dir/colmap/sparse/0 (or first model)
      dense_dir = work_dir/colmap/dense
    """
    colmap_dir = work_dir / "colmap"
    colmap_dir.mkdir(parents=True, exist_ok=True)

    db_path = colmap_dir / "database.db"
    sparse_root = colmap_dir / "sparse"
    dense_dir = colmap_dir / "dense"
    sparse_root.mkdir(parents=True, exist_ok=True)

    cam_params_file = None
    if camera_params:
        cam_params_file = write_colmap_camera_params(work_dir, camera_params)

    # 1) Feature extraction
    fe_cmd = [
        "colmap", "feature_extractor",
        "--database_path", str(db_path),
        "--image_path", str(images_dir),
        "--ImageReader.camera_model", camera_model,
        "--SiftExtraction.use_gpu", "1" if use_gpu else "0",
        "--ImageReader.single_camera", "1" if single_camera else "0",
    ]
    if cam_params_file is not None:
        fe_cmd += ["--ImageReader.camera_params", cam_params_file.read_text().strip()]

    run(fe_cmd)

    # 2) Matching
    matcher_cmd = [
        "colmap", "exhaustive_matcher",
        "--database_path", str(db_path),
        "--SiftMatching.use_gpu", "1" if use_gpu else "0",
    ]
    run(matcher_cmd)

    # 3) Mapping
    mapper_cmd = [
        "colmap", "mapper",
        "--database_path", str(db_path),
        "--image_path", str(images_dir),
        "--output_path", str(sparse_root),
    ]
    run(mapper_cmd)

    # Prefer sparse_root/0; else first directory
    sparse_model_dir = sparse_root / "0"
    if not sparse_model_dir.exists():
        candidates = sorted([p for p in sparse_root.iterdir() if p.is_dir()])
        if not candidates:
            raise RuntimeError(
                "COLMAP mapper produced no model in {}. "
                "Try different fps, better frames, or change camera_model.".format(sparse_root)
            )
        sparse_model_dir = candidates[0]
        print("[WARN] sparse/0 not found. Using first model: {}".format(sparse_model_dir))

    # 4) Undistort images (creates dense/images + dense/sparse)
    if dense_dir.exists():
        shutil.rmtree(str(dense_dir))

    undist_cmd = [
        "colmap", "image_undistorter",
        "--image_path", str(images_dir),
        "--input_path", str(sparse_model_dir),
        "--output_path", str(dense_dir),
        "--output_type", "COLMAP",
    ]
    run(undist_cmd)

    return sparse_model_dir, dense_dir


def make_gs_dataset(out_dir: Path, dense_dir: Path, sparse_model_dir: Path) -> Path:
    gs_dir = out_dir / "gs_dataset"

    # gs_dataset 초기화
    if gs_dir.exists():
        shutil.rmtree(str(gs_dir))
    gs_dir.mkdir(parents=True, exist_ok=True)

    dense_images = dense_dir / "images"
    dense_sparse = dense_dir / "sparse"

    images_dst = gs_dir / "images"
    sparse_dst = gs_dir / "sparse" / "0"   # GS가 요구하는 구조

    # 목적지 폴더가 이미 있으면 제거 (copytree는 dst 존재하면 실패)
    if images_dst.exists():
        shutil.rmtree(str(images_dst))
    if sparse_dst.parent.exists():
        shutil.rmtree(str(sparse_dst.parent))

    # 1) images 복사
    if not dense_images.exists():
        raise RuntimeError("Expected undistorted images at {} but not found.".format(dense_images))
    shutil.copytree(str(dense_images), str(images_dst))

    # 2) sparse 복사 → sparse/0
    sparse_dst.parent.mkdir(parents=True, exist_ok=True)  # 부모(sparse)만 생성
    if dense_sparse.exists():
        if (dense_sparse / "0").exists():
            shutil.copytree(str(dense_sparse / "0"), str(sparse_dst))
        else:
            shutil.copytree(str(dense_sparse), str(sparse_dst))
    else:
        shutil.copytree(str(sparse_model_dir), str(sparse_dst))

    print("[INFO] Gaussian Splatting dataset created at: {}".format(gs_dir))
    return gs_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=str, required=True, help="Input video path")
    ap.add_argument("--out", type=str, required=True, help="Output root directory")
    ap.add_argument("--fps", type=float, default=2.0, help="Frame extraction FPS (start with 1~2)")
    ap.add_argument("--max_frames", type=int, default=0, help="Limit number of extracted frames (0 = no limit)")
    ap.add_argument(
        "--camera_model",
        type=str,
        default="SIMPLE_RADIAL",
        help="COLMAP camera model: SIMPLE_RADIAL / PINHOLE / OPENCV / ...",
    )
    ap.add_argument(
        "--camera_params",
        type=str,
        default="",
        help="Optional forced intrinsics string, e.g. 'fx,fy,cx,cy,k1,k2,p1,p2' depending on model.",
    )
    ap.add_argument("--single_camera", action="store_true", help="Assume single camera intrinsics for all frames")
    ap.add_argument("--no_gpu", action="store_true", help="Disable COLMAP GPU usage (SIFT)")
    args = ap.parse_args()

    video = Path(args.video).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    frames_dir = out_dir / "frames"
    extract_frames_ffmpeg(video, frames_dir, fps=args.fps, max_frames=args.max_frames)

    sparse_model_dir, dense_dir = colmap_sfm(
        images_dir=frames_dir,
        work_dir=out_dir,
        camera_model=args.camera_model,
        use_gpu=(not args.no_gpu),
        single_camera=args.single_camera,
        camera_params=(args.camera_params.strip() if args.camera_params else None),
    )

    gs_dir = make_gs_dataset(out_dir, dense_dir, sparse_model_dir)

    print("\n✅ DONE")
    print("GS dataset folder: {}".format(gs_dir))
    print("\nNext (inside gaussian-splatting repo):")
    print("  python train.py -s {} -m {}".format(gs_dir, out_dir / "model"))


if __name__ == "__main__":
    main()
