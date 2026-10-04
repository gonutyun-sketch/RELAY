# RELAY — SIGNAL 모델 연결 안내

이 모델은 현재 `Startup_Graybox` 씬의 SIGNAL 기능과 조작 위치에 맞춘 외형입니다. Unity 조작은 사용자가 직접 합니다. 기존 스크립트·참조·Collider를 유지하고, 새 FBX를 자식으로 연결하는 방식입니다. Blender에서 확인한 결과와 Unity 게임 화면에서의 확인은 구분합니다. 최종 클릭 판정·파형 가독성·조명은 사용자가 Play 모드에서 확인해야 합니다.

한 번에 전부 연결하지 말고 아래 단계마다 저장하고 확인하세요.

## 1. 가져오기 전 확인

1. Play를 종료하고 현재 씬을 저장합니다.
2. Hierarchy에서 아래 구조가 있는지 확인합니다. 위치나 이름이 달라졌다면 먼저 차이를 확인합니다.
3. Project 창에서 `Assets/_STARTUP/Art/SIGNAL` 아래에 `Models`, `Materials` 폴더를 만듭니다.
4. 제공된 `exports` 폴더의 FBX 9개를 `Models`에 가져옵니다. `.blend` 파일은 Unity 밖의 작업 원본으로 보관합니다.
5. 각 FBX의 Model 탭에서 `Generate Colliders`를 끕니다. 새 모델에 추가 Collider를 만들지 않습니다.

```text
Environment
└─ SIGNAL_Module
   ├─ Panel_SIGNAL
   ├─ Label_SIGNAL
   ├─ Scope
   │  ├─ Housing
   │  ├─ Screen
   │  ├─ ReferenceWave
   │  └─ CurrentWave
   ├─ FREQUENCY_Dial
   │  ├─ Body
   │  ├─ Label_FREQUENCY
   │  └─ PointerPivot
   │     ├─ Knob
   │     └─ Pointer
   ├─ PHASE_Slider
   │  ├─ Body
   │  ├─ Track
   │  ├─ Handle
   │  └─ Label_PHASE
   ├─ GAIN_Slider
   │  ├─ Body
   │  ├─ Track
   │  ├─ Handle
   │  └─ Label_GAIN
   └─ LOCK_Indicator
      ├─ Body
      ├─ Lens_Off
      ├─ Lens_On
      └─ Label_LOCK
```

## 2. 본체와 모니터 외장

Project 창의 `SIGNAL_Cabinet.fbx`를 Hierarchy의 기존 `SIGNAL_Module` 위로 드래그합니다. 새로 추가한 모델만 선택해서 다음 값을 입력합니다.

| 새 모델의 Transform | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0 | 0 |
| Rotation | 0 | 180 | 0 |
| Scale | 1 | 1 | 1 |

`SCOPE_Housing.fbx`는 기존 `SIGNAL_Module/Scope` 아래로 넣고 같은 값을 입력합니다.

| 새 FBX | 넣을 부모 |
|---|---|
| `SIGNAL_Cabinet` | `SIGNAL_Module` |
| `SCOPE_Housing` | `SIGNAL_Module/Scope` |

기존 `Panel_SIGNAL`과 `Scope/Housing`의 **Mesh Renderer 체크만** 끕니다. 오브젝트 전체와 Collider는 계속 켜 둡니다. 새 모델의 Mesh Renderer는 켜 둡니다.

기존 `Scope/Screen`, `Scope/ReferenceWave`, `Scope/CurrentWave`는 그대로 유지합니다. 새 외장은 실제 파형이 지나가는 가운데가 열린 구조입니다. 화면의 격자는 새 모델에 포함돼 있지만, 파형과 검은 화면은 기존 Unity 오브젝트가 계속 담당합니다. 모델 미리보기의 파형은 설명용이며 FBX에 포함되지 않습니다.

모니터에 유리를 추가하는 단계는 없습니다. 화면 앞에 Cube나 불투명한 판을 추가하면 기존 파형을 가릴 수 있습니다.

## 3. 주파수 다이얼

다음 두 모델을 각각 해당 부모에 넣습니다. 새 FBX의 Position은 `(0, 0, 0)`, Rotation은 `(0, 180, 0)`, Scale은 `(1, 1, 1)`입니다.

