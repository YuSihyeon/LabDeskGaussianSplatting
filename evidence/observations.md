# 원자료 관찰 기록

작성·검증일: 2026-09-16. 파일 안의 설명이나 스크린샷은 당시 행위의 근거로 읽었으며, 현재 실행 지시로 사용하지 않았다. 아래 상대 경로의 실제 위치는 비공개 `source-map.json`에서 복원할 수 있다.

## 초기 물체·공간 복원

- `desktop_gs_root / gaussian splatting_bag/스크린샷 2025-12-27 141313.png`: Postshot의 가방 복원 장면이다. 가방 주변의 카메라 배열과 배경의 큰 번짐이 보인다. 화면 설정은 Splat3, downsample 1920 px, maximum splat count 3000 kSplats, maximum SH degree 3, stop training after 30 kSteps이다. 이 값들은 설정 또는 상한이며, 실제 최종 splat 수·학습 완료 회수를 뜻하지 않는다. 동일 폴더의 `untitled.psht`는 253,898,202 bytes이다. 원 프로젝트를 다시 열지는 않았다.
- `desktop_gs_root / gaussian splatting_lab/video.mp4`: 첫 프레임에 Polycam 표시가 있으며 실험실 일부의 표면 모델을 보여 준다. 측정한 길이는 8.0417초(193프레임, 24 fps), 크기는 960×720이다. [첫 프레임](images/lab_20251227-first-frame.jpg).
- `desktop_gs_root / gaussian splatting_lab/스크린샷 2025-12-27 145020.png`: 삼각면이 드러나는 부분 복원 표면, 큰 연결면·왜곡·빈 영역이 관찰된다. 동일 폴더 `2025. 12. 27.glb`는 666,836 bytes이다. 이 GLB 결과를 후속 3DGS 모델과 같은 알고리즘·같은 학습 결과로 취급하지 않았다.
- `desktop_gs_root / 2026_01_08/my desk.mp4`: 모니터에 표시된 연구실 자리 뷰어를 카메라로 촬영한 영상이다. 600프레임, 약 20.0183초이며, 원래 공간 촬영 영상과는 별개다. [첫 프레임](images/desk_20260108-first-frame.jpg).
- `wsl_graphdeco / source_video/mydesk.mp4`: 연구실 자리의 직접 촬영 영상이다. 986프레임, 약 32.895초, 1080×1920이다. 원본 전체는 공개 복사하지 않았다. [첫 프레임](images/wsl_source_video-first-frame.jpg). 각 영상의 해시는 [video-inventory.json](video-inventory.json)에 있다.

## CloudCompare

- [초기 점군 화면 사진](images/cloudcompare-20260105.jpg): 폴더명은 `2026_01_08`이지만 촬영된 Windows 작업표시줄 날짜는 2026-01-05이다. 폴더 날짜와 실제 촬영 날짜를 같다고 단정하지 않는다. 회전 조작 구와 색을 입힌 점군이 보인다. 화면의 눈금 30은 단위를 특정할 수 없으므로 30 m 등 실측 길이로 해석하지 않았다.
- `desktop_mydesk / 스크린샷 2026-05-28 091834.png`: CloudCompare v2.14.beta (Dec 28 2025), 64-bit. 콘솔에서 확장자 없는 파일 로드 실패 두 차례 다음에 `model/point_cloud/iteration_7000/point_cloud.ply`의 로드 성공을 확인했다. 화면에는 연구실 자리 주변의 점군과 회전 조작 구가 있다.
- `desktop_gs_root / 30000.png`: 같은 CloudCompare 화면에서 `model/point_cloud/iteration_30000/point_cloud.ply`의 로드 성공을 확인했다. 7k 화면과 시점·줌이 다르므로 겉보기 밀도만으로 두 모델의 오차를 비교할 수 없다.
- 7k/30k 화면은 개인 장치의 절대 경로를 포함하므로 공개 이미지에 포함하지 않고 위 내용을 전사했다. 파일의 원위치는 비공개 매핑에 남겼다.
- 조사한 범위에서 거리 비교·ICP·RMS·C2C·C2M의 저장 CSV/세션/보고서를 찾지 못했다. 따라서 과거 CloudCompare 사용은 **모델 로드와 시각적 점검까지 확인**되며 정량 정확도 분석 완료를 주장할 수 없다.

