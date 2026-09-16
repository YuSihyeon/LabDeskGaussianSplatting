# 연구실 자리 3D Gaussian Splatting

**직접 촬영한 연구실 책상 공간을 Gaussian으로 복원하고, 학습 결과를 검토하여 Unity에 연결한 공간 시각화 프로젝트.**

[결과 영상](#결과-미리보기) · [연구 목표](#연구-질문과-목표) · [구현 과정](#구현-과정) · [정량 결과](#결과와-분석) · [재현 안내](#재현과-자료-안내)

[독립 GitHub 저장소](https://github.com/YuSihyeon/LabDeskGaussianSplatting) · [상세 연구 기록 원문](RESEARCH_REPORT.md) · [전체 데이터와 복원 범위](DATA_AND_RESTORE.md)

## 프로젝트 개요

영상에서 얻은 **66개 프레임 → COLMAP 등록 59개 시점 → 희소 구조 → 7k/30k Gaussian 모델 → Unity 자산**으로 이어지는 작업이다.
책상·모니터·키보드·의자·파티션을 포함한 실제 장면을 대상으로, 촬영 기반 표현이 엔진 시각화까지 연결되는지 확인했다.

| 항목 | 프로젝트에서 확인한 내용 |
|---|---|
| 연구 대상 | 휴대형 카메라로 촬영한 연구실 개인 자리와 주변 공간 |
| 주요 흐름 | FFmpeg → COLMAP → Graphdeco 3DGS → CloudCompare 점검 → Unity |
| 보존된 기존 모델 | 7k: 720,554 Gaussian / 30k: 1,067,490 Gaussian |
| 엔진 표시 | Unity 2022.3.62f3 · DX12 · URP 14.0.12 · Unity VR Gaussian Splatting |
| 추가 검증 | 2026-09-16 CUDA 재렌더 및 새 optimizer를 사용한 200회 추가 최적화 |
| 현재 도달 범위 | 공간 외관 복원·엔진 표시·학습 시점 재평가; 최종 Unity 장면 저장은 보완 필요 |

> **수치를 읽는 기준:** 아래 PSNR·SSIM은 기존 학습 시점 59개에서 새로 계산했다. 독립 시험 영상의 성능, 실측 형상 정확도, 헤드셋 FPS를 뜻하지 않는다.

## 결과 미리보기

### 영상과 설명

두 영상은 보존된 Gaussian PLY를 실제 CUDA rasterizer로 렌더링한 결과다. 제목이나 미리보기를 누르면 MP4를 열 수 있다.

| 영상 | 볼 수 있는 내용 | 공개 범위 |
|---|---|---|
| [**연구실 자리 · 카메라 이동 렌더**](evidence/public/mydesk-camera-path.mp4) | 기존 30k 모델의 책상·의자·파티션을 보간 카메라 경로에서 확인 | 200프레임 · 24 fps · 8.33초 |
| [**7k · 30k · 추가 200회 최적화 비교**](evidence/public/mydesk-comparison.mp4) | 같은 입력 시점에서 세 모델의 외관 차이를 비교 | 26개 시점 · 13초 |

<a href="evidence/public/mydesk-camera-path.mp4"><img src="evidence/images/rerender-30000-view25.png" width="360" alt="기존 30k Gaussian 모델의 CUDA 재렌더, 클릭하면 카메라 이동 영상"></a>

*2026-09-16 재렌더의 한 시점. 영상은 기존 촬영 경로 주변을 보간한 것이며, 완전히 새로운 관측에서의 정확도 검증은 아니다.*

<img src="evidence/images/unity-20260108.png" width="860" alt="당시 Unity 2022.3.62f3에서 연구실 자리 Gaussian 자산을 표시한 화면">

*당시 Unity 표시 화면. 화면의 Gaussian 1,067,490개는 30k PLY 및 변환 자산과 일치한다. 저장된 장면에는 renderer 연결이 남지 않아 복구 작업이 필요하다.*

전체 렌더에는 배경 사람이 포함된 구간이 있어 공개 영상은 사람이 없는 구간만 선별했다.
공개 비교 영상의 26개 시점과 정량 평가의 전체 59개 시점은 서로 다른 범위다.
선별 근거는 [공개 미디어 목록](evidence/publication-manifest.json), 전체 영상 점검은 [decode 검증 기록](evidence/outputs/20260916/video-verification.json)에 남겼다.

## 연구 질문과 목표

### 촬영한 공간을 어떤 표현으로 엔진에 가져올 수 있는가

직접 확인되는 목표는 촬영 영상, `mydesk` 데이터셋, 학습 PLY, 점군 점검 화면, Unity 자산을 하나의 공간 복원 흐름으로 연결하는 것이다.
수작업 메시 모델링 부담을 줄이면서 실제 책상의 외관을 보존하고 VR 표현을 탐색하려는 동기는 자료로부터 추론할 수 있다.
다만 이를 명시한 당시 연구계획서나 도구 선정 비교표는 발견되지 않았다.

| 질문 | 이번 자료로 답할 수 있는 부분 | 추가 검증이 필요한 부분 |
|---|---|---|
| 영상으로 자리의 외관을 복원할 수 있는가 | 등록 카메라·희소점·학습 PLY·새 렌더를 확인 | 촬영 범위 밖과 가려진 영역의 정확도 |
| 7k와 30k 결과는 어떻게 다른가 | 동일한 59개 시점에서 재렌더·수치 비교 | 동일 조건 전체 재학습과 독립 시점 성능 |
| 결과를 Unity에서 표시할 수 있는가 | 당시 표시 화면·변환 자산·패키지 연결 확인 | 저장 후 재열기 및 별도 기기에서 복구 |
| 실제 VR 콘텐츠로 사용할 수 있는가 | VR 지원 renderer를 연결한 흔적 | 헤드셋·양안 렌더링·추적·기기별 성능 |

정밀 측량, 충돌 메시 생성, 로봇 물리 연동, 재조명, 헤드셋 실험의 완료를 이 프로젝트의 성과로 합산하지 않는다.

## 수행 내용과 기여 범위

### 프로젝트에서 수행한 연결과 검증

- 연구실 자리 촬영을 이미지 입력으로 구성하고 COLMAP 등록·왜곡 보정을 거쳐 학습 자료로 연결했다.
- 기존 3DGS 구현을 사용한 학습 모델을 보존하고, CloudCompare에서 점 분포와 이상점을 시각적으로 점검했다.
- 30k PLY를 Unity용 자산으로 변환하여 엔진 안에서 실제 공간 외관을 표시했다.
- 2026-09-16에는 파일·해시·카메라 메타데이터를 감사하고, 실제 GPU 재렌더와 조건을 고정한 짧은 후속 최적화를 수행했다.
- 원래 기록과 새 실행 결과를 분리하고, 공개 영상·평가 CSV·재실행 스크립트로 검토 경로를 남겼다.

### 외부 구현과 도구의 역할

| 도구 | 사용 역할 | 기여를 해석하는 경계 |
|---|---|---|
| FFmpeg | 영상에서 PNG 프레임 추출 | 로컬 전처리 스크립트가 호출하는 외부 도구 |
| COLMAP | 특징 추출·매칭·카메라 등록·희소 구조·왜곡 보정 | SfM 알고리즘 자체의 독자 개발을 의미하지 않음 |
| Graphdeco 3DGS | Gaussian 최적화, PLY 로드, CUDA 렌더 | upstream 학습·렌더러를 사용한 장면 적용 |
| CloudCompare | 7k/30k PLY 및 점 위치 분포 확인 | 정량 C2C/C2M 측정 완료 기록은 없음 |
| Unity VR Gaussian Splatting | PLY 변환·정렬·엔진 표시 | package의 C#/shader 전체를 개인 구현으로 분류하지 않음 |
| Postshot / Polycam | 가방·공간의 초기 별도 복원 시도 | 현재 `mydesk` 수치와 동일 실험으로 합치지 않음 |

자세한 작업 흔적은 [관찰 기록](evidence/observations.md), 실행에 사용한 소스 commit과 모듈 해시는 [실행 기록](evidence/run-record.json)에 있다.

### 자료로 확인되는 진행 순서

| 시점 | 남아 있는 근거 | 확인되는 작업 |
|---|---|---|
| 2025-12-27 이름의 자료 | 가방 촬영·Postshot 프로젝트, Polycam 영상·GLB | 작은 물체 및 공간 복원의 초기 탐색 |
| 화면 날짜 2026-01-05 / 폴더 `2026_01_08` | 점군 사진·뷰어 시연·Unity 화면 | 자리 결과 점검과 엔진 표시; 날짜 종류는 구분 |
| 2026-05-28 | CloudCompare 스크린샷 | 7k/30k 모델 로드와 시각적 비교 |
| 2026-09-16 | 감사 JSON·CUDA 로그·평가 CSV·영상 | 기존 결과의 재실행과 별도 200-step 실험 |

## 데이터와 선정 과정

### 원영상에서 최종 학습 이미지까지

| 단계 | 수량·크기 | 선정 및 확인 방법 |
|---|---|---|
| 자리 촬영 원영상 | 약 32.895초 · 1080×1920 | 복원 입력 `mydesk.mp4`; 화면을 촬영한 시연 영상과 구별 |
| 원프레임 | 66개 · 각 1080×1920 | 원프레임 폴더 및 COLMAP DB에 모두 존재 |
| 등록·왜곡 보정 이미지 | 59개 · 각 1062×1888 | 최종 학습 이미지 이름과 sparse 등록 이미지 이름이 일치 |
| 등록되지 않은 이미지 | 7개 | `000044.png`~`000049.png`, `000061.png` |
| 이번 평가 입력 | 기존 59개 카메라·480×854 | desktop 모델의 `cameras.json`을 파일명 순서로 사용 |

[당시 전처리 코드](evidence/historical/video_to_gs_dataset.py)의 기본 추출률은 2 fps이며 영상 길이와 프레임 수가 이에 부합한다.
당시 명령이 남아 있지 않아 실제로 기본값을 사용했는지는 확정하지 않는다.
등록률은 **59/66 = 89.39%**다. 제외된 프레임도 DB에 118~1,210개의 특징점이 남아 있으므로 파일 누락이나 특징 추출 자체의 실패로 단정할 수 없다.

제외는 등록·왜곡 보정 과정에서 발생한 것으로 해석한다. 수동 삭제를 입증하는 기록은 없다.
블러·낮은 겹침·저텍스처는 가능한 원인이지만 프레임별 실패 로그가 없어 확정하지 않았다.
가방 영상, Polycam GLB 및 별도 benchmark 자료는 이번 렌더·최적화 입력에 섞지 않았다. 근거는 [프레임·DB 감사](evidence/historical-statistics.json)에서 확인할 수 있다.

### 재현 전에 해결해야 할 입력 불일치

| 항목 | desktop 모델 snapshot | 현재 데이터셋 또는 WSL snapshot |
|---|---|---|
| 초기점 | `model/input.ply` 8,326점 | 현재 sparse PLY 8,322점 |
| 영상 크기 | `cameras.json` 1062×1889 | 현재 보정 이미지·sparse 1062×1888 |
| focal | 모델 약 1666.3786 px | 현재 sparse 약 1668.9216 px |
| 동일 30k PLY의 WSL 사본 | PLY SHA-256 동일 | pose·input PLY가 다르고 카메라 크기는 1061×1888 |

이름이 같은 폴더라도 하나의 실행에서 나온 완전한 묶음이라고 가정할 수 없다.
이번 재실행은 당시 Unity 자산의 카메라 위치와도 부합하는 desktop 모델 카메라를 기준으로 삼았다.
현재 보정 이미지와의 작은 차이가 남으므로 아래 수치는 명시한 입력 조합의 결과다. [메타데이터·해시 비교](evidence/metadata-consistency.json).

## 구현 과정

### 1. 영상 전처리와 COLMAP 희소 구조

[전처리 스크립트](evidence/historical/video_to_gs_dataset.py)는 다음 순서로 입력을 만든다.

1. FFmpeg `fps` 필터로 PNG를 추출한다.
2. `feature_extractor`에 카메라 모델과 single-camera 설정을 전달한다.
3. `exhaustive_matcher`로 이미지 쌍을 매칭한다.
4. `mapper`로 희소 모델을 생성하고 기본적으로 `sparse/0`을 선택한다.
5. `image_undistorter`로 보정 영상을 만든다.
6. 이미지와 sparse 모델을 `gs_dataset/images`, `gs_dataset/sparse/0`에 배치한다.

DB에는 66개 이미지·1개 카메라·254,155개 특징점·2,145개 영상 쌍이 있다. 2,145는 66개 이미지의 전체 쌍 수다.
이 중 683개 쌍에 검증된 inlier가 있고, 현재 희소 모델은 8,322점이다.
원영상 카메라는 SIMPLE_RADIAL, 보정 후 카메라는 PINHOLE이다. `dense` 폴더에는 depth/normal/consistency 출력이나 `fused.ply`가 없어 dense MVS 완료 근거로 사용하지 않는다.

### 2. Gaussian 학습 산출물 확인

| 보존 산출물 | Gaussian 또는 점 수 | 파일 크기 |
|---|---:|---:|
| 현재 `gs_dataset/sparse/0/points3D.ply` | 8,322 | 희소 구조 |
| 모델의 `input.ply` | 8,326 | 학습 입력 snapshot |
| `iteration_7000/point_cloud.ply` | 720,554 | 178,698,923 bytes |
| `iteration_30000/point_cloud.ply` | 1,067,490 | 264,739,052 bytes |

학습 PLY의 62개 float 속성은 위치·법선 필드·SH 색 계수·opacity·scale·rotation을 담는다.
[보존 설정](evidence/historical/training-config.json)은 SH degree 3, black background, CUDA, `eval=False`, depth 입력 없음, `train_test_exp=False`를 보여 준다.
당시 전체 학습 명령·loss 로그·optimizer checkpoint·원래 학습 시간은 확인하지 못했다.

### 3. 점군 점검과 Unity 표시

CloudCompare 사진은 모델을 로드하고 회전시켜 구조·이상점을 확인한 근거다.
화면별 시점·줌과 색상 범례가 달라 시각적 차이를 수치 정확도로 읽지 않았다. [CloudCompare 관찰](evidence/observations.md#cloudcompare).

Unity에서는 SH Order 3, Device Radix Sort와 1,067,490 splat을 확인했다.
변환 데이터 5개는 총 64,318,080 bytes, 약 61.34 MiB다. 저장 크기이며 런타임 GPU 메모리 측정값은 아니다.
[Unity 버전](evidence/historical/unity-version.txt), [package manifest](evidence/historical/unity-vr-manifest.json), [자산 정의](evidence/historical/unity-mydesk.asset)를 함께 보존했다.

당시 화면에는 미저장 표시 `*`가 있고, [저장된 GaussianTestScene](evidence/historical/GaussianTestScene.unity)에는 Main Camera와 Directional Light만 남아 있다.
변환 자산은 존재하지만 renderer를 다시 연결하고 저장해야 당시 화면을 복원할 수 있다.

### 4. 2026-09-16 GPU 재렌더와 후속 최적화

실행 환경은 RTX 5060 Ti 16 GB, Windows CUDA, Torch 2.7.0+cu128 및 `diff_gaussian_rasterization`이다.
기존 WSL 환경의 Torch 1.12.1은 sm_120 미지원 경고와 rasterizer 부재가 있어 사용하지 않았다. [환경 버전](evidence/outputs/20260916/environment-versions.json).

1. 기존 7k·30k PLY를 59개 카메라에서 각각 480×854로 렌더링한다.
2. 각 시점의 PSNR·SSIM·L1을 계산하고 CSV를 보존한다.
3. 회전 SLERP와 위치 선형 보간으로 30k 카메라 경로를 만든다.
4. 30k PLY에서 fresh Adam, seed 0으로 200회 최적화한다.
5. Gaussian 수를 고정하고 densification·pruning·exposure 최적화 없이 위치·색·opacity·scale·rotation을 갱신한다.
6. 같은 59개 시점으로 재평가하고 비교 영상을 만든다.

손실은 `0.8 × L1 + 0.2 × (1 − SSIM)`이다. [실행 코드](evidence/rerun_mydesk.py), [학습률](evidence/outputs/20260916/refinement-learning-rates.json), [loss CSV](evidence/outputs/20260916/refined_200/training-loss.csv)를 연결했다.
원본 PLY·이미지·카메라는 읽기 전용 입력으로 사용했고 새 결과를 별도 폴더에 기록했다.

## 결과와 분석

### 학습 시점 재구성 품질

**공통 조건: 기존 학습 시점 59개, 480×854, 시점별 지표의 평균.** 추가 200회도 같은 영상들을 최적화에 사용했다.

| 모델·실험 | Gaussian 수 | PSNR ↑ | SSIM ↑ | L1 ↓ |
|---|---:|---:|---:|---:|
| 기존 7k 모델의 새 렌더 | 720,554 | 30.9276 dB | 0.93243 | 0.015924 |
| 기존 30k 모델의 새 렌더 | 1,067,490 | 34.0718 dB | 0.96184 | 0.010607 |
| 30k 초기화 + 새 200-step 실험 | 1,067,490 | 36.9819 dB | 0.97001 | 0.007641 |

근거: [집계 JSON](evidence/outputs/20260916/metrics-summary.json), [7k 시점별 CSV](evidence/outputs/20260916/iteration_7000/per-view-metrics.csv), [30k 시점별 CSV](evidence/outputs/20260916/iteration_30000/per-view-metrics.csv), [추가 최적화 CSV](evidence/outputs/20260916/refined_200/per-view-metrics.csv).

30k 모델은 이번 조건에서 7k보다 입력 영상에 더 잘 맞고, 추가 최적화는 30k 대비 PSNR을 약 2.91 dB 높였다.
이는 해당 입력 조합과 해상도에서 적합도가 향상된 결과다. 카메라 불일치와 독립 평가 부재 때문에 새 시점 일반화나 연구 방법 자체의 개선으로 확장할 수 없다.
과거 optimizer 상태를 읽지 않았으므로 200-step을 원래 학습의 정확한 resume로 표현하지 않는다.

### 구조 및 실행 비용의 해석

| 항목 | 확인한 값 | 측정의 의미 |
|---|---:|---|
| COLMAP 평균 track 길이 | 4.582 | 희소점 하나를 지지하는 등록 관측의 평균 |
| 재투영 오차 평균 / 중앙값 / 95백분위 | 0.7268 / 0.5915 / 1.7455 px | 영상 평면 특징점 오차; mm/cm 단위 형상 정확도 아님 |
| 새 실행 전체 wall time | 44.83초 | 이번 저해상도 렌더·최적화 작업의 기록 |
| 추가 최적화·PLY 저장 구간 | 14.19초 | 원래 30k 학습 시간과 구분 |
| Torch 최대 allocated GPU memory | 1,736,743,936 bytes | 이번 실행에서 측정한 할당량; Unity/VR 사용량 아님 |

근거는 [역사 자료 통계](evidence/historical-statistics.json), [실행 로그](evidence/outputs/20260916/run.log), [최적화 시간](evidence/outputs/20260916/refined_200/refinement-timing.json)이다.
영상에서 주변부 번짐과 가려진 영역의 불완전성을 함께 볼 수 있다. 중심 책상의 외관이 보이는 것과 공간 전체의 정밀 형상이 확보된 것은 구별해야 한다.

## 한계와 다음 단계

| 우선순위 | 현재 제약 | 다음 작업 | 완료 판단 기준 |
|---|---|---|---|
| 1 | 카메라·초기점 snapshot 불일치 | 영상·보정·카메라·점·config·PLY를 실행 ID로 묶기 | 입력 해시와 이미지 크기·pose 일치 검사 통과 |
| 2 | 학습 시점으로만 평가 | 촬영 구간 단위로 holdout을 미리 고정 | 학습/시험 목록 공개, 별도 시점별·평균 지표 |
| 3 | 동적 배경과 제한된 겹침 | 무인 상태·노출/초점 고정, 책상 아래·옆면 추가 촬영 | 등록률·가려진 영역·동적 잔상 비교 |
| 4 | 실측 형상 기준 부재 | 기준 스캔·실측점 확보 후 스케일·정합 고정 | C2C/C2M 등 목적에 맞는 오차와 정합 조건 |
| 5 | Unity 최종 장면 연결 누락 | renderer·GUID·API·pose를 저장 | 재열기 및 별도 작업 복사본에서 표시 성공 |
| 6 | VR 및 일반화 미검증 | 기기별 양안 렌더·성능, 동일 보정 조건 추가 실험 | 기기·해상도·splat 수별 FPS/메모리와 holdout 결과 |

## 재현과 자료 안내

### 기존 PLY에서 재렌더하기

[전체 데이터 안내](DATA_AND_RESTORE.md)에서 비공개 보존 입력과 환경을 복구하고, `GRAPHDECO_ROOT`, `MYDESK`, 비어 있는 `NEW_OUTPUT`을 지정한다.

```text
python -B -X utf8 -u evidence/rerun_mydesk.py --repo GRAPHDECO_ROOT --dataset MYDESK/gs_dataset --model MYDESK/model --out NEW_OUTPUT --width 480 --steps 200 --interpolation 8
```

Graphdeco 기준 commit은 `54c035f7834b564019656c3e3fcc3646292f727d`다.
[입력 provenance](evidence/outputs/20260916/input-provenance.json)와 [실행 기록](evidence/run-record.json)을 대조한다. CUDA 확장의 버전 문자열 `0.0.0`만으로 동일 빌드를 보장할 수 없어 빌드 소스·환경도 필요하다.
파일 감사만 수행할 때는 [inspect_historical.py](evidence/inspect_historical.py)를 사용한다. 이 스크립트는 COLMAP DB를 read-only로 연다.

### Unity와 전체 원본 복구

- 기존 VR-URP의 작업 사본을 Unity 2022.3.62f3·DX12로 열고 루트 `package` 참조를 유지한다.
- `GaussianAssets`의 `.asset`, `.bytes` 5개 및 `.meta`를 함께 복구하고 `GaussianSplatRenderer`에 다시 연결한다.
- 재변환할 때는 `Tools → Gaussian Splats → Create GaussianSplatAsset`에서 기존 30k PLY를 지정한다.
- 카메라 방향을 확인한 후 저장·재열기를 검증한다. 이번 정리에서는 새 Unity 장면이나 헤드셋 빌드를 실행하지 않았다.
- 촬영부터 재처리하려면 전처리 코드의 폴더 초기화 동작을 확인하고 반드시 새 작업 경로를 사용한다.

| 자료 | 읽을 문서·근거 | 포함 범위 |
|---|---|---|
| 포트폴리오 | 이 README | 핵심 질문·미디어·실험·결과·다음 검증 |
| 기존 상세 기록 | [RESEARCH_REPORT.md](RESEARCH_REPORT.md) | 재구성 전 README의 바이트 보존본 |
| 공개 검토 자료 | [근거 manifest](evidence/copied-evidence-manifest.json) | 코드·설정·CSV/JSON·대표 화면·공개 발췌 영상 |
| 전체 원본·환경 | [DATA_AND_RESTORE.md](DATA_AND_RESTORE.md) | 원영상·프레임·COLMAP·대형 PLY·Unity·WSL·conda 위치 |

대형 모델, optimizer 상태, 전체 영상, 배경 인물이 포함된 결과 및 upstream 전체 소스는 비공개 보존 묶음에 있다.
GitHub clone은 설명과 공개 근거를 제공하며 전체 실험 입력을 모두 포함하지 않는다.
로컬 보존 자료의 내용·해시 검증과 외부 USB 전송, 초기화 후 실행 성공은 별도 상태다. 최종 범위는 [복원 안내](DATA_AND_RESTORE.md)를 기준으로 확인한다.
