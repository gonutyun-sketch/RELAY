# RELAY — COOLING 모델 연결 안내

이 안내는 현재 `Startup_Graybox` 씬의 COOLING 조작부를 유지하면서 Blender 외형만 연결하는 절차입니다. Unity 조작은 사용자가 직접 합니다. 모델은 기존 좌표와 회전축에 맞춰 제작했지만, **Unity 안에서의 최종 외형·클릭 판정·가독성은 아직 확인하지 않았습니다.**

## 1. 준비

1. Play를 종료합니다.
2. 현재 씬을 저장합니다. 복구를 쉽게 하려면 사용자가 직접 씬 백업을 하나 남깁니다.
3. 아래 기존 구조와 이름을 확인합니다. 기존 오브젝트는 지우거나 다른 위치로 옮기지 않습니다.

```text
Environment
└─ COOLING_Module
   ├─ Panel_COOLING
   ├─ PUMP_Switch
   │  ├─ Body
   │  └─ HandlePivot
   │     └─ Handle
   ├─ FLOW_Valve
   │  ├─ Body
   │  ├─ Shaft
   │  └─ WheelPivot
   ├─ FLOW_Gauge
   │  ├─ Body / Face / Hub / Tick_0 / Tick_50 / Tick_100
   │  ├─ NeedlePivot
   │  │  └─ Needle
   │  └─ Readout
   └─ Cooling_Readout
      ├─ Housing / Face
      └─ StatusText
```

작업 대상은 이 구조 안의 **외형**입니다. `CoolingModule`, `PoweredSwitch`, `MachineDial`, `CoolingFlowGauge`와 연결된 참조는 그대로 둡니다.

## 2. FBX 가져오기

1. Project 창에 COOLING 아트용 폴더를 만듭니다. 예: `Assets/_STARTUP/Art/COOLING`.
2. 제공된 `exports` 폴더의 FBX 9개를 이 폴더로 가져옵니다. 이번 모델은 단색 재질과 실제 형상으로 표현하므로 **별도 텍스처 파일이 필요하지 않습니다.**
3. FBX의 Model 탭에서 **Generate Colliders는 꺼 둡니다.** 다른 가져오기 옵션은 우선 기본값을 유지합니다.
4. FBX 전체를 씬 한곳에 배치하지 말고, 다음 표대로 개별 모델을 연결합니다.

## 3. 모델별 부모 연결

Project 창의 FBX를 해당 부모 아래로 드래그한 뒤, **새로 들어온 FBX 인스턴스의 Transform만** 다음 값으로 입력합니다.

| 항목 | X | Y | Z |
|---|---:|---:|---:|
| Local Position | 0 | 0 | 0 |
| Local Rotation | 0 | 180 | 0 |
| Local Scale | 1 | 1 | 1 |

이 회전값은 POWER에서 확인한 가져오기 방향과 같습니다. **기존 `HandlePivot`, `WheelPivot`, `NeedlePivot`의 회전값을 바꾸는 작업이 아닙니다.**

| 새 FBX | 배치할 기존 부모 | 역할 |
|---|---|---|
| `COOLING_Frame` | `COOLING_Module` | 고정 외장과 배관 |
| `PUMP_Housing` | `PUMP_Switch` | 펌프 스위치 고정 몸체 |
| `PUMP_Handle` | `PUMP_Switch/HandlePivot` | 움직이는 스위치 손잡이 |
| `VALVE_Housing` | `FLOW_Valve` | 밸브 고정 몸체와 축 |
| `VALVE_Wheel` | `FLOW_Valve/WheelPivot` | 회전하는 밸브 휠 |
| `FLOW_Housing` | `FLOW_Gauge` | 유량계 몸체·눈금판 |
| `FLOW_Needle` | `FLOW_Gauge/NeedlePivot` | 움직이는 유량계 바늘 |
| `FLOW_Glass` | `FLOW_Gauge` | 선택적으로 사용할 유량계 유리 |
| `THERMAL_Housing` | `Cooling_Readout` | 압력·온도 표시창 외장 |

기존 스크립트의 `Moving Part`나 `Needle Pivot`을 새 FBX로 교체하지 않습니다. 기존 Pivot이 새 자식 모델을 함께 움직입니다.

## 4. 회색 임시 외형 숨기기

다음 **기존 오브젝트에서 Mesh Renderer 컴포넌트의 체크만 해제**합니다. 오브젝트 이름 옆의 활성화 체크나 Collider 체크를 끄지 않습니다. 기존 Collider가 클릭 판정과 충돌을 계속 담당합니다.