| 새 FBX | 넣을 기존 부모 |
|---|---|
| `FREQUENCY_Housing` | `SIGNAL_Module/FREQUENCY_Dial` |
| `FREQUENCY_Knob` | `SIGNAL_Module/FREQUENCY_Dial/PointerPivot` |

기존 `FREQUENCY_Dial/Body`, `PointerPivot/Knob`, `PointerPivot/Pointer`의 Mesh Renderer만 끕니다. 기존 `PointerPivot`은 계속 켜 둡니다.

`Machine Dial` 컴포넌트의 `Moving Part`는 기존 `PointerPivot`을 유지합니다. 새 손잡이가 그 자식이므로 기존 회전에 따라 함께 움직입니다. 새 FBX를 `Moving Part` 슬롯에 넣지 않습니다.

저장하고 실행해서 다이얼을 조준한 뒤 왼쪽 클릭 또는 R로 증가, Q로 감소시킵니다. 새 손잡이의 표시가 중심을 기준으로 도는지 확인합니다.

## 4. 가로 PHASE 슬라이더

이 단계는 손잡이 Scale이 다른 모델과 다릅니다. 기존 손잡이는 크기 조절된 Cube이므로 새 모델에서 그 배율을 상쇄합니다.

`PHASE_Housing.fbx`는 기존 `PHASE_Slider` 아래에 넣고 다음 값을 입력합니다.

| 새 `PHASE_Housing` | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0 | 0 |
| Rotation | 0 | 180 | 0 |
| Scale | 1 | 1 | 1 |

`PHASE_Handle.fbx`는 **기존 `PHASE_Slider/Handle`의 자식**으로 넣습니다.

```text
PHASE_Slider
├─ Body
├─ Track
├─ Handle                 ← 기존 오브젝트: 이동·클릭 판정 유지
│  └─ PHASE_Handle        ← 새 모델
└─ PHASE_Housing          ← 새 고정 몸체
```

새 `PHASE_Handle`에만 다음 값을 입력합니다. Scale 축이 묶여 있으면 연결을 풀고 축마다 입력합니다.

| 새 `PHASE_Handle` | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0 | 0 |
| Rotation | 0 | 180 | 0 |
| Scale | **14.285714** | **7.142857** | **14.285714** |

기존 `Handle`의 Scale `(0.07, 0.14, 0.07)`과 위치는 바꾸지 않습니다. 기존 `Machine Slider`의 `Moving Part` 역시 기존 `Handle`을 유지합니다.

기존 `Body`, `Track`, `Handle`의 Mesh Renderer만 끕니다. 특히 기존 `Handle` 오브젝트 전체를 끄면 새 손잡이도 사라지고 조작에 문제가 생깁니다. 새 `PHASE_Handle`의 Mesh Renderer는 계속 켭니다.

저장하고 실행한 뒤 손잡이를 조준하고 왼쪽 버튼을 누른 채 좌우로 끌어 봅니다. 양 끝까지 이동해도 손잡이가 레일에서 벗어나지 않는지 확인합니다. Q와 R로 미세 조정도 확인합니다.

## 5. 세로 GAIN 슬라이더

`GAIN_Housing.fbx`를 기존 `GAIN_Slider` 아래에 넣습니다. Position `(0, 0, 0)`, Rotation `(0, 180, 0)`, Scale `(1, 1, 1)`입니다.

`GAIN_Handle.fbx`는 **기존 `GAIN_Slider/Handle`의 자식**으로 넣습니다.

| 새 `GAIN_Handle` | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0 | 0 |
| Rotation | 0 | 180 | 0 |
| Scale | **7.142857** | **14.285714** | **14.285714** |

PHASE와 X·Y 배율이 반대입니다. 기존 GAIN `Handle`의 Scale `(0.14, 0.07, 0.07)`은 바꾸지 않습니다. `Machine Slider`의 `Moving Part`는 기존 `Handle`을 유지합니다.

기존 `GAIN_Slider/Body`, `Track`, `Handle`의 Mesh Renderer만 끄고 새 모델의 Mesh Renderer는 켭니다.

저장하고 실행한 뒤 손잡이를 위아래로 끌어 양 끝까지 움직입니다. 새 손잡이가 레일 안에서 움직이는지, 손잡이의 보이는 위치에서 드래그가 시작되는지 확인합니다.