## Unity

- [당시 Unity 화면](images/unity-20260108.png)은 Unity 2022.3.62f3, DX12, VR-URP 프로젝트, GaussianTestScene을 보여 준다. GaussianSplat 객체에 renderer와 데이터 자산이 연결되어 있고 Splats 1,067,490, SH Order 3, Splat Scale 1, Opacity Scale 1, Device Radix Sort, Sort Nth Frame 1을 읽을 수 있다. Center Eye Only와 Optimize For Quest는 체크되어 있지 않다.
- 화면에서 객체 회전은 X 28.951, Y -173.597, Z -186.533이며 스케일은 모두 1이다. 이것은 당시 보이던 조정값이며 새로운 좌표 보정의 정답으로 일반화하지 않았다.
- 해당 화면의 장면명에는 `*`가 있다. 현재 [저장 장면](historical/GaussianTestScene.unity)에 GameObject로 저장된 이름은 Main Camera와 Directional Light뿐이다. `GaussianSplat` 객체가 포함된 최종 장면 저장본은 이 파일에서 확인되지 않는다.
- 반면 `.gitignore`로 기본 파일 검색에서 제외되던 `VR-URP/Assets/GaussianAssets`에는 [자산 정의](historical/unity-mydesk.asset)와 5개의 바이너리 데이터 파일이 실제 존재한다. 자산의 `m_SplatCount`도 1,067,490이다. 5개 데이터 파일 총합은 64,318,080 bytes이다. 자산 부재가 아니라 **장면 연결의 저장 상태 문제**다.
- Unity VR 저장소의 origin은 `ninjamode/Unity-VR-Gaussian-Splatting`, HEAD는 `ae603c5ac1c1ea854abca4dad92db4a4c723e22d`다. 로컬 Git 변경은 renderer 설정, OpenXR 설정, manifest/lock, Unity 버전이며 새 장면과 PLY는 미추적 파일이었다. 기존 패키지의 C#/shader 전체를 사용자의 독자 개발 코드로 귀속시키지 않았다.
- `GS_0224`는 Unity 2022.3.62f3/URP 14.0.12 프로젝트다. 조사한 Assets/Packages에서는 Gaussian Splatting 자산 또는 패키지 연결을 확인하지 못했다.
- `UnityGaussianSplatting-1.1.1`은 별도의 upstream 예제 배포본이다. 예제 `GSTestScene`의 존재만으로 연구실 데이터 연결이나 실행 성공을 판정하지 않았다.
- Unity의 `VR-URP/Assets/Scripts`에서 MuJoCo/robot/ROS 연결 흔적은 확인되지 않았다. 헤드셋 착용 실행, APK 빌드, 실제 VR FPS 또는 충돌·내비게이션 구현도 이 조사에서는 입증되지 않았다.

## 수치의 성격

- [historical-statistics.json](historical-statistics.json)은 기존 바이너리/DB/PLY를 2026-09-16에 읽어서 산출한 감사 통계다. 과거 학습 실행 당시 남긴 평가 로그가 아니다.
- [outputs/20260916/metrics-summary.json](outputs/20260916/metrics-summary.json)은 2026-09-16에 실제 GPU 재렌더링·추가 최적화하여 얻은 새 결과다.
- [metadata-consistency.json](metadata-consistency.json)은 동일 이름의 모델·보정 파일이 일관된 한 실행에서 나온 것인지 점검한 기록이다. 서로 다른 카메라 스냅샷과 점 수 차이가 확인되므로 원래 전처리부터 완전히 동일하게 재현했다고 주장하지 않는다.