| 위치 | Mesh Renderer를 끌 기존 오브젝트 |
|---|---|
| `COOLING_Module` | `Panel_COOLING` |
| `PUMP_Switch` | `Body`, `HandlePivot/Handle` |
| `FLOW_Valve` | `Body`, `Shaft` |
| `FLOW_Valve/WheelPivot` | `Hub`, `Spoke_H`, `Spoke_V`, `PositionMark`, `Rim_Top`, `Rim_Bottom`, `Rim_Left`, `Rim_Right`, `Rim_TL`, `Rim_TR`, `Rim_BL`, `Rim_BR` |
| `FLOW_Gauge` | `Body`, `Face`, `Hub`, `Tick_0`, `Tick_50`, `Tick_100`, `NeedlePivot/Needle` |
| `Cooling_Readout` | `Housing`, `Face` |

새 모델에 이름이 같은 부품이 있을 수 있습니다. **기존 Graybox 자식인지 확인한 뒤** 체크를 바꿉니다. 부모를 한꺼번에 비활성화하면 조작 기능까지 멈출 수 있습니다.

다음 두 실시간 텍스트는 숨기거나 삭제하지 않습니다.

- `FLOW_Gauge/Readout`: 실제 유량과 밸브 개방률.
- `Cooling_Readout/StatusText`: 실제 압력과 온도.

두 텍스트의 위치·크기·글꼴·색은 우선 그대로 둡니다. 모델 표시창은 기존 어두운 글자를 읽을 수 있도록 밝은 바탕을 기준으로 합니다. 실행 중 숫자는 기존 코드가 갱신하며, FBX에 고정 숫자를 넣어 대체하지 않습니다.

새 이름표가 정상적으로 보인 뒤 중복되는 기존 `Label_COOLING`, `Label_FLOW`, `Label_PUMP`는 **텍스트 오브젝트만** 비활성화해도 됩니다. 조작부 부모는 계속 활성화합니다.

## 5. 기본 URP 재질 설정과 연결

**커스텀 셰이더나 Shader Graph는 만들지 않습니다.** 기본 `Universal Render Pipeline/Lit` 셰이더로 아래 재질을 설정하면 됩니다. Base Map에는 색상만 넣고, 텍스처·Normal Map·Emission은 사용하지 않습니다.

FBX에 포함된 재질이 정상적으로 보이면, 우선 그 상태에서 모델 위치와 회전을 확인할 수 있습니다. 최종 재질을 정리할 때는 COOLING용 `Materials` 폴더에 실제 `.mat` 파일을 만들거나 추출해 사용합니다. 이름은 아래와 동일하게 지정하면 연결할 때 구분하기 쉽습니다.

유리를 제외한 11개 재질의 공통값:

| 항목 | 값 |
|---|---|
| Shader | `Universal Render Pipeline/Lit` |
| Workflow Mode | Metallic |
| Surface Type | Opaque |
| Render Face | Front |
| Alpha Clipping | 꺼짐 |
| Base Map의 색상 Alpha | 255 / 1.0 |
| Emission | 꺼짐 |

색상 선택창의 HEX 칸에 아래 값을 입력합니다. Metallic과 Smoothness는 재질 Inspector의 숫자 값입니다.

| 재질 이름 | Base Map 색상 | Metallic | Smoothness |
|---|---|---:|---:|
| `RLYC_PumpBlue` | `#46686C` | 0 | 0.41 |
| `RLYC_FramePaint` | `#414D49` | 0 | 0.39 |
| `RLYC_InstrumentEnamel` | `#C4C3AF` | 0 | 0.38 |
| `RLYC_Steel` | `#838A85` | 0.80 | 0.63 |
| `RLYC_OxidizedSteel` | `#414944` | 0.65 | 0.42 |
| `RLYC_Rubber` | `#1B221F` | 0 | 0.20 |
| `RLYC_Bakelite` | `#30352F` | 0 | 0.55 |
| `RLYC_Brass` | `#89794D` | 0.72 | 0.53 |
| `RLYC_ValveRed` | `#87473C` | 0 | 0.47 |
| `RLYC_PrintDark` | `#252C28` | 0 | 0.22 |
| `RLYC_PrintLight` | `#DDD8C3` | 0 | 0.27 |
| `RLYC_MeterGlass` — 선택 사항 | `#F0F1E9` | 0 | 0.90 |

