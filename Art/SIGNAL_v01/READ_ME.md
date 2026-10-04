# RELAY — SIGNAL 아트 패키지

기존 SIGNAL 퍼즐의 모니터, 주파수 다이얼, 가로 PHASE 슬라이더, 세로 GAIN 슬라이더, LOCK 표시등에 연결하는 Blender 외형입니다.

Unity의 기존 기능을 유지하며 새 모델을 각 조작부의 자식으로 연결합니다. Unity에서의 적용은 사용자가 직접 합니다. 제작 과정에서 Unity 씬·Inspector·스크립트를 대신 수정하지 않습니다.

## 파일 구성

- `RELAY_SIGNAL_v01.blend`: Blender 작업 원본.
- `exports/`: 기능별로 분리된 FBX 9개.
- `previews/`: 완성 외형 확인용 이미지.
- `UNITY_HANDOFF.md`: 현재 프로젝트 구조를 기준으로 한 수동 연결 절차.
- `manifest.json`: 모델별 부모·배치 기준과 재질 정보.
- `checks/`: 저장된 씬의 기준 정보와 모델 검증 결과.
- 제작·렌더·검증 스크립트: Blender 작업 재현용. Unity를 자동 조작하는 스크립트가 아닙니다.

## FBX 9개

| 파일 | 용도 |
|---|---|
| `SIGNAL_Cabinet.fbx` | 전체 캐비닛 고정 외장 |
| `SCOPE_Housing.fbx` | 기존 파형 화면을 둘러싸는 모니터 외장 |
| `FREQUENCY_Housing.fbx` | 주파수 다이얼 고정 몸체 |
| `FREQUENCY_Knob.fbx` | 회전하는 주파수 손잡이 |
| `PHASE_Housing.fbx` | 가로 슬라이더 고정 몸체 |
| `PHASE_Handle.fbx` | 가로로 움직이는 손잡이 |
| `GAIN_Housing.fbx` | 세로 슬라이더 고정 몸체 |
| `GAIN_Handle.fbx` | 세로로 움직이는 손잡이 |
| `LOCK_Housing.fbx` | 기존 표시등을 둘러싸는 고정 외장 |

## 연결할 때 기억할 것

일반 모델은 새 FBX의 로컬 Position `(0, 0, 0)`, Rotation `(0, 180, 0)`, Scale `(1, 1, 1)`로 연결합니다. **슬라이더 손잡이 2개만 예외**입니다. 기존 손잡이가 이미 비율이 다른 Cube이므로 새 모델의 Scale에서 그 배율을 상쇄합니다. 정확한 부모와 값은 `UNITY_HANDOFF.md`에 있습니다.

기존 Screen·ReferenceWave·CurrentWave와 표시등 Lens_Off·Lens_On은 계속 사용합니다. 미리보기에 등장하는 파형은 설명용이며 FBX에 포함되지 않습니다. 게임 안의 파형과 잠금 판정은 기존 코드가 담당합니다. 별도 유리 모델이나 가짜 파형을 화면 앞에 추가하지 않습니다.

기존 손잡이·Pivot·Collider·스크립트 참조를 유지하고, 임시 회색 외형의 Mesh Renderer만 숨깁니다. 새 모델의 Mesh Renderer까지 끄지 않도록 구분합니다.

파일과 형상 검증은 Unity의 실제 플레이 확인을 대신하지 않습니다. 적용 후 드래그 양 끝, 클릭 위치, 파형 표시, 잠금 표시등과 Console을 직접 확인해 주세요.
