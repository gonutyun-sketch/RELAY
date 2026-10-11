# RELAY — Forest Exit Integration 03

숲으로 올라온 광산 승강기의 뒤쪽 빈 공간과 바닥 틈을 마감하는 모델 패키지입니다. 실제 Blender 메시와 FBX를 제작했습니다. Unity 씬·Inspector·스크립트는 수정하지 않았습니다.

## 바로 열 파일

- `RELAY_ForestExit_Review.blend`: 기존 숲과 승강기를 함께 놓아 확인하는 파일. 기존 모델은 검토용이며 FBX에 중복 포함되지 않습니다.
- `RELAY_ForestExit.blend`: 이번에 납품하는 메시를 편집하는 파일.
- `UNITY_연결안내.md`: 사용자가 Unity에서 직접 연결하는 순서와 재질값.
- `previews/`: 실제 Blender 렌더. 게임 내 촬영 화면이 아닙니다. 안개·조명은 검토용으로, FBX에는 들어 있지 않습니다.

렌더는 `EXIT_01_From_Forest`(숲길에서 입구), `EXIT_02_Threshold_Detail`(문턱), `EXIT_03_From_Cage`(승강기에서 숲), `EXIT_04_Overview`(새 모델만 보이는 구조 확인)입니다. 구조 확인 화면에는 기존 승강기와 기존 숲 나무를 제외했으므로 빈 승강기 구멍이 보입니다.

## 구성

| FBX | 역할 |
|---|---|
| FOREST_Terrain | 승강기 구멍과 새 발판 자리를 절단한 기존 숲 지형 교체본 |
| FOREST_Undergrowth | 출구 발판·승강기 안으로 뚫고 나오던 풀 조각을 제거한 교체본 |
| EXIT_Hillside | 뒤쪽 배경을 가리는 바위·흙 산비탈. 승강기 자리에는 아래까지 열린 빈 공간이 있음 |
| EXIT_Headwall | 콘크리트 광산 입구, 문이 열리는 옆 공간의 가림판, 금속 마감 |
| EXIT_Landing | 고정 발판과 숲길로 이어지는 짧은 경사면 |
| EXIT_SealTrim | 발판 가장자리의 고무 마감과 아래쪽 가림판. 시각용 |
| EXIT_BackTrees | 새 산비탈에 심은 침엽수 16그루 |
| ELEVATOR_LandingApron | 승강기와 함께 움직이는 바닥 테두리 |

기존 숲 나무·바위 배치는 유지했습니다. 새 나무와 출구 구조물만 추가하고, 지형과 풀은 출구 작업 영역만 수정했습니다. 콘크리트·철판 텍스처는 2048px BaseColor와 OpenGL Normal로 제공하며, 기존 숲의 재질도 재사용합니다.

## 기준과 검증

- 길이 단위는 m. 새 FBX의 로컬 위치·회전은 0, 크기는 1로 연결합니다.
- 고정 모델 기준은 기존 `MountainEnding`, 이동 테두리 기준은 기존 `ELEVATOR_Module`입니다. 기존 승강기 FBX와 달리 새 모델에 추가 Y 180도 회전을 주지 않습니다.
- 기존 숲의 지형·풀 FBX 두 개는 같은 이름으로 교체하되 각각의 `.meta`를 유지합니다.
- 지형은 발판 아래까지 잘렸으므로 `EXIT_Landing`과 함께 적용합니다.
- `checks/independent_exit_audit.json`: 8개 FBX의 축·단위·UV·노멀·재질·퇴화면 및 이동 공간 검사 결과.
- 지형 구멍 1,561개, 산지 내부 통로 336개의 광선 검사에서 막힘이 없었습니다. 고정 모델과 현재 승강기 바닥·천장·레일·상단의 상승 경로 교차도 없었습니다.
- 도착 후 하향 사선 1,152개 검사에서 아래 허공으로 완전히 빠지는 광선은 없었습니다. 양쪽 레일 포켓을 비스듬히 보면 약 0.8m 깊이의 막힌 내부가 보일 수 있습니다. 레일 통로를 바닥으로 덮지는 않았습니다.
- 이 검사는 실제 메시와 저장된 씬 치수에 대한 검사입니다. Unity 임포트, 이동, 문 작동의 최종 확인은 사용자가 진행해야 합니다.

## 제작 재현

`scripts/build_exit.py`를 Blender 5.2 background 모드에서 실행하면 원본 `FOREST_02_Environment`와 `ELEVATOR_v01`을 읽어 이 패키지 안에만 새 결과를 만듭니다. 원본 두 패키지가 필요합니다. `scripts/make_exit_materials.py`는 재질 생성, `scripts/render_exit.py`는 실제 렌더, `scripts/finalize_package.py`는 검토용/편집용 Blender 파일 분리입니다.

`manifest.json`에는 내보낸 FBX별 크기·삼각형·재질·해시가, `checks/delivery_files.json`에는 납품 파일의 해시가 기록됩니다. 기존 프로젝트와 원본 아트에 적용하는 자동 실행 파일은 없습니다.