## 6. LOCK 표시등 외장

`LOCK_Housing.fbx`를 기존 `LOCK_Indicator` 아래에 넣습니다. Position `(0, 0, 0)`, Rotation `(0, 180, 0)`, Scale `(1, 1, 1)`입니다.

기존 `LOCK_Indicator/Body`의 Mesh Renderer만 끕니다. **`Lens_Off`와 `Lens_On`은 숨기거나 삭제하지 않습니다.** 두 렌즈가 기존 표시등입니다. `SignalScope`가 기존 `Lens_On`의 Mesh Renderer를 켜고 끄므로 새 모델로 참조를 바꾸지 않습니다.

Play 중 파형이 맞지 않으면 켜진 렌즈가 보이지 않고, 파형을 맞춘 상태가 유지되면 기존 로직에 따라 표시등이 켜집니다. 모델은 표시등 바깥의 테두리와 몸체만 담당합니다. 외형의 `SYNC` 글자는 이 기존 LOCK 상태를 표시하는 이름표입니다.

## 7. 중복 이름표 정리

새 이름표가 정상적으로 보인 뒤 아래 **기존 텍스트 오브젝트만** 비활성화합니다.

- `SIGNAL_Module/Label_SIGNAL`
- `FREQUENCY_Dial/Label_FREQUENCY`
- `PHASE_Slider/Label_PHASE`
- `GAIN_Slider/Label_GAIN`
- `LOCK_Indicator/Label_LOCK`

조작부의 부모나 `Scope`를 비활성화하지 않습니다. 스크립트가 사용하는 파형·표시등·손잡이 참조도 유지합니다.

## 8. 재질 연결

이 패키지는 단색 재질과 실제 형상으로 제작했습니다. 별도 이미지 텍스처가 필요하지 않습니다. 아래 12개 재질을 만듭니다. `manifest.json`에도 같은 정보가 있습니다.

재질은 Project의 `SIGNAL/Materials` 폴더에 독립된 `.mat`로 만듭니다. Shader는 `Universal Render Pipeline/Lit`, Workflow는 `Metallic`, Surface Type은 `Opaque`, Alpha Clipping과 Emission은 끕니다. 색상의 Alpha는 1 또는 255로 둡니다.

| 재질 이름 | HEX 색상 | Metallic | Smoothness |
|---|---|---:|---:|
| `RLYS_CasePaint` | `626A60` | 0 | 0.40 |
| `RLYS_FramePaint` | `363E3A` | 0 | 0.38 |
| `RLYS_Enamel` | `C8C5B2` | 0 | 0.36 |
| `RLYS_Steel` | `959B96` | 0.80 | 0.65 |
| `RLYS_OxidizedSteel` | `454E49` | 0.65 | 0.41 |
| `RLYS_Rubber` | `1B221F` | 0 | 0.18 |
| `RLYS_Bakelite` | `2B302C` | 0 | 0.56 |
| `RLYS_Brass` | `89794D` | 0.72 | 0.51 |
| `RLYS_PrintDark` | `252C28` | 0 | 0.21 |
| `RLYS_PrintLight` | `DED8C3` | 0 | 0.28 |
| `RLYS_GainCap` | `AC925E` | 0 | 0.46 |
| `RLYS_Graticule` | `355346` | 0 | 0.10 |

`RLYS_Graticule`은 화면 격자, `RLYS_GainCap`은 세로 GAIN 손잡이의 황토색입니다. 파형 자체의 발광 재질은 이 표에 포함되지 않으며 기존 Unity 파형 재질을 유지합니다.

각 FBX를 Project에서 선택하고 Materials 탭의 `Remapped Materials`에 이름이 같은 `.mat`를 연결한 뒤 Apply합니다. Inspector 자물쇠를 잠그면 다른 폴더에서 재질을 끌어올 때 편합니다. 연결을 마치면 자물쇠를 풉니다.

| FBX | 재질 슬롯 수 |
|---|---:|
| `SIGNAL_Cabinet` | 9 |
| `SCOPE_Housing` | 8 |
| `FREQUENCY_Housing` | 5 |
| `FREQUENCY_Knob` | 4 |
| `PHASE_Housing` | 5 |
| `PHASE_Handle` | 4 |
| `GAIN_Housing` | 5 |
| `GAIN_Handle` | 3 |
| `LOCK_Housing` | 4 |

