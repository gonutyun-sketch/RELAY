# RELAY CORE v01 — Unity 수동 연결 안내

이 파일은 사용자가 Unity에서 직접 따라 하는 연결 안내다. 모델 제작 과정에서는 Unity 씬, 스크립트, Inspector를 수정하지 않았다.

이번 모델은 두 덩어리로 구성된다. `Core_Block` 자리에 중앙 반응기를 넣고, `CORE_Module`에는 START 레버·진행 게이지·고온/저온 표시가 있는 조작 캐비닛을 넣는다. 두 기존 오브젝트의 위치를 서로 합치거나 옮기지 않는다.

오늘 범위는 외형 연결이다. 전원을 올리면 연구실 조명이 켜지고 코어가 빛나며 전기가 튀는 연출은 다음 작업이다. 현재 `CORE_Emitter`도 발광을 끈 재질로 연결한다.

## 1. 모델 가져오기

1. Unity 재생을 중지하고 현재 씬을 저장한다.
2. Project에서 `Assets/_STARTUP/Art/CORE` 안에 `Models`, `Materials` 폴더를 만든다.
3. 탐색기에서 `C:/Users/gonut/RELAY_Art/CORE_v01/exports`를 연다.
4. FBX 파일 11개를 모두 Unity의 `CORE/Models`에 드래그한다. `.blend` 원본은 가져오지 않는다.
5. 원본 FBX를 선택한 Inspector의 Model 탭에서 `Generate Colliders`가 꺼져 있는지 확인한다. 켜져 있었다면 끄고 Apply한다.

새 모델에는 Rigidbody나 Collider를 추가하지 않는다. 기존 조작부와 `Core_Block`의 Collider를 그대로 사용한다.

## 2. 중앙 반응기 4개 연결

Hierarchy의 **기존 `Environment → Core_Block` 바로 아래**에 다음 FBX를 넣는다.

```text
Environment
└─ Core_Block                   ← 기존 오브젝트, Collider 유지
   ├─ CORE_Containment          ← 새 본체·바닥·내부 기구
   ├─ CORE_Glass                ← 새 원통 보호 유리
   ├─ CORE_Emitter              ← 새 발광용 표면, 현재는 발광 끔
   └─ CORE_Guardrail            ← 새 안전 난간
```

**새 모델 4개 각각** 다음 값을 입력한다. Scale 축 연결이 켜져 있으면 풀고 각 값을 따로 넣는다.

| 항목 | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0 | 0 |
| Rotation | 0 | 180 | 0 |
| Scale | 0.3333333333 | 0.2857142857 | 0.3333333333 |

부모 `Core_Block`의 기존 Scale은 `(3, 3.5, 3)`이다. 자식에서 이 배율을 보정해 모델이 원래 크기로 보이게 하는 값이다. **부모 Scale을 1로 바꾸거나 부모 Transform을 Reset하면 안 된다.**

현재 저장된 부모 값은 아래와 같다. 이는 확인용이며, 기존 값을 바꾸라는 뜻이 아니다.

```text
Core_Block
Position  0, 1.75, 6.5
Rotation  0, 0, 0
Scale     3, 3.5, 3
```

모델 원점은 반응기 중심이다. **새 모델 Position Y도 0이며, -0.5를 넣지 않는다.**

4개를 붙인 다음 **기존 `Core_Block`의 Mesh Renderer 체크만 끈다.** 오브젝트 전체 체크와 Box Collider는 켜 둔다. 새 모델의 Renderer는 켜 둔다.

반응기는 기존 3 × 3.5 × 3m 공간 안에 들어간다. 바닥판과 난간을 포함한 새 형상이 기존 Collider 범위를 넘어 앞으로 튀어나오지 않게 제작했다. 기존 기계 배치는 이번 단계에서 바꾸지 않는다.

## 3. 조작 캐비닛 7개 연결

아래 경로는 모두 `Environment → CORE_Module` 안이다. Project의 FBX를 해당 부모 위로 드래그한다.

| FBX 모델 | 부모로 둘 기존 오브젝트 |
|---|---|
| `CORE_Cabinet` | `CORE_Module` |
| `START_Housing` | `CORE_Module → START_Lever` |
| `START_Handle` | `CORE_Module → START_Lever → HandlePivot` |
| `STARTUP_GaugeHousing` | `CORE_Module → Startup_Gauge` |
| `HEAT_Housing` | `CORE_Module → HEAT_Indicator` |
| `COLD_Housing` | `CORE_Module → COLD_Indicator` |
| `STARTUP_Housing` | `CORE_Module → STARTUP_Indicator` |

