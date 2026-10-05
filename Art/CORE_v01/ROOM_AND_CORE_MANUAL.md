# RELAY — 방 축소와 CORE 모델 연결

2026-10-05 저장된 `Startup_Graybox` 씬을 읽어 작성한 수동 적용안이다.
아래 값은 사용자가 Unity에 적용할 값이며, 아직 씬에 반영된 것이 아니다.
Unity 씬, 스크립트, Inspector는 자동으로 수정하지 않는다.

목표: 바닥 24×20m → 16×16m, 기존 천장 높이 6m 유지.
현재 출구 Z=-10과 엘리베이터·도착 지점은 유지한다. 뒤 벽만 Z=10에서6으로 이동한다.
새 방 바닥의 중심은 (0,0,-2)이다. 조명 개수·위치·크기·외형은 변경하지 않는다.

## 1. 준비

Play를 끄고 씬을 저장한다. 아래는 Inspector Transform의 Local 값이다.
기존 `Environment`는 Position0, Rotation0, Scale1 그대로 둔다.
기계 부모나 Environment 전체를 Scale로 줄이지 않는다.
숫자는 모두 X,Y,Z 순서다. 표에 없는 값은 그대로 둔다.

## 2. 바닥·벽·천장

모두 `Environment` 바로 아래다. Rotation은 기존0,0,0을 유지한다.

| 오브젝트 | Position | Scale |
|---|---|---|
| Floor | 0,-0.25,-2 | 16,0.5,16 |
| Ceiling | 0,6.15,-2 | 16,0.3,16 |
| Wall_Left | -8,3,-2 | 0.5,6,16 |
| Wall_Right | 8,3,-2 | 0.5,6,16 |
| Wall_Back | 0,3,6 | 16,6,0.5 |

기존 `Wall_Front`는 현재 비활성 상태다. 다시 켜지 않는다.
출입구 쪽 벽은 `EXIT_Module` 안의 분할 벽이 담당한다.

`Environment/EXIT_Module` 부모 Position은 **0,0,-10 그대로** 둔다.
그 아래 두 자식만 변경한다.

| 자식 | Local Position | Scale |
|---|---|---|
| Wall_LeftSection | -4.6,3,0 | 6.8,6,0.5 |
| Wall_RightSection | 4.6,3,0 | 6.8,6,0.5 |

중앙 문 폭2.4m, `Wall_Header`, `DoorMover`, `DoorRevealPoint`, `ELEVATOR_Module`과 도착 지점은 그대로 둔다.
출구 부모를 이동하면 엘리베이터 출발점과 고정 도착점의 관계까지 바뀔 수 있으므로 이번 배치는 출구 위치를 유지한다.

## 3. 기존 기둥과 천장 보

`Environment/LabStructure` 부모 Transform은 그대로 두고 자식만 바꾼다.

| 오브젝트 | Position | Scale |
|---|---|---|
| Pillar_LeftFront | -7.55,3,-5 | 0.4,6,0.65 |
| Pillar_RightFront | 7.55,3,-5 | 0.4,6,0.65 |
| Pillar_LeftBack | -7.55,3,5 | 0.4,6,0.65 |
| Pillar_RightBack | 7.55,3,5 | 0.4,6,0.65 |
| Beam_Front | 0,5.85,-5 | 14.7,0.3,0.65 |
| Beam_Back | 0,5.85,5 | 14.7,0.3,0.65 |

## 4. 기계 배치

다음은 `Environment` 바로 아래 부모 오브젝트를 선택해 Position만 바꾼다.
기계 안의 손잡이, 유리, 계기판 등 개별 자식은 이동하지 않는다.

| 오브젝트 | Position | Scale |
|---|---|---|
| Core_Block | 0,1.75,-1.5 | 기존3,3.5,3 |
| COOLING_Module | -3,1.2,4 | 기존1,1,1 |
| SIGNAL_Module | -1,1.2,4 | 기존1,1,1 |
| POWER_Module | 1,1.2,4 | 기존1,1,1 |
| CORE_Module | 3,1.2,4 | 기존1,1,1 |

`Environment/FloorMarkings` 부모 Position을 **-2,0,0**으로 바꾼다.
그 아래 기존 작업 구역 선3개의 Local 값은 그대로 둔다.

Hierarchy 최상위 `Player`의 Position은 **0,0.06,-5.5**로 바꾼다.
Player의 Rotation0,0,0과 Scale1,1,1은 유지한다. Main Camera 자식값은 바꾸지 않는다.

