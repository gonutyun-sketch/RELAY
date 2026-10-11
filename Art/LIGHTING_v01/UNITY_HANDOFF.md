# RELAY 조명 모델 수동 연결

이 문서는 사용자가 Unity에서 직접 적용할 작업 순서다. 제작 과정에서 Unity 씬, Inspector, 스크립트를 수정하지 않았다. 아래 배치 정보는 2026-10-06에 저장된 `Startup_Graybox.unity` 파일을 읽어 확인했다. 아직 저장하지 않은 Unity 화면의 상태는 포함하지 않는다.

이번 모델은 실험실용 긴 조명과 엘리베이터용 작은 보호망 조명 두 종류다. 기존 조명 네 개의 전원 연결을 사용한다.

## 1. 사용할 FBX

| 용도 | 외장 | 점등 면 | 보호 유리 |
|---|---|---|---|
| 실험실 조명 세 개 | `LIGHT_LinearHousing.fbx` | `LIGHT_LinearLens.fbx` | `LIGHT_LinearGlass.fbx` |
| 엘리베이터 조명 한 개 | `LIGHT_BulkheadHousing.fbx` | `LIGHT_BulkheadLens.fbx` | `LIGHT_BulkheadGlass.fbx` |

각 조명의 세 FBX는 같은 피벗을 사용한다. 피벗은 천장과 맞닿는 설치 면이며, 모델은 그 아래로 내려온다. Unity 기준 긴 방향은 Z축, 빛이 나오는 방향은 아래쪽인 -Y축이다.

| 모델 | 전체 폭 X | 피벗 아래 깊이 | 전체 길이 Z |
|---|---:|---:|---:|
| Linear | 최대 0.60m | 최대 0.19m | 최대 1.80m |
| Bulkhead | 최대 0.50m | 최대 0.17m | 최대 0.84m |

## 2. FBX와 외부 재질 가져오기

Play를 종료하고 현재 씬을 저장한다. Project 창의 기존 Art 폴더 아래에 `Lighting` 폴더를 만들고 위 FBX 여섯 개를 가져온다. 예: `Assets/_STARTUP/Art/Lighting`.

FBX는 제작된 실제 크기로 사용한다. Import Settings의 Scale Factor는 1로 두고, 씬에 넣은 모델의 Transform Scale도 `(1, 1, 1)`로 설정한다. 모델 축 변환은 FBX에 포함되므로 씬에서 X축을 90도로 추가 회전하지 않는다.

Housing에는 아래 이름의 외부 Material을 만든다. Shader는 모두 `Universal Render Pipeline/Lit`, Surface Type은 `Opaque`다. Base Map 색을 넣고 Metallic과 Smoothness를 설정한다. Emission은 사용하지 않는다.

| Material 이름 | Base Map HEX | Metallic | Smoothness |
|---|---|---:|---:|
| `RLYL_Paint` | `777C72` | 0 | 0.44 |
| `RLYL_Frame` | `303B3D` | 0 | 0.43 |
| `RLYL_Steel` | `939C9C` | 0.82 | 0.65 |
| `RLYL_Rubber` | `191F1E` | 0 | 0.17 |

보호 유리는 외부 Material `RLYL_Glass` 하나를 만든다.

| 설정 | 값 |
|---|---|
| Shader | `Universal Render Pipeline/Lit` |
| Surface Type | `Transparent` |
| Blending Mode | `Alpha` |
| Base Map | HEX `CFE0D8`, Alpha `0.12` |
| Metallic | `0` |
| Smoothness | `0.88` |
| Render Face | `Front` |
| Receive Shadows | 끄기 |
| Emission | 끄기 |

각 FBX를 Project에서 선택하고 Inspector의 **Materials → Remapped Materials**에서 같은 이름의 외부 재질을 연결한 뒤 Apply한다. FBX 안에 들어 있는 재질을 다른 FBX의 외부 재질로 연결하지 말고, Project 창에 직접 만든 `.mat` 파일을 사용한다.

**Lens의 `RLYL_Lens` 슬롯에는 기존 `Assets/_STARTUP/Materials/M_LightFace.mat`를 연결한다.** `M_LightFace`는 이미 전원 코드와 연결되는 `Universal Render Pipeline/Unlit` 재질이다. 새 Lens는 한 개의 MeshRenderer와 한 개의 재질 슬롯을 사용한다.

