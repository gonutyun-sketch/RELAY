# RELAY — COOLING v01

2026-10-03 제작. 현재 Unity 씬의 COOLING 위치, 스위치/밸브/계기판 축에 맞춘 독립 Blender 아트 패키지입니다.

## 먼저 열 파일

- `RELAY_COOLING_v01.blend`: 수정 가능한 Blender 원본.
- `previews/COOLING_hero.png`: 전체 구조 렌더.
- `previews/COOLING_front.png`: 정면 배치 렌더.
- `previews/COOLING_controls.png`: 조작부 확대 렌더.
- `UNITY_HANDOFF.md`: 사용자가 직접 Unity에 연결하는 절차와 재질 값.

## 구성

노출형 프레임, 배관, 펌프와 모터, 리턴 탱크, 회전 밸브, 펌프 스위치, 유량계, 압력/온도 표시창으로 구성했습니다. 명판은 POWER 수정본과 같은 작은 인쇄식 판입니다. 움직이는 부품은 기존 게임 스크립트가 구동할 수 있도록 고정부에서 분리했습니다.

`exports`에는 FBX 9개가 있습니다.

| 파일 | 역할 |
|---|---|
| COOLING_Frame.fbx | 프레임, 배관, 펌프 모터, 탱크, 고정 브래킷 |
| PUMP_Housing.fbx | 펌프 스위치 고정부 |
| PUMP_Handle.fbx | 펌프 스위치 회전 손잡이 |
| VALVE_Housing.fbx | 배관 밸브 몸체와 고정 축 |
| VALVE_Wheel.fbx | 회전 휠 |
| FLOW_Housing.fbx | 유량계 몸체·눈금·표시창 |
| FLOW_Needle.fbx | 유량계 바늘 |
| FLOW_Glass.fbx | 선택적 유량계 유리 |
| THERMAL_Housing.fbx | 압력/온도 표시창 몸체 |

## Blender 안의 구조

- `01_EDITABLE_COOLING`: 개별 부품. 베벨과 노멀 수정자가 남아 있어 형태를 계속 조정할 수 있습니다. 명판/눈금 문자는 폰트 없이 열 수 있도록 메시로 변환했습니다.
- `02_NEUTRAL_FBX_MESHES`: 내보내기에 사용한 합쳐진 중립 자세 메시. 뷰포트와 렌더에서 숨겨져 있습니다.
- `03_PREVIEW_ONLY`: 바닥·카메라·스튜디오 조명·읽기 위치 확인용 임시 숫자. FBX에는 포함하지 않았습니다.

Blender의 `FLOW: 0 L/min`, `PRESS: 0 kPa` 등은 배치 검토용 숫자입니다. 게임의 실제 값은 기존 Unity TMP와 스크립트가 표시합니다. 렌더의 조명은 Unity 조명과 다르므로 게임 안에서 최종 밝기와 가독성을 확인해야 합니다.

## Unity 연결 전 알아둘 점

이 패키지는 Unity 프로젝트 밖에서 제작했습니다. Unity 씬, Inspector, 스크립트, 기존 모델은 자동으로 변경하거나 가져오지 않았습니다.

Unity에서는 기존 기능 오브젝트와 Collider를 유지하고, 회색 임시 외형의 Mesh Renderer를 숨긴 뒤 FBX를 지정 부모 아래에 연결합니다. 새 FBX 자식만 Local Position `(0,0,0)`, Local Rotation `(0,180,0)`, Local Scale `(1,1,1)`을 적용합니다. 기존 Pivot의 회전은 변경하지 않습니다. 자세한 순서는 `UNITY_HANDOFF.md`에 있습니다.

재질은 12종이며 별도 이미지 텍스처나 커스텀 셰이더가 필요하지 않습니다. Unity에서 독립 `.mat`로 연결하고 안내의 URP/Lit 값을 사용합니다. Blender의 내장 재질을 FBX 밖의 재질인 것처럼 연결하지 않습니다.

## 검증 범위

`checks/validation.json`에는 FBX 재가져오기 크기 검사, 좌표 유한성, 기존 회전축 위치, 밸브 회전 여유, 기존 클릭 부피와 휠 정점의 수학적 비교가 기록됩니다. 실제 Unity에서의 모델 방향, 반사, Raycast, 물리 충돌, 프레임 속도는 아직 테스트하지 않았습니다. 최종 확인은 사용자가 수동 연결한 뒤 수행합니다.

`manifest.json`에는 각 부품의 부모, 좌표, 재질, 폴리곤 수가 있습니다. 전체는 약 5.2만 삼각형입니다. 실측 성능 수치는 아닙니다.

## 제작 파일

`build_cooling.py`는 별도 Blender 프로세스에서 모델을 재생성하기 위한 원본입니다. 이 스크립트를 실행한 Blender 세션의 씬을 초기화하고 이 폴더의 출력물을 다시 만듭니다. 일반 검토에는 실행할 필요 없이 `.blend`를 열면 됩니다. 사용자 작업 중인 Blender의 콘솔에서 실행하지 마세요.

`validate_cooling.py`는 이 아트 폴더의 Blender/FBX만 읽고 검사 결과를 기록합니다. Unity를 실행하지 않습니다.
