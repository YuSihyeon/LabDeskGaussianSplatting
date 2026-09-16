# 데이터 보존 및 복원 안내

이 저장소는 연구실 자리 3D Gaussian Splatting의 설명, 선택 근거, 재실행 코드와 공개 검토를 거친 결과를 보관한다. **원본 전체 데이터와 실행 환경은 별도의 비공개 ResearchCollection에 보존한다. GitHub clone만으로 전체 실험을 복원할 수 없다.**

2026-09-16 이 문서 작성 시 전체 로컬 복사/WSL export/환경 snapshot 및 해시 검증이 진행 중이다. USB·외장 저장장치 사본 검증과 초기화 후 복원 실행은 완료되지 않았다. 이 문서는 데이터 위치와 복원 절차를 설명하며 완전한 백업 완료를 주장하지 않는다. 최종 상태는 로컬 collection의 검증 보고서와 각 copy manifest를 확인해야 한다.

## 보존 구조

아래 경로는 비공개 `ResearchCollection/`을 기준으로 한다. `originals/<id>`는 `01-LabDeskGaussianSplatting/originals/<id>`의 줄임말이다. 공개 저장소에는 이 폴더가 포함되지 않는다. Linux의 `~/`는 가져온 배포판의 기존 연구 사용자 홈을 뜻한다.

| 자료 | 비공개 보존 위치 | 역할 |
|---|---|---|
| 연구실 자리 프레임·COLMAP·기존 모델 | `originals/desktop_gs_root/mydesk/` | `frames`, `colmap/database.db`, `gs_dataset/images`, `gs_dataset/sparse/0`, `model` |
| 실제 자리 촬영 원본 `mydesk.mp4` | `_shared/wsl/Ubuntu-22.04.tar.zst` 내부 `~/gaussian-splatting/source_video/mydesk.mp4` | 13,178,554바이트 원본 입력 영상 |
| Graphdeco 전체 소스·다른 데이터 snapshot | 같은 WSL archive 내부 `~/gaussian-splatting/` | `datasets/mydesk`, `outputs/mydesk`, 사용자 변환 스크립트, submodules, SIBR 소스 |
| Windows SIBR 실행 번들 | `originals/sibr_viewers/` | EXE/DLL/셰이더, `run_mydesk.bat`, `output/mydesk`, `output/duck` |
| Unity VR 구현 | `originals/unity_vr/` | 루트 `package/`, `VR-URP/Assets`, `Packages`, `ProjectSettings`, `.git` |
| Unity 추가 작업 | `originals/unity_gs0224/`, `originals/unity_sound/`, `originals/unity_project1229/` | 시작 프로젝트·렌더러 1.1.1 포함 프로젝트·Meta XR 시제품. 모두 자리 복원 성공으로 간주하지 않는다. |
| Unity 배포 소스와 ZIP | `originals/unity_package111/`, `originals/unity_source_zip/` | Gaussian renderer 1.1.1 예제/소스와 원본 배포 ZIP |
| Bag·Lab 관련 원본 | `originals/desktop_gs_root/gaussian splatting_bag/`, `gaussian splatting_lab/` | 촬영/시연 영상, `untitled.psht`, Lab GLB |
| Synthetic/LLFF 데이터·원본 배포 ZIP | `originals/download_nerf_synthetic/`, `originals/download-originals/` | 별도 benchmark 데이터. 원본 출처/라이선스 범위 유지 |
| 이번 재실행의 전체 결과 | `originals/gs_private_archive/evidence/outputs/20260916/` | 전체 프레임·영상·수치·refined PLY·optimizer state |
| Windows 실행 환경 snapshot | `_shared/environments/snapshots/miniconda3-full.tar.zst` | gs_graphdeco를 포함한 전체 miniconda private snapshot |
| 환경 정의/패키지 목록 | `_shared/environments/conda/gs_graphdeco-*` | environment.yml, explicit spec, pip freeze/list |
| Windows CUDA extension 빌드 소스 | `05-GSPhysicalInference/originals/graphdeco_build_mirror/` | 로컬 컴파일 rasterizer·simple_knn·fused_ssim의 소스/빌드 상태 |