기존 코드는 Lens의 `_BaseColor`를 어둡게 해서 소등한다. Lens에 별도의 Emission을 추가하거나 Housing과 하나의 렌더러로 합치면 의도한 소등 방식과 달라진다. 발광하는 부분은 Lens 렌더러 하나로 유지한다.

## 3. 실험실용 조명 한 개부터 교체

Hierarchy에서 다음 경로를 펼친다.

```text
Environment
└─ Lighting
   ├─ Fixture_WorkLeft
   ├─ Fixture_WorkRight
   └─ Fixture_Exit
```

먼저 `Fixture_WorkLeft`의 바로 아래 자식으로 다음 FBX 세 개를 끌어 넣는다.

```text
Fixture_WorkLeft
├─ Housing                 기존 외장
├─ Lens                    기존 점등 면
├─ Light                   기존 실제 조명
├─ LIGHT_LinearHousing     새 모델
├─ LIGHT_LinearLens        새 모델
└─ LIGHT_LinearGlass       새 모델
```

새로 넣은 세 모델의 Transform을 각각 같은 값으로 설정한다. 이 값은 **부모 Fixture 기준 로컬 값**이다.

| 항목 | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0.05 | 0 |
| Rotation | 0 | 0 | 0 |
| Scale | 1 | 1 | 1 |

기존 Fixture의 Scale은 `(1, 1, 1)`이므로 CORE 때 사용한 역수 Scale을 입력하지 않는다. Fixture 부모 자체의 Scale도 바꾸지 않는다.

기존 `Housing`과 `Lens`는 **Mesh Renderer 컴포넌트 체크만 해제**한다. 기존 `Light`, Fixture 부모, 새 모델 오브젝트는 활성 상태로 둔다. 기존 오브젝트를 삭제할 필요는 없다.

새 `LIGHT_LinearGlass` 안의 실제 Mesh Renderer에서 **Cast Shadows를 Off**로 설정한다. Glass 재질의 Receive Shadows도 꺼져 있어야 한다. Housing은 기존처럼 그림자를 받을 수 있다.

같은 방법으로 `Fixture_WorkRight`와 `Fixture_Exit`에도 Linear 모델 세 개씩을 넣는다.

## 4. 엘리베이터 조명 교체

Hierarchy에서 다음 경로를 펼친다.

```text
Environment
└─ EXIT_Module
   └─ ELEVATOR_Module
      └─ Fixture_Cabin
         ├─ Housing
         ├─ Lens
         └─ Light
```

`Fixture_Cabin` 바로 아래에 `LIGHT_BulkheadHousing`, `LIGHT_BulkheadLens`, `LIGHT_BulkheadGlass`를 넣는다. 세 모델 모두 Position `(0, 0.05, 0)`, Rotation `(0, 0, 0)`, Scale `(1, 1, 1)`로 설정한다.

기존 `Housing`과 `Lens`의 Mesh Renderer만 끄고, 새 Glass의 Mesh Renderer는 Cast Shadows를 Off로 설정한다.

**`Fixture_Cabin`은 계속 `ELEVATOR_Module` 아래에 둔다.** 이 부모가 움직여야 천장, 기구, 실제 Light가 엘리베이터와 함께 올라간다. 일반 `Environment/Lighting` 아래로 옮기지 않는다.

## 5. 새 점등 면 네 개를 기존 전원 코드에 연결

`Environment → Core_Block`을 선택하고 기존 **Core Power Visual → Room Fixtures**를 펼친다. Size는 기존 `4`를 유지한다.

| 항목 | 기존 Light 칸 | 새로 연결할 Lens 칸 |
|---|---|---|
| Element 0 | `Lighting/Fixture_WorkLeft/Light` 유지 | 같은 Fixture의 `LIGHT_LinearLens` 안 MeshRenderer |
| Element 1 | `Lighting/Fixture_WorkRight/Light` 유지 | 같은 Fixture의 `LIGHT_LinearLens` 안 MeshRenderer |
| Element 2 | `Lighting/Fixture_Exit/Light` 유지 | 같은 Fixture의 `LIGHT_LinearLens` 안 MeshRenderer |
| Element 3 | `EXIT_Module/ELEVATOR_Module/Fixture_Cabin/Light` 유지 | 같은 Fixture의 `LIGHT_BulkheadLens` 안 MeshRenderer |