각 슬롯의 순서보다 이름을 기준으로 연결합니다. 한 모델에 12개 재질이 모두 쓰이는 것은 아닙니다.

FBX 아래에 펼쳐지는 내장 재질을 외부 재질 슬롯에 넣지 않습니다. 반드시 방금 만든 `.mat` 파일을 사용합니다. 예전에 발생한 `sub-asset ... cannot be used as an external material` 오류는 내장 재질을 외부 재질로 넣으려 할 때 생깁니다.

기존 `Screen`, `ReferenceWave`, `CurrentWave`, `Lens_Off`, `Lens_On`의 재질은 우선 유지합니다. 이번 FBX 재질 설정으로 기존 파형과 표시등 재질을 대체하지 않습니다.

## 9. Game 화면 확인

1. 첫 클릭으로 커서를 잠갔을 때 조작부가 동시에 작동하지 않는지 확인합니다.
2. POWER를 정상 가동한 뒤 SIGNAL 화면에 기존 두 파형이 나타나는지 확인합니다. 전원이 없을 때 파형이 안 보이는 것은 기존 동작입니다.
3. 주파수 다이얼을 돌리면 새 손잡이와 실제 파형의 간격이 함께 변하는지 확인합니다.
4. PHASE 손잡이를 좌우로 끌면 실제 파형이 옆으로 이동하는지 확인합니다.
5. GAIN 손잡이를 위아래로 끌면 실제 파형의 높이가 변하는지 확인합니다.
6. 슬라이더를 양 끝까지 이동한 뒤에도 보이는 손잡이에서 드래그와 Q/R 조정이 되는지 확인합니다.
7. 파형을 맞춘 상태를 유지하면 LOCK 표시등과 기존 퍼즐 판정이 작동하는지 확인합니다.
8. 정면과 옆에서 파형·눈금·조작부 이름이 읽히는지, 겹친 표면이 깜빡이지 않는지 확인합니다.
9. Console에 새로운 오류가 없는지 확인하고 Play를 종료한 뒤 저장합니다.

Play 중 변경한 Transform은 Play를 종료하면 되돌아갑니다. 위치를 조정했다면 종료 후 같은 값을 다시 입력하고 저장합니다.

## 문제가 보일 때

| 증상 | 먼저 확인할 내용 |
|---|---|
| 새 모델이 통째로 안 보임 | 새 FBX의 Mesh Renderer까지 꺼졌는지 확인합니다. 기존 외형만 숨깁니다. |
| PHASE 또는 GAIN 손잡이가 아주 작음 | 새 손잡이의 부모가 기존 `Handle`인지, 위의 축별 Scale 값을 입력했는지 확인합니다. |
| 손잡이 모양이 찌그러짐 | 기존 `Handle` Scale을 그대로 두었는지, PHASE와 GAIN의 서로 다른 보정 배율을 사용했는지 확인합니다. |
| 드래그해도 새 손잡이가 안 움직임 | 새 FBX가 `PHASE_Slider`/`GAIN_Slider` 바로 아래가 아니라 기존 `Handle`의 자식인지 확인합니다. |
| 파형이 안 보임 | 먼저 POWER 가동 여부와 기존 두 Line Renderer의 참조·오브젝트 활성화를 확인합니다. `Screen`과 두 파형을 삭제하지 않습니다. |
| LOCK 판정은 되는데 불이 안 보임 | 기존 `Lens_Off`, `Lens_On` 오브젝트가 활성화돼 있고 `SignalScope`의 기존 `Lock Lamp` 참조가 유지돼 있는지 확인합니다. |
| 모델이 뒤를 보고 있음 | 새 FBX 인스턴스의 로컬 Rotation Y가 180인지 확인합니다. 기존 기능 오브젝트를 돌리지 않습니다. |

외형만으로 해결되지 않는 현상이 생기면 해당 오브젝트를 선택한 Inspector와 Game 화면을 확인한 뒤 조정합니다. 파형 계산, 퍼즐 수치, 조작 코드 변경은 이 모델 연결 작업에 포함되지 않습니다.