`originals/desktop_gs_root/2026_01_08/my desk.mp4`는 화면을 촬영한 시연 기록이다. 원본 재구성 입력 영상 `source_video/mydesk.mp4`와 구분한다. 보존 경로는 copy 작업 매핑이며 존재/전송 성공/복원 가능성은 별도로 검증해야 한다.

## 핵심 입력과 모델

확인한 Desktop snapshot은 입력 프레임 66개, 등록·왜곡 보정 이미지 59개를 포함한다. COLMAP DB와 sparse 모델은 카메라·특징·삼각측량 근거다. 원본 프레임을 다시 가공하지 않아도 보존된 등록 이미지/카메라로 재렌더링 경로를 구성할 수 있다.

기존 모델은 `model/point_cloud/iteration_7000/point_cloud.ply`의 Gaussian 720,554개와 `iteration_30000/point_cloud.ply`의 1,067,490개이다. 해당 PLY 크기는 각각 178,698,923바이트와 264,739,052바이트다. 역사적 학습의 원래 optimizer 체크포인트는 발견하지 못했다. PLY로 가중치를 다시 읽는 작업을 원래 학습 상태의 완전한 continuation으로 표현하지 않는다.

Desktop과 WSL `outputs/mydesk/model`은 일부 카메라 메타데이터·input PLY가 다르다. 보존된 30k PLY가 과거 비교에서 동일했어도 두 전체 snapshot이 같다는 뜻은 아니다. 이름을 기준으로 병합하거나 하나를 지우지 않는다. 자세한 근거는 [메타데이터 비교](evidence/metadata-consistency.json)와 [연구 기록](README.md)에 있다.

이번 200-step 결과는 기존 PLY에서 새로운 Adam optimizer로 시작한 짧은 후속 최적화다. `refined_200/optimizer-state.pt`는 이번 실행의 상태이며 원래 30k 학습 상태가 아니다. 수치는 같은 학습 시점 카메라에서 계산했고 held-out test 결과가 아니다. [실행 기록](evidence/run-record.json)과 [재실행 코드](evidence/rerun_mydesk.py)를 함께 확인한다.

## 복원할 때 확인할 점

1. collection의 원본 사본·WSL tar·miniconda snapshot을 다른 물리 저장장치에서도 검증하고, 새 작업 디렉토리에 복원한다. 보존본을 직접 학습 출력 경로로 사용하지 않는다.
2. WSL은 기존 배포판을 덮어쓰지 않는 **새 이름**으로 가져온다. 로컬 `RESTORE.md`에 import 명령과 원래 Linux 경로가 있다. 이 작업만으로 Windows CUDA 환경이 복원되는 것은 아니다.
3. 성공했던 Windows 환경은 Python3.11.16, torch2.7.0+cu128, torchvision0.22.0+cu128, RTX5060Ti16GB였다. 로컬 컴파일 `diff_gaussian_rasterization`과 `simple_knn` 바이너리를 보존해야 한다. 환경 snapshot의 경로 재배치와 GPU 호환성을 다시 검사한다. pip freeze의 옛 `file:` 경로는 새 PC에서 그대로 설치 가능한 주소가 아니다.
4. Unity2022.3.62f3에서 `originals/unity_vr/VR-URP`의 **작업 복사본**을 연다. 루트 `package`를 함께 유지해 `file:../../package`를 해결하고, `Packages/MixedReality/*.tgz`, `.meta`, `Assets/GaussianAssets`의 `.bytes`와 `.asset`을 모두 유지한다. 저장된 장면에 Splat renderer 참조가 있었는지 직접 확인해야 한다.
5. SIBR은 `sibr_viewers` 전체 작업 복사본에서 실행한다. `run_mydesk.bat`가 참조하는 `bin`과 `output/mydesk/model`을 분리하지 않는다.

같은 WSL archive에는 별도 Duck·4DGS·RoDyGS 작업도 있다. `~/duck/input.mp4`, `~/4dgs_from_youtube/{input.mp4,clip.mp4}`, 관련 코드·COLMAP 자료를 보존했는지 확인한다. 이들은 자리 복원의 성과와 구분한다.

전체 원본/렌더 영상에는 공개 검토 대상이 아닌 배경 인물·화면이 포함될 수 있다. 전체 보존본과 공개용 선택 영상은 목적이 다르다. 공개 저장소의 [영상 목록](evidence/publication-manifest.json)은 전체 데이터의 대체물이 아니다.