**새 조작 캐비닛 모델 7개 각각** 아래 값을 사용한다. 앞의 중앙 반응기 4개와 Scale이 다르다.

| 항목 | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0 | 0 |
| Rotation | 0 | 180 | 0 |
| Scale | 1 | 1 | 1 |

구조는 다음과 같다. 표시하지 않은 기존 오브젝트도 그대로 둔다.

```text
CORE_Module
├─ Panel_CORE                        ← 기존
├─ CORE_Cabinet                      ← 새 모델
├─ START_Lever
│  ├─ Body                          ← 기존
│  ├─ Hinge                         ← 기존
│  ├─ START_Housing                 ← 새 모델
│  └─ HandlePivot                   ← 기존, 스크립트가 회전시킴
│     ├─ Handle                     ← 기존, Collider 유지
│     ├─ Grip                       ← 기존, Collider 유지
│     └─ START_Handle               ← 새 모델
├─ Startup_Gauge
│  ├─ Body                          ← 기존
│  ├─ Track                         ← 기존, 그대로 표시
│  ├─ FillPivot                     ← 기존, 크기 유지
│  │  └─ Fill                       ← 기존, 그대로 표시
│  └─ STARTUP_GaugeHousing          ← 새 모델
├─ HEAT_Indicator
│  ├─ Body                          ← 기존
│  ├─ Lens_Off                      ← 기존, 유지
│  ├─ Lens_On                       ← 기존, 유지
│  └─ HEAT_Housing                  ← 새 모델
├─ COLD_Indicator
│  ├─ Body                          ← 기존
│  ├─ Lens_Off                      ← 기존, 유지
│  ├─ Lens_On                       ← 기존, 유지
│  └─ COLD_Housing                  ← 새 모델
├─ STARTUP_Indicator
│  ├─ Body                          ← 기존
│  ├─ Lens_Off                      ← 기존, 유지
│  ├─ Lens_On                       ← 기존, 유지
│  └─ STARTUP_Housing               ← 새 모델
└─ Startup_Status                    ← 기존 동적 글자, 반드시 유지
```

`START_Handle`을 기존 `Handle`이나 `Grip` 아래에 넣으면 크기와 위치가 잘못된다. 반드시 **기존 `HandlePivot`의 바로 아래**에 넣는다. `Core Start Lever`의 Moving Part 연결도 기존 `HandlePivot` 그대로 둔다.

## 4. 겹치는 기존 외형 숨기기

다음 **기존 오브젝트의 Mesh Renderer 컴포넌트 체크만** 끈다. 오브젝트 전체 체크와 Collider는 유지한다.

| 기존 오브젝트 경로 | 끌 항목 |
|---|---|
| `Environment/Core_Block` | Mesh Renderer |
| `CORE_Module/Panel_CORE` | Mesh Renderer |
| `CORE_Module/START_Lever/Body` | Mesh Renderer |
| `CORE_Module/START_Lever/Hinge` | Mesh Renderer |
| `CORE_Module/START_Lever/HandlePivot/Handle` | Mesh Renderer |
| `CORE_Module/START_Lever/HandlePivot/Grip` | Mesh Renderer |
| `CORE_Module/Startup_Gauge/Body` | Mesh Renderer |
| `CORE_Module/HEAT_Indicator/Body` | Mesh Renderer |
| `CORE_Module/COLD_Indicator/Body` | Mesh Renderer |
| `CORE_Module/STARTUP_Indicator/Body` | Mesh Renderer |

새 모델 이름표가 표시되면 아래 **기존 고정 글자 6개는 오브젝트 전체 체크를 꺼도 된다.**

```text
CORE_Module/Label_CORE
CORE_Module/START_Lever/Label_START
CORE_Module/Startup_Gauge/Label_Gauge
CORE_Module/HEAT_Indicator/Label_LOCK
CORE_Module/COLD_Indicator/Label_LOCK
CORE_Module/STARTUP_Indicator/Label_LOCK
```

다음 항목은 숨기거나 교체하지 않는다.