새 코어 충돌 범위는 X=-1.5..1.5, Z=-3..0이다.
새 Player 시작점 Z=-5.5는 코어 밖이다. 출구 카메라 지점도 기존 Z=-6을 유지한다.
네 조작 기계는 뒤편에 한 줄로 모이고 중앙 코어 양옆으로 접근하는 배치다.
이는 좌표로 확인한 배치이며 실제 이동·시야 평가는 사용자가 Play로 확인한다.

## 5. 중앙 코어 외형 연결

`exports`의 FBX11개를 기존 규칙대로 `Assets/_STARTUP/Art/CORE/Models`에 가져온다.
모델 Import Settings의 Generate Colliders는 끈다. `.blend`는 Assets에 넣지 않는다.

기존 `Environment/Core_Block` 아래에 다음4개를 자식으로 넣는다.

```text
Core_Block
├─ CORE_Containment
├─ CORE_Glass
├─ CORE_Emitter
└─ CORE_Guardrail
```

새 자식4개는 **각각** Local Position0,0,0 / Rotation0,180,0 /
Scale **0.3333333,0.2857143,0.3333333**으로 설정한다.
이는 부모의 기존3,3.5,3 배율을 보정하는 값이다.

붙인 뒤 기존 `Core_Block`의 **Mesh Renderer만 끈다**.
부모 오브젝트 전체 체크와 Box Collider는 유지한다.

## 6. 조작 캐비닛 외형 연결

아래 부모는 모두 `Environment/CORE_Module` 안이다.

| FBX | 붙일 부모 |
|---|---|
| CORE_Cabinet | CORE_Module |
| START_Housing | START_Lever |
| START_Handle | START_Lever/HandlePivot |
| STARTUP_GaugeHousing | Startup_Gauge |
| HEAT_Housing | HEAT_Indicator |
| COLD_Housing | COLD_Indicator |
| STARTUP_Housing | STARTUP_Indicator |

새 자식7개 각각 Local Position0,0,0 / Rotation0,180,0 / Scale1,1,1로 설정한다.

가져오기가 끝나면 아래 **기존 Mesh Renderer만** 끈다.

- `Panel_CORE`
- `START_Lever/Body`, `START_Lever/Hinge`
- `START_Lever/HandlePivot/Handle`, `START_Lever/HandlePivot/Grip`
- `Startup_Gauge/Body`
- `HEAT_Indicator/Body`, `COLD_Indicator/Body`, `STARTUP_Indicator/Body`

기존 Collider와 기능 스크립트 연결은 그대로 둔다.
`Track`, `FillPivot`, `Fill`, 세 표시등의 `Lens_Off`와 `Lens_On`, `Startup_Status`는 유지한다.
기존 고정 이름표6개만 새 외형과 중복될 경우 숨긴다. 전체 목록은 UNITY_HANDOFF.md의4번에 있다.

## 7. 재질과 확인

같은 폴더 `UNITY_HANDOFF.md`의 **5번 CORE 전용 재질 만들기**, **6번 FBX 재질 연결**을 따른다.
재질값과 FBX 연결법은 그대로다. 기존 안내의 Core_Block Z=6.5와 CORE_Module X=5는
축소 전 위치를 설명한 값이므로 되돌리지 않는다. **부모 배치는 이 문서의4번이 우선이다.**

유리는 URP/Lit Transparent, Alpha0.16, Smoothness0.925, RenderFaceFront,
ReceiveShadows 끔, 실제 Glass MeshRenderer의 CastShadows Off로 설정한다.
`RLYK_Emitter`의 Emission은 현재 끈다. 실제 전원·실험실 조명·전기 방전 연동은 후속 작업이다.

저장 후 직접 확인할 것:

1. Player가 코어 밖에서 시작하고 코어 양옆으로 이동할 수 있다.
2. 네 조작 기계에 접근해 기존 조작이 된다.
3. 코어 바닥이 지면에 붙고 유리 속 기구가 보인다.
4. START 레버, 진행률 막대, 고온·저온·가동등과 상태 문구가 표시된다.
5. 문 열림 장면과 엘리베이터 탑승·상승·도착까지 기존 진행이 유지된다.

이 작업안은 조명 개수·외형·크기를 변경하지 않으며, 실험실 아트 전체를 새로 재구성하지 않는다.
