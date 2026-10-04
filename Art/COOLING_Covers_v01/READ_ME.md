# RELAY COOLING — 보호 커버 추가 모델

COOLING의 열린 앞면과 좌우 측면에 얇은 투명 보호 커버를 추가하는 패키지입니다.

- 앞면: 유량계·펌프 스위치·밸브·온도 표시기가 통과하는 실제 구멍 4개.
- 측면: 원래 보호 레일과 간섭하지 않도록 간격을 둔 6mm 유리.
- 고정 부품: 기존 프레임 색상과 맞춘 테두리, 고무 패킹, 볼트, 고정 브래킷.
- 기존 COOLING 본체와 조작부는 계속 사용합니다.
- 기존 FLOW_Glass의 Unity 로컬 Z 0.01을 유지합니다.
- 새 FBX 4개와 새 유리 재질 1개만 추가합니다. Unity 씬·코드·Inspector는 자동 수정하지 않습니다.

## 파일

- `RELAY_COOLING_Covers_v01.blend`: 기존 COOLING과 새 커버를 함께 보는 편집 원본.
- `exports/`: 새 커버만 담은 FBX 4개.
- `previews/`: 실제 Blender 렌더.
- `UNITY_HANDOFF.md`: 사용자가 직접 Unity에 연결하는 단계별 안내.
- `manifest.json`: 치수, 재질, 연결 정보.
- `checks/validation.json`: 형상·FBX·조작부 간섭 검사.

`.blend`에는 기존 조작부와 미리보기용 숫자가 함께 보이지만, 이번 FBX에는 새 보호 커버만 들어갑니다. 기존 COOLING 모델을 통째로 다시 가져올 필요가 없습니다.

## 재생성

별도 Blender 백그라운드 프로세스에서 `build_covers.py`를 실행합니다. 빌드는 이 폴더에만 출력하며, 형제 폴더 `COOLING_v01/RELAY_COOLING_v01.blend`를 읽습니다. Unity 프로젝트는 쓰지 않습니다. `validate_covers.py`로 검사하고 `render_previews.py`로 미리보기를 만듭니다.

커버 유리의 Blender 재질은 실제 굴절을 사용합니다. Unity에서는 기본 URP Lit 투명 재질로 연결하므로 반사와 밝기가 똑같지는 않습니다. 최종 조정 기준은 게임 화면입니다.