- `Startup_Status`: STANDBY, STARTING, 완료/실패 상태를 표시하는 실제 글자다.
- `Startup_Gauge/Track`, `FillPivot`, `Fill`: 현재 진행률을 보여 주는 실제 게이지다.
- 세 표시등의 `Lens_Off`, `Lens_On`: 기존 코드가 켜고 끄는 실제 표시등이다.
- 기존 `Core Module`, `Core Panel Display`, `Core Start Lever` 컴포넌트와 그 안의 연결값.

새 모델은 게이지와 표시등 주변의 외장이다. 기존 Renderer 참조를 새 외장 Renderer로 바꾸면 기능이 잘못된다.

## 5. CORE 전용 재질 만들기

`Assets/_STARTUP/Art/CORE/Materials`에서 **Create → Material**로 실제 `.mat` 파일을 만든다. `RLYK_`는 이번 CORE 전용 이름이다. POWER·COOLING·SIGNAL의 기존 재질을 수정하지 않는다.

공통 설정:

- Shader: `Universal Render Pipeline/Lit`
- Workflow Mode: `Metallic`
- Surface Type: 아래 표에서 유리만 `Transparent`, 나머지는 `Opaque`
- Alpha Clipping: 끄기
- Render Face: `Front`
- Emission: 모두 끄기

Base Map 옆 색상 칸에서 HEX를 입력한다. 유리 외의 재질은 Alpha 1, 색상 창이 0~255 범위라면 255로 설정한다.

| 재질 이름 | HEX | Metallic | Smoothness | Surface Type |
|---|---|---:|---:|---|
| `RLYK_CasePaint` | `62655F` | 0 | 0.44 | Opaque |
| `RLYK_FramePaint` | `303B3D` | 0 | 0.43 | Opaque |
| `RLYK_Enamel` | `C8C5B2` | 0 | 0.40 | Opaque |
| `RLYK_Steel` | `939C9C` | 0.82 | 0.68 | Opaque |
| `RLYK_DarkSteel` | `444B4A` | 0.72 | 0.52 | Opaque |
| `RLYK_Rubber` | `191F1E` | 0 | 0.17 | Opaque |
| `RLYK_Bakelite` | `713E32` | 0 | 0.57 | Opaque |
| `RLYK_Brass` | `8B7754` | 0.73 | 0.58 | Opaque |
| `RLYK_PrintDark` | `242B2A` | 0 | 0.21 | Opaque |
| `RLYK_PrintLight` | `DED8C3` | 0 | 0.28 | Opaque |
| `RLYK_SafetyPaint` | `AD8740` | 0 | 0.51 | Opaque |
| `RLYK_ChamberGlass` | `CFE4E2` | 0 | 0.925 | Transparent |
| `RLYK_Emitter` | `B2D8DC` | 0 | 0.68 | Opaque |

유리 재질 `RLYK_ChamberGlass`의 추가 설정:

| 항목 | 값 |
|---|---|
| Surface Type | Transparent |
| Blending Mode | Alpha |
| Base Map 색상의 Alpha | 0.16, 즉 16% — 0~255 표시라면 약 41 |
| Render Face | Front |
| Alpha Clipping | 끄기 |
| Receive Shadows | 끄기 |
| Emission | 끄기 |

Hierarchy의 새 `CORE_Glass` 안에서 실제 **Mesh Renderer가 붙은 오브젝트**를 선택해 `Cast Shadows`를 `Off`로 설정한다. 유리만 해당하며 금속 본체와 난간에는 적용하지 않는다. `Receive Shadows`도 유리 재질에서 꺼 둔다.

`RLYK_Emitter`는 나중에 전원 상태에 따라 빛나게 만들 표면이다. **지금은 Emission을 켜지 않는다.** Blender의 발광 미리보기와 게임에서의 전원 제어는 별개다.

## 6. FBX 재질 연결

각 FBX에 아래 방법으로 재질을 연결한다.

1. **Project 창의 원본 FBX 파일**을 선택한다. Hierarchy의 인스턴스를 선택하는 단계가 아니다.
2. Inspector에서 `Materials` 탭을 연다.
3. Inspector 오른쪽 위 자물쇠를 잠가 선택을 고정한다.
4. Project에서 `CORE/Materials`를 연다.
5. `Remapped Materials`의 각 슬롯에 **이름이 같은 실제 `.mat` 파일**을 드래그한다.
6. Apply를 누르고 자물쇠를 푼다.
7. 다른 FBX도 반복한다.

