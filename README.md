# 연구실 자리 3D Gaussian Splatting 복원과 Unity 시각화


**독립 연구 저장소:** [GitHub](https://github.com/YuSihyeon/LabDeskGaussianSplatting) · [전체 데이터와 복원 범위](DATA_AND_RESTORE.md) · [영상 갤러리](https://yusihyeon.github.io/LabDeskGaussianSplatting/gallery.html)

휴대형 카메라 영상으로 연구실 책상·의자·파티션을 복원하고, 점군을 확인한 뒤 Unity에서 표시한 작업을 정리한 기록이다. 남아 있는 파일로 **66개 프레임 → 59개 등록 시점 → COLMAP 희소점 → 7k/30k Gaussian 모델 → Unity 자산**의 흐름을 확인했다. 2026-09-16에는 기존 모델을 실제 CUDA 렌더러로 다시 실행하고, 별도의 200회 추가 최적화 실험과 영상을 만들었다.

이 문서는 당시 결과, 이번에 계산한 통계, 당시 의도에 대한 추론을 구분한다. 원본 학습 로그·정량 CloudCompare 분석·최종 Unity 장면 저장에는 공백이 있고, 일부 카메라 메타데이터는 서로 일치하지 않는다.

- [기존 30k 모델의 새 카메라 경로 영상 — 공개 구간 8.33초](evidence/public/mydesk-camera-path.mp4)
- [7k / 30k / 200회 추가 최적화 비교 영상 — 공개 구간 13초](evidence/public/mydesk-comparison.mp4)
- [실제 실행 코드](evidence/rerun_mydesk.py), [명령·버전·실험 구분](evidence/run-record.json), [새 평가 수치](evidence/outputs/20260916/metrics-summary.json)

![당시 Unity에서 표시한 연구실 자리](evidence/images/unity-20260108.png)

## 목적과 작업의 범위

**직접 확인한 목적의 흔적**은 연구실 자리 촬영 영상, `mydesk` 데이터셋, 학습된 PLY, CloudCompare 화면, Unity에 연결된 자산이다. 따라서 실제 공간을 촬영 기반으로 복원하고 엔진에서 자유 시점으로 표시하는 실습·프로토타입이었다고 정리할 수 있다.

**추론되는 동기**는 직접 메시를 모델링하는 부담을 줄이면서 실제 책상의 외관을 보존하고, 이후 VR로 가져갈 수 있는 표현을 탐색하는 것이다. 이를 명시한 당시 연구계획서나 도구 비교표는 발견하지 못했다. 정밀 측량, 로봇 물리 충돌, relighting 또는 헤드셋 실험이 이 작업에서 완료되었다는 증거는 없다.

여기서 확인한 실질적인 기여는 촬영·전처리·기존 3DGS 학습 도구·Unity 렌더러를 연구실 장면에 연결하고 결과를 점검한 과정이다. upstream의 Gaussian 최적화 알고리즘이나 Unity C#/shader 전체를 독자 구현 성과로 분류하지 않는다.

## 남아 있는 진행 순서

| 시기·근거 | 확인한 작업 | 해석의 범위 |
|---|---|---|
| 2025-12-27 이름의 가방 자료 | Postshot 가방 복원 화면, 촬영 영상, `.psht` 프로젝트 | 작은 대상에 대한 초기 연습. 화면의 30 kSteps와 3,000 kSplats는 설정 상한이며 실제 완료 수치가 아님 |
| 2025-12-27 이름의 연구실 자료 | Polycam 표시 영상, GLB, 삼각면이 보이는 공간 복원 화면 | 연구실 공간 복원의 별도 초기 시도. 후속 3DGS 결과와 동일 실험으로 합치지 않음 |
| 2026-01-05가 보이는 화면 사진 / `2026_01_08` 폴더 | 점군 확인, 자리 뷰어를 촬영한 영상, Unity 표시 화면 | 폴더 날짜·화면 날짜를 분리함. Unity 화면은 성공적으로 표시된 상태를 입증 |
| 2026-05-28 스크린샷 | CloudCompare에서 7k와 30k PLY 로드 | 정량 거리 분석 완료까지는 입증되지 않음 |
| 2026-09-16, 이번 정리 | 파일 감사, GPU 재렌더, 200-step 추가 최적화, 공개 구간 영상 | 기존 30k 학습을 처음부터 다시 수행한 결과가 아님 |

원자료별 관찰 내용은 [관찰 기록](evidence/observations.md), 영상 길이·해시는 [영상 목록](evidence/video-inventory.json)에 있다.

## 사용 도구와 선택의 의미

| 도구 | 파일에서 확인한 역할 | 선택 이유에 대해 말할 수 있는 범위 |
|---|---|---|
| Postshot | 가방 촬영 영상으로 radiance field를 만든 GUI 작업 | 빠르게 물체 복원을 시험한 흔적으로 해석할 수 있으나 당시 선정 이유 문서는 없음 |
| Polycam | 초기 연구실 공간 모델·영상 출력 | 공간 복원 시도임은 확인. 정확한 촬영 모드·입력 수·설정은 확인되지 않음 |
| FFmpeg | 로컬 `video_to_gs_dataset.py`에서 영상 프레임 추출 | 정해진 fps로 반복 가능한 이미지 입력을 만들 수 있음 |
| COLMAP | 특징 추출, 전체 영상 쌍 매칭, 카메라 등록, 희소 구조 복원, 왜곡 보정 | 스크립트 호출 순서와 DB·바이너리 결과가 일치함 |
| Graphdeco 3DGS | SH3 Gaussian PLY 생성·렌더 | 기존 reference 구현을 사용한 정황과 산출물 확인. 당시 GPU·학습 시간·전체 학습 명령은 미확인 |
| CloudCompare | 학습 PLY의 로드·점 위치 분포 시각적 점검 | 색과 점 분포를 보았다는 근거는 있으나 실측 정확도 검증 기록은 없음 |
| Unity VR Gaussian Splatting | 학습 PLY를 압축 자산으로 변환하고 엔진에 표시 | 당시 화면·자산·package 연결로 확인. VR 지원 패키지를 선택한 것과 실제 헤드셋 검증은 구별 |

COLMAP의 바이너리는 카메라·등록 이미지·3D 점을 나누어 저장한다. 이 구조와 점의 재투영 오차 의미를 공식 설명에 맞춰 읽었다. [COLMAP 형식 문서](https://colmap.github.io/format.html). 3DGS와 Unity 통합의 일반적인 흐름은 각각 [Graphdeco 원본 구현](https://github.com/graphdeco-inria/gaussian-splatting), [사용한 Unity VR fork](https://github.com/ninjamode/Unity-VR-Gaussian-Splatting)에 근거한다. 외부 저장소의 벤치마크는 이 연구실 장면의 성능으로 사용하지 않았다.

## 데이터 구성과 선택·제외

직접 촬영 원영상은 약 32.895초, 1080×1920이다. 원프레임 66개도 모두 1080×1920이며, 왜곡 보정 후 학습 폴더에는 1062×1888 이미지 59개가 있다. 로컬 [전처리 스크립트](evidence/historical/video_to_gs_dataset.py)의 기본 추출률은 2 fps다. 원영상 길이와 66개 프레임은 이 값과 부합하지만, 당시 실행 명령을 찾지 못했으므로 실제 지정값이 2 fps였다고 확정하지 않는다.

현재 학습 폴더에 없는 프레임은 `000044.png`~`000049.png`, `000061.png`의 7개다. 모두 원프레임 폴더와 COLMAP DB에는 있고, 희소 모델의 등록 이미지와 최종 학습 이미지에는 없다. 최종 이미지 집합과 등록 시점의 이름은 정확히 일치한다. 따라서 전처리의 등록·왜곡 보정 과정에서 제외된 것으로 해석하는 것이 타당하며, 사용자가 수동으로 나쁜 이미지를 지웠다고 단정할 근거는 없다.

제외된 프레임에도 각각 118~1,210개의 특징점이 DB에 남아 있다. 단순히 파일이 없거나 특징 추출 자체가 안 된 상황은 아니다. 낮은 겹침·블러·저텍스처가 원인이었을 가능성은 있지만 프레임별 매칭 실패 로그가 없으므로 원인을 확정하지 않았다. 현재 등록률은 59/66, 약 **89.39%**다. [프레임·DB·희소점 감사 결과](evidence/historical-statistics.json).

가방 영상과 Polycam의 GLB는 다른 초기 시도이므로 이번 `mydesk` 렌더·최적화 입력에 섞지 않았다. 이번 재실행은 기존 30k 모델과 시각적으로 일치하는 desktop 측 `model/cameras.json`을 사용하고, 경로는 파일명 순서로 구성했다. 다른 보정 스냅샷으로 바꾸지 않은 이유는 아래 메타데이터 불일치 때문이다.

## 전처리와 학습 산출물

로컬 전처리 코드는 다음 순서다.

1. `ffmpeg`의 `fps` 필터로 PNG를 추출한다.
2. COLMAP `feature_extractor`에 카메라 모델과 single-camera 여부를 전달한다.
3. `exhaustive_matcher`로 이미지 쌍을 매칭한다.
4. `mapper`로 희소 모델을 만들고 기본적으로 `sparse/0`을 선택한다.
5. `image_undistorter`를 실행한다.
6. 보정된 영상과 sparse 모델을 `gs_dataset/images`, `gs_dataset/sparse/0`에 복사한다.

DB에는 66개 이미지, 1개 카메라, 총 254,155개 특징점이 있고 2,145개의 영상 쌍이 기록되어 있다. 이는 66개 이미지의 전체 조합 수와 같다. 683개 쌍에는 검증된 inlier가 있다. 현재 희소 모델은 **8,322점**, 평균 track 길이 **4.582**, 평균 재투영 오차 **0.7268 px**다. 중앙 재투영 오차는 0.5915 px, 95백분위는 1.7455 px다. 이 값은 COLMAP 특징점의 영상 평면 오차이며 실제 공간의 mm/cm 오차가 아니다.

원영상 카메라 모델은 SIMPLE_RADIAL, 1080×1920, 추정 focal 1668.9216 px, radial 항 0.0377827이다. 보정 후 카메라는 PINHOLE, 1062×1888, fx=fy=1668.9216 px로 저장되어 있다. `dense`라는 폴더가 있지만 depth/normal/consistency 출력은 비어 있고 `fused.ply`도 없다. 따라서 이 폴더명만으로 dense MVS·메시 복원까지 수행했다고 볼 수 없다.

| 산출물 | 확인한 수치 | 의미 |
|---|---:|---|
| 현재 `gs_dataset/sparse/0/points3D.ply` | 8,322점 | 현재 저장된 COLMAP 희소 구조 |
| `model/input.ply` | 8,326점 | 모델 폴더에 보존된 초기점 스냅샷. 현재 데이터셋과 4점 차이 |
| `iteration_7000/point_cloud.ply` | 720,554 Gaussian, 178,698,923 bytes | 7k라는 이름으로 저장된 학습 모델 |
| `iteration_30000/point_cloud.ply` | 1,067,490 Gaussian, 264,739,052 bytes | 30k라는 이름으로 저장된 학습 모델 |

학습 PLY는 각 Gaussian에 62개 float 속성을 보존한다. 위치·법선 필드, SH 색 계수, opacity, scale, rotation을 포함하므로 일반 RGB 점군과 같지 않다. [설정 요약](evidence/historical/training-config.json)은 SH degree 3, black background, CUDA data device, `eval=False`, depth 입력 없음, `train_test_exp=False`를 보여 준다. 실제 optimizer 상태를 담은 과거 checkpoint와 학습 loss 로그는 이 범위에서 확인하지 못했다.

## 메타데이터가 서로 다른 부분

이 부분은 재현성과 성능 해석에 직접 영향을 준다.

| 항목 | desktop 모델 폴더 | 현재 데이터셋 또는 다른 사본 |
|---|---|---|
| 초기점 수 | `input.ply` 8,326 | 현재 sparse PLY 8,322 |
| 카메라 영상 크기 | 모델 `cameras.json` 1062×1889 | 현재 보정 영상·sparse 카메라 1062×1888 |
| focal | 모델 `cameras.json` 약 1666.3786 | 현재 sparse 약 1668.9216 |
| WSL 모델 사본 | 30k PLY SHA-256이 동일 | WSL `cameras.json`은 다른 pose와 1061×1888 크기, input PLY도 다름 |

**동일한 30k PLY 옆의 보정 메타데이터가 사본마다 다르다.** 반복 전처리나 폴더 복사 과정에서 서로 다른 스냅샷이 섞였을 가능성이 있으나 원인을 확인할 변경 이력은 없다. 파일명만으로 한 실행의 완전한 데이터 묶음이라고 가정하면 안 된다. [해시와 첫 카메라 비교](evidence/metadata-consistency.json).

이번 재렌더에서는 당시 Unity 자산의 카메라 위치와도 부합하는 desktop 모델의 카메라 JSON을 기준으로 사용했다. 기준 영상은 현재 남은 보정 이미지이며 해상도·보정값의 작은 차이가 존재한다. 따라서 새 수치는 **이번에 명시한 입력 조합의 재실행 수치**다. 원래 학습 당시 점수나 완전히 동일한 전처리의 재현 점수로 소급하지 않는다.

## CloudCompare에서 확인한 것

초기 사진과 2026-05-28 화면으로 점군을 회전시켜 보고 7k/30k 파일을 로드한 사실을 확인했다. 구조 밖에 흩어진 점들과 방향에 따른 분포 차이를 관찰할 수 있다. 다만 스크린샷의 색 의미·scalar field·범례가 명확하지 않고 비교 화면의 시점과 줌도 다르다.

조사 범위에서 정합 행렬, 실측 기준점, ICP 잔차, cloud-to-cloud/cloud-to-mesh 오차, 정량 비교 CSV는 확인되지 않았다. 그러므로 당시 분석은 **시각적인 구조·이상점 점검** 수준으로 기록한다. 위 재투영 오차는 이번 COLMAP 파일 감사에서 계산한 값으로, 당시 CloudCompare 측정 결과가 아니다. [관찰 기록의 CloudCompare 항목](evidence/observations.md#cloudcompare).

## Unity 구현의 성과와 저장 공백

당시 화면에서는 책상·모니터·키보드·의자·파티션이 Unity 안에 렌더링된다. Unity 2022.3.62f3, DX12, URP 14.0.12와 `ninjamode/Unity-VR-Gaussian-Splatting` 패키지 연결을 확인했다. SH Order 3, Device Radix Sort이며 화면의 splat 수 1,067,490은 PLY와 자산 정의 양쪽 수치에 일치한다. [버전](evidence/historical/unity-version.txt), [패키지 manifest](evidence/historical/unity-vr-manifest.json), [변환 자산](evidence/historical/unity-mydesk.asset).

5개의 변환 데이터 파일은 총 64,318,080 bytes, 약 61.34 MiB다. 이는 저장용 데이터의 크기이며 런타임 GPU 메모리나 FPS는 아니다. 화면에서 압축 품질 프리셋을 확정할 수 없으므로 `High`·`Medium` 등을 임의로 붙이지 않았다.

반면 당시 화면에는 장면의 미저장 표시 `*`가 있고, 지금 [GaussianTestScene 저장본](evidence/historical/GaussianTestScene.unity)에는 Main Camera와 Directional Light만 있다. 압축 자산과 데이터 파일은 남아 있으므로 재연결할 수 있지만, 이 장면을 열기만 하면 사진과 같은 결과가 자동으로 나오는 상태는 아니다. 따라서 **Unity에서 표시한 성공 증거는 충분하지만 최종 장면 패키징은 불완전**하다.

헤드셋에서의 양안 렌더링, 추적, 성능 측정, APK 빌드, 충돌 메시 또는 로봇 연결은 확인하지 못했다. `GS_0224`의 일반 URP 프로젝트와 `UnityGaussianSplatting-1.1.1` 배포본도 존재하지만 이들의 폴더 존재를 별도의 완성된 연구실 VR 구현으로 세지 않았다.

## 2026-09-16 실제 재실행

먼저 자원을 점검했다. RTX 5060 Ti 16 GB, 시스템 RAM 약 31.65 GB, 당시 가용 RAM 약 15.11 GB였다. 오래된 WSL `gaussian_splatting` 환경은 Torch 1.12.1과 sm_120 미지원 경고, rasterizer 모듈 부재를 보였다. 대신 이미 설치된 Windows CUDA 환경의 **Torch 2.7.0+cu128 + diff_gaussian_rasterization**으로 텐서 연산·모듈 import를 확인한 뒤 실행했다. [자원 기록](evidence/outputs/20260916/resources.json), [실제 라이브러리 버전](evidence/outputs/20260916/environment-versions.json).

실행은 원본 PLY·이미지·카메라를 읽기만 하고 새 출력 디렉토리에 결과를 썼다. 기존 repo의 렌더러와 모델 로더를 사용했으며 입력 영상의 재인코딩을 3DGS 결과인 것처럼 사용하지 않았다. 모든 새 프레임은 PLY Gaussian을 카메라에 투영해 실제 rasterization으로 계산했다.

1. 7k와 30k 모델을 각각 59개 카메라에서 480×854로 렌더링했다.
2. 각 프레임에서 기준 영상과 PSNR·SSIM·L1을 계산하고 프레임별 CSV를 보존했다.
3. 30k 카메라 사이에서 회전을 SLERP, 위치를 선형 보간하여 464프레임/24 fps 영상을 만들었다. 이것은 기존 촬영 경로 주변의 보간 경로다.
4. 기존 30k PLY를 초기값으로 **fresh Adam 200회 추가 최적화**했다. seed 0, Gaussian 수 고정, densification·pruning·exposure 최적화 없이 위치·색 계수·opacity·scale·rotation을 업데이트했다. 손실은 `0.8 × L1 + 0.2 × (1 − SSIM)`이다. [학습률](evidence/outputs/20260916/refinement-learning-rates.json), [200회 loss 기록](evidence/outputs/20260916/refined_200/training-loss.csv).
5. 추가 최적화 후 같은 59개 시점으로 평가하고 7k/30k/refined 비교 영상을 만들었다.

| 모델·실험 | Gaussian 수 | 평균 PSNR ↑ | 평균 SSIM ↑ | 평균 L1 ↓ |
|---|---:|---:|---:|---:|
| 기존 7k 저장 모델의 새 렌더 | 720,554 | 30.9276 dB | 0.93243 | 0.015924 |
| 기존 30k 저장 모델의 새 렌더 | 1,067,490 | 34.0718 dB | 0.96184 | 0.010607 |
| 30k PLY 초기화 + 이번 200-step 실험 | 1,067,490 | 36.9819 dB | 0.97001 | 0.007641 |

**세 행 모두 기존 학습 시점 59개에서 평가한 값이다. 독립 시험 성능이 아니다.** 새 200회 최적화도 같은 영상들을 사용한다. PSNR 약 2.91 dB 상승은 그 시점·해상도에서의 적합도 향상이며 새로운 시점 일반화, 실측 형상 정확도 또는 원래 30k 학습을 다시 달성했다는 의미가 아니다. 기존 optimizer 상태를 복원하지 않았으므로 정확한 학습 resume로 부르지 않는다.

기록된 전체 실행시간은 44.83초, 추가 최적화와 PLY 저장을 포함한 해당 구간은 14.19초였다. Torch의 최대 allocated GPU memory는 1,736,743,936 bytes다. 이는 이번 저해상도 실행의 측정치이고 원래 고해상도 30k 학습 시간·VR FPS가 아니다. [실행 로그](evidence/outputs/20260916/run.log), [최적화 구간 기록](evidence/outputs/20260916/refined_200/refinement-timing.json).

![기존 30k 모델을 이번에 실제 재렌더한 한 시점](evidence/images/rerender-30000-view25.png)

전체 영상은 프레임 수를 실제로 디코딩해 확인했고 시작·중간·끝과 등록 시점 연락시트를 육안으로 점검했다. 중간 일부에 배경 사람이 포함되어 **공개 영상은 무인 구간만 선별**했다. 공개 카메라 경로는 200프레임·8.33초, 공개 비교 영상은 26시점·13초다. 전체 로컬 결과의 59시점 평가 수치와 공개 발췌 길이를 혼동하지 않도록 구분했다. [공개 미디어 목록](evidence/publication-manifest.json), [전체 영상 구조 검증 기록](evidence/outputs/20260916/video-verification.json).

## 재현 방법

원본 경로는 공개 README에 넣지 않았다. 해당 컴퓨터의 비공개 `source-map.json`을 이용해 `GRAPHDECO_ROOT`, `MYDESK`, 새 `NEW_OUTPUT` 위치를 정한다. `NEW_OUTPUT`은 기존 자료가 없는 별도의 폴더여야 한다.

```text
python -B -X utf8 -u evidence/rerun_mydesk.py \
  --repo GRAPHDECO_ROOT \
  --dataset MYDESK/gs_dataset \
  --model MYDESK/model \
  --out NEW_OUTPUT \
  --width 480 --steps 200 --interpolation 8
```

위는 플랫폼에 맞게 한 줄로 연결할 수 있는 인자 예시다. Graphdeco 소스는 `54c035f7834b564019656c3e3fcc3646292f727d`를 사용했다. 정확한 입력 SHA-256은 [입력 provenance](evidence/outputs/20260916/input-provenance.json)에 있고 주요 소스 모듈의 해시는 [실행 기록](evidence/run-record.json)에 있다. CUDA 확장 패키지의 버전 문자열은 `0.0.0`이므로 버전 문자열만으로 동일 빌드를 재구축할 수 있다고 보장하지 않는다.

파일 감사만 하려면 [inspect_historical.py](evidence/inspect_historical.py)에 비공개 소스맵과 새 출력 폴더를 전달한다. 이 스크립트는 COLMAP DB를 read-only로 열고 바이너리·PLY 헤더를 읽는다.

Unity를 복구하려면 기존 VR-URP 프로젝트의 사본에서 DX12를 선택하고 `GaussianTestScene`에 `GaussianSplatRenderer` 객체를 다시 연결한다. 남아 있는 `GaussianAssets`의 변환 자산과 5개 데이터 파일을 함께 유지해야 한다. 자산을 재생성할 때는 `Tools → Gaussian Splats → Create GaussianSplatAsset`에서 학습된 30k PLY를 선택한다. 사진의 pose는 참고값으로 삼아 장면 방향을 확인한 뒤 저장하고 다시 열어서 참조가 유지되는지 검증해야 한다. 이번 정리는 기존 Unity 프로젝트를 변경하거나 새로운 헤드셋 빌드를 실행하지 않았다.

처음부터 촬영→COLMAP→학습을 재실행할 경우 [당시 전처리 스크립트](evidence/historical/video_to_gs_dataset.py)는 재사용 가능하나, 대상 폴더를 초기화하는 코드가 있으므로 원본 폴더를 출력 대상으로 사용하면 안 된다. 이번 실행에서는 이 전처리를 다시 돌리지 않았다. 30,000회 전체 재학습도 이번 결과에 포함되지 않는다.

## 한계와 다음 개선

1. **먼저 입력 묶음을 고정해야 한다.** 원영상, 프레임, 보정 이미지, cameras/images/points3D, 학습 config와 모델을 하나의 실행 ID로 묶고 해시를 남긴다. 지금 확인된 카메라·초기점 불일치를 해소하는 것이 추가 성능 비교보다 우선이다.
2. **새 시점 평가를 분리해야 한다.** 기존 모델은 `eval=False`이며 이번 200회 실험은 학습 시점 평가다. 이후에는 촬영 구간을 나누어 겹치는 인접 프레임의 누출을 줄이고, 학습 전부터 고정한 holdout을 사용한다.
3. **촬영 범위와 동적 배경을 정리해야 한다.** 배경 사람이 일부 모델에 들어 있고, 주변부·가려진 영역은 번짐이 보인다. 사람이 없는 상태에서 노출·초점을 고정하고, 의자와 책상 아래·옆면의 겹침을 늘린 촬영을 별도 실험으로 설계할 수 있다.
4. **CloudCompare 평가 목표를 구체화해야 한다.** 기준 스캔 또는 실측 기준점이 있을 때만 좌표 정합·스케일을 고정하고 C2C/C2M 등 목적에 맞는 지표를 남긴다. 현재 점군 색상이나 화면 눈금을 정확도 수치로 대체하지 않는다.
5. **Unity 저장·배포를 마무리해야 한다.** 최종 장면의 renderer 연결, 필요한 자산 GUID, 그래픽 API, 카메라 pose를 보존하고 다시 열기 검증을 추가한다. VR 목표가 있다면 기기·양안 모드·해상도·splat 수별 FPS와 메모리를 실제 측정해야 한다.
6. **추가 최적화는 비교 실험으로 확장해야 한다.** 이번 200회는 빠른 동작 확인과 후속 최적화의 가능성을 보인 실험이다. 보정값 일치, 원해상도, 독립 시점 평가 없이 수치 상승을 연구 방법 개선으로 일반화하지 않는다.

## 보존한 근거와 제외한 자료

공개본에는 설명문, 전처리·감사·재실행 코드, 검증한 작은 자산 정의, 숫자 로그/CSV/JSON, 대표 화면, 무인 구간 영상만 포함한다. [복사 근거 목록](evidence/copied-evidence-manifest.json)은 선택 복사한 원본과 SHA-256을 대조한 기록이다. 절대 경로는 비공개 매핑으로 분리했다.

대형 원본 PLY, 원프레임 전체, COLMAP DB, `.psht`, upstream 소스 전체, Unity Library/캐시, 이번 264,739,052-byte 최적화 PLY와 503,861,677-byte optimizer 상태는 공개 저장소에 복사하지 않는다. 새 대형 결과는 로컬 날짜별 출력 폴더에 보존한다. 배경 사람이 포함된 전체 렌더와 연락시트도 로컬에만 남긴다. 메신저 자료는 조사·게시 범위에서 제외했다.

`Review/3D_Gaussian_Splatting_as_a_New_Era_A_Survey.pdf`는 관련 참고문헌 파일이 보존되어 있다는 것만 확인했다. 이 파일의 존재로 사용자가 논문 전체를 검토했거나 특정 방법을 채택했다고 추정하지 않았다. `3dgs_project`는 조사 당시 비어 있었고, `spectral-relighting-3dgs`의 후속 계획은 이 자리 복원의 실제 실험 성과에 합산하지 않았다.