유리 `RLYC_MeterGlass`만 다음 값을 별도로 설정합니다.

| 항목 | 값 |
|---|---|
| Shader / Workflow | 위와 동일한 Lit / Metallic |
| Surface Type | Transparent |
| Blending Mode | Alpha |
| Preserve Specular Lighting | 켜짐 |
| Base Map의 색상 Alpha | 약 0.06 — 0~255 표시라면 15 |
| Receive Shadows | 꺼짐 |

`FLOW_Glass`의 Mesh Renderer에서는 Cast Shadows를 Off로 설정합니다. 이 유리는 선택 사항이며, 반사 때문에 바늘이 흐려지면 연결을 나중으로 미뤄도 됩니다. Blender의 투명 재질이 Unity로 동일하게 전달된다고 가정하지 말고 위 값을 확인합니다.

**다른 FBX를 펼쳤을 때 보이는 내장 재질을 Remapped Materials에 넣지 마세요.** POWER에서 발생했던 “sub-asset … cannot be used as an external material” 오류가 다시 생길 수 있습니다.

실제 `.mat` 파일을 만든 다음 외부 재질을 연결하는 순서:

1. Project에서 대상 FBX 선택 → Inspector의 Materials 탭.
2. Inspector 자물쇠를 잠급니다.
3. 실제 `Materials` 폴더를 엽니다.
4. 알맞은 `.mat` 파일을 해당 Remapped Materials 슬롯으로 드래그합니다.
5. Apply를 누르고 자물쇠를 풉니다.

먼저 한 부품으로 색상과 반사를 확인한 뒤 나머지 부품에 적용합니다. 유리가 불투명하게 보이거나 바늘을 가리면, 확인하는 동안 **새 `FLOW_Glass`의 Mesh Renderer만** 꺼 두어도 됩니다. 유리는 조작이나 계산에 필요하지 않습니다.

## 6. Play 확인

POWER를 정상적으로 가동한 상태에서 COOLING을 확인합니다.

1. 첫 클릭은 커서 잠금만 수행하며 스위치를 동시에 켜지 않는지 봅니다.
2. 펌프 스위치를 조준하고 왼쪽 클릭합니다. 새 손잡이가 고정 몸체에 붙은 채 회전해야 합니다.
3. 밸브를 조준하고 왼쪽 클릭 또는 R로 증가, Q로 감소시킵니다. 새 휠과 표시 마크가 함께 돌아야 합니다.
4. 밸브를 돌리면 유량계 바늘과 실시간 숫자가 함께 변하는지 봅니다. 압력은 밸브 값에 따라 달라지고, 온도는 서서히 변합니다.
5. 전원을 끄면 펌프가 OFF로 돌아가고 유량·압력이 0으로 바뀌는지 봅니다.
6. 정면과 비스듬한 방향에서 계기판·밸브가 서로 겹치지 않는지, 손잡이가 외장에 파고들지 않는지 확인합니다.
7. 휠 테두리와 손잡이의 보이는 위치를 조준했을 때 클릭이 먹는지 봅니다. 기존 Collider와 새 외형 사이의 차이는 실제 게임 화면에서 확인해야 합니다.
8. `Readout`, `StatusText`가 창 안에 들어오고 숫자 두 줄을 읽을 수 있는지, Console에 새 오류가 없는지 확인합니다.

펌프는 POWER가 꺼져 있으면 켤 수 없습니다. 이 상태에서 거부 표시가 나오는 것은 정상입니다. 모델 교체만으로 퍼즐 조건이나 조작 방식은 바뀌지 않습니다.

## 문제가 생겼을 때 되돌리기

새로 추가한 FBX 인스턴스 9개만 비활성화하고, 4단계에서 껐던 **기존 Mesh Renderer**를 다시 켜면 Graybox 외형으로 돌아갈 수 있습니다. 숨겼던 기존 이름표도 다시 켭니다. 실시간 텍스트와 Collider, Pivot, 스크립트는 처음부터 유지했으므로 다시 연결할 필요가 없습니다.

부품 하나만 잘못 보이면 해당 FBX 자식의 부모·로컬 Position·Rotation·Scale부터 확인합니다. 기존 조작부의 좌표나 스크립트 참조를 임의로 바꾸지 말고, Game 화면과 그 FBX 자식의 Transform 화면을 함께 확인해 수정 범위를 정합니다.