FBX를 펼쳤을 때 그 안에 보이는 내장 재질은 사용하지 않는다. 그 재질을 외부 재질 슬롯에 넣으면 `is a sub-asset ... cannot be used as an external material` 오류가 날 수 있다. **Materials 폴더에 직접 만든 `.mat` 파일**을 연결해야 한다.

| FBX | 재질 슬롯 수 |
|---|---:|
| `CORE_Cabinet` | 7 |
| `START_Housing` | 5 |
| `START_Handle` | 4 |
| `STARTUP_GaugeHousing` | 5 |
| `HEAT_Housing` | 4 |
| `COLD_Housing` | 4 |
| `STARTUP_Housing` | 4 |
| `CORE_Containment` | 9 |
| `CORE_Glass` | 1 |
| `CORE_Emitter` | 1 |
| `CORE_Guardrail` | 3 |

같은 이름의 재질은 여러 FBX에서 함께 사용한다. 기존 동적 `Track`, `Fill`, `Lens_Off`, `Lens_On`, `Startup_Status`의 재질은 바꾸지 않는다.

## 7. 저장 후 확인

아래 항목은 사용자가 Unity에서 직접 확인한다. 모델 파일 검증은 실제 게임 플레이 검사를 대신하지 않는다.

1. 반응기 바닥이 바닥면에 맞고, 유리가 기둥 사이를 덮으며 내부 기구가 보인다.
2. 난간이나 본체가 다른 기계 안으로 들어가지 않고 기존 통로를 더 좁히지 않는다.
3. 조작 캐비닛의 이름표가 중복되지 않고, 하단 STANDBY 글자가 보인다.
4. 기존 순서대로 전력·냉각·신호를 준비한 뒤 START 레버를 작동시키면 새 손잡이가 기존 회전축을 따라 끝까지 움직인다.
5. 진행 게이지의 실제 막대가 왼쪽부터 차오르고 새 테두리에 가려지지 않는다.
6. 고온·저온·가동 표시가 기존처럼 켜지고 꺼진다.
7. 실제 완료/실패 문구가 계속 표시되고 문·엘리베이터 등 기존 게임 진행이 유지된다.
8. Console에 새 오류가 없다.

처음 Game 화면에서는 반응기에 전기 효과가 없고 발광 표면도 꺼져 있는 것이 현재 단계의 정상 상태다. 전원 켜짐 연출은 다음 구현 때 연결한다.

## 문제가 보일 때

| 증상 | 먼저 확인할 것 |
|---|---|
| 중앙 반응기가 너무 크거나 길쭉하다 | 새 반응기 4개의 Scale을 보정값으로 넣었는지, 부모 `Core_Block`은 기존 Scale인지 |
| 반응기가 바닥 밑으로 내려간다 | 새 모델 Local Position이 모두 0인지; 중심 원점이므로 Y=-0.5를 쓰지 않는지 |
| START 손잡이가 움직이지 않거나 크기가 이상하다 | 새 `START_Handle`이 `HandlePivot` 바로 아래인지, Scale1인지 |
| 조작부 클릭이 안 된다 | 기존 오브젝트 전체를 껐거나 Collider를 껐는지, 새 FBX에 불필요한 Collider가 생겼는지 |
| 진행 막대나 경고등이 안 보인다 | 기존 `Track`, `Fill`, `Lens_On`, `Lens_Off`를 숨겼는지, 스크립트의 Renderer 참조를 바꿨는지 |
| 상태 글자가 안 보인다 | `Startup_Status`를 껐는지, 새 모델 위치를 0이 아닌 값으로 옮겼는지 |
| 유리가 불투명하거나 속이 너무 어둡다 | `Transparent`, Alpha0.16, Front, Receive Shadows 끔, 유리 Renderer Cast Shadows Off인지 |
| 분홍색 재질이 나온다 | 해당 `.mat`의 Shader가 `Universal Render Pipeline/Lit`인지 |

위 안내대로 연결한 뒤 위치가 달라 보이면, Transform 값을 임의로 계속 바꾸기 전에 현재 Hierarchy와 Inspector를 확인한다. 기존 조작 코드와 기계 배치를 유지하면서 원인을 찾는다.