FBX 루트에 MeshRenderer가 없으면 FBX를 펼쳐 실제 메시 자식의 MeshRenderer를 연결한다. 각 항목에는 해당 Fixture의 Lens를 넣어야 하며, 같은 Lens 하나를 여러 항목에 반복 연결하면 안 된다.

Power Source, Emitter Renderer, Lab Reflection, Fade 설정은 기존 값을 사용한다. 스크립트 교체나 새 Light 추가는 필요 없다.

기존 Light 값은 다음과 같다. 이번 모델 크기에서는 그대로 사용한다.

| 항목 | 실험실 세 개 | 엘리베이터 한 개 |
|---|---|---|
| Local Position | `(0, -0.16, 0)` | `(0, -0.16, 0)` |
| Local Rotation | `(90, 0, 0)` | `(90, 0, 0)` |
| Type / Mode | Spot / Realtime | Spot / Realtime |
| Intensity | 18 | 4 |
| Range | 12 | 4 |
| Spot Angle | 110 | 110 |

Linear의 최하단은 Fixture 기준 Y=-0.14, Bulkhead 최하단은 Y=-0.12 안쪽이다. 기존 Light의 Y=-0.16은 두 모델의 아래에 있으므로 위치를 추가로 내리지 않아도 된다.

## 6. 출구 조명과 천장 보의 겹침 한 곳 조정

저장된 씬에서 `Fixture_Exit`는 Z=-6이다. 1.8m 길이의 기존 Housing은 Z=-5.1까지 뻗는데, `LabStructure/Beam_Front`는 Z=-5.325부터 있어 두 물체가 약 0.225m 겹친다.

모델을 연결한 뒤 사용자가 **Fixture_Exit 부모의 Position Z만 `-6.5`로 변경하는 것을 권장**한다.

| Fixture_Exit | X | Y | Z |
|---|---:|---:|---:|
| 권장 Position | 0 | 5.95 | -6.5 |
| Rotation | 0 | 0 | 0 |
| Scale | 1 | 1 | 1 |

이렇게 하면 1.8m 모델의 끝은 Z=-5.6이 되어 보와 0.275m 간격을 확보한다. 모델 세 개와 기존 Light가 같은 부모 아래 있으므로 함께 이동한다. 이 문서에서 위치를 실제로 바꾼 것은 아니다.

다른 조명의 위치와 개수 조정은 이 외형 교체와 점등 확인 후에 진행한다. 현재 저장된 부모 위치는 다음과 같다.

| Fixture | 현재 로컬 Position |
|---|---|
| WorkLeft | `(-1, 5.95, 1.8)` |
| WorkRight | `(5, 5.95, 1.8)` |
| Exit | `(0, 5.95, -6)` |
| Cabin | `(0, 2.95, -1.7)` — ELEVATOR_Module 기준 |

## 7. 사용자가 Play에서 확인할 항목

| 상태 | 정상 결과 |
|---|---|
| 처음 시작, AUX와 MAIN 모두 OFF | 네 기구의 새 Lens가 어둡고 실제 Light가 꺼짐 |
| AUX만 ON | 네 기구는 계속 소등 |
| MAIN ON | 실험실 세 개와 엘리베이터 한 개가 코어와 함께 부드럽게 점등 |
| MAIN OFF 또는 전원 조건 상실 | 네 Light와 새 Lens가 함께 어두워짐 |
| 엘리베이터 상승 | Cabin의 외장, Lens, Glass, 실제 Light가 모두 함께 움직임 |
| 전체 과정 | Console에 새 오류가 없고, 꺼 둔 기존 Lens는 보이지 않음 |

소등해도 실험실의 약한 환경 밝기와 금속 반사는 남을 수 있다. 이 작업은 기존 전원 동작에 새 기구 외형을 연결하는 단계이며, 실험실 전체 밝기나 엔딩 조명 설정을 바꾸지는 않는다.

이 체크리스트는 Unity 실행을 대신 검증한 결과가 아니다. Blender 결과물 및 파일 검증과 별도로, 사용자가 Unity에 연결한 뒤 확인할 항목이다.
