# RELAY — 숲 출구 모델 연결

이번 모델은 **승강기 뒤를 가리는 산비탈·광산 입구**, **지상 발판**, **승강기 가장자리 틈 마감**이다. 기존 승강기와 숲을 유지하면서 외형을 덧붙인다. 아래 연결은 사용자가 Unity에서 직접 진행한다.

제작 기준은 확인한 저장 씬의 `MountainEnding`과 `ELEVATOR_Module` 치수다. 이후 이 두 부모의 위치·회전·크기를 바꿨다면 먼저 원래 배치를 확인해야 한다. Blender와 FBX 형상 검사는 마쳤지만 Unity에서 연결·플레이 검증을 대신 수행한 것은 아니다.

## 1. Play를 멈추고 파일 가져오기

1. 현재 씬을 저장한다.
2. 기존 `C:\Users\gonut\School_p2\Assets\RELAY\Art\Forest\exports` 폴더의 `FOREST_Terrain.fbx`와 `FOREST_Undergrowth.fbx`를 **프로젝트 밖에 백업**한다.
3. 이 패키지의 `exports`에 있는 같은 이름의 FBX 2개로 위 기존 파일만 각각 덮어쓴다. **두 파일의 기존 `.meta`는 삭제하거나 덮어쓰지 않는다.** Hierarchy의 기존 지형·풀 오브젝트도 유지한다. 새 Undergrowth는 발판과 승강기 바닥을 뚫고 나오던 출구 작업 영역의 풀 조각만 제거한 버전이다.
4. 나머지 FBX 6개와 `textures`의 `RLYX_`로 시작하는 PNG 4개를 Unity의 새 아트 폴더에 가져온다. 예: `Assets/RELAY/Art/ForestExit`.
5. 새 FBX는 Import Scale `1`, Bake Axis Conversion 끔, Generate Colliders 끔을 기준으로 한다. 기존 지형의 임포트 설정과 재질 연결은 유지한다.

FBX는 총 **8개**다. 기존 파일 교체 2개, 새 고정 모델 5개, 새 이동 모델 1개로 나뉜다.

**교체 지형은 새 발판이 들어갈 부분까지 비워 놓았다. `EXIT_Landing`을 함께 배치하기 전에는 지면에 구멍이 크게 보이는 것이 정상이다.** 기존 지형·풀과 새 교체본을 동시에 배치하지 않는다. 다른 숲 모델과 배치는 유지한다.

## 2. 움직이지 않는 출구 배치

`MountainEnding` 아래 빈 오브젝트 `EXIT_Visual`을 만들고 다음 5개 FBX를 그 아래에 넣는다.

```text
MountainEnding                         ← 기존 도착 지점 유지
├─ Forest_Visual                       ← 기존 숲 유지
└─ EXIT_Visual                         ← 새 빈 오브젝트
   ├─ EXIT_Hillside                    ← 산비탈과 바위
   ├─ EXIT_Headwall                    ← 광산 입구와 문 옆 가림판
   ├─ EXIT_Landing                     ← 지상 발판과 숲길 연결부
   ├─ EXIT_SealTrim                    ← 틈 마감
   └─ EXIT_BackTrees                   ← 뒤쪽 산비탈의 나무
```

`EXIT_Visual`과 위 FBX 5개의 Transform을 **부모 기준 Position `(0,0,0)`, Rotation `(0,0,0)`, Scale `(1,1,1)`**로 맞춘다. 개별 모델의 원점에 필요한 배치가 들어 있으므로 눈대중으로 다시 옮기지 않는다.

새 FBX는 방향 보정이 이미 들어 있다. **Y를 180도로 돌리지 않는다.** 기존 승강기 모델의 Y 180도 설정은 그대로 둔다. `MountainEnding` 자체를 이동하거나 회전하지 않는다.

## 3. 승강기와 함께 움직이는 테두리 배치

`ELEVATOR_LandingApron.fbx`는 **실제로 위아래로 움직이는** `EXIT_Module/ELEVATOR_Module`의 직접 자식으로 넣는다. 회전된 기존 Cabin 외형의 자식으로 넣지 않는다.

```text
EXIT_Module
└─ ELEVATOR_Module                     ← 기존 움직이는 부모
   ├─ 기존 승강기 오브젝트들
   └─ ELEVATOR_LandingApron            ← 새 바닥 가장자리
```

새 Apron의 로컬 Position `(0,0,0)`, Rotation `(0,0,0)`, Scale `(1,1,1)`로 맞춘다. `MountainEnding`에 넣으면 승강기를 따라 움직이지 않으므로 주의한다.

## 4. 재질 연결

FBX의 Materials 탭에서 같은 이름의 **외부 Material**을 Remapped Materials에 연결하고 Apply한다. FBX 내부에 들어 있는 재질을 다른 FBX의 외부 재질로 끌어다 쓰지 않는다.

- `RLYF_` 슬롯에는 현재 숲에서 사용하는 외부 재질을 재사용한다. 현재 프로젝트에는 아래처럼 `M_Forest_` 이름으로 저장되어 있다. 바위·바닥·나무껍질·나뭇잎의 기존 설정을 그대로 따른다.

| FBX의 재질 슬롯 | 연결할 기존 외부 재질 |
|---|---|
| `RLYF_DampGranite` | `M_Forest_Rock` |
| `RLYF_ForestFloor` | `M_Forest_Floor` |
| `RLYF_TroddenPath` | `M_Forest_Path` |
| `RLYF_SpruceBark` | `M_Forest_Bark` |
| `RLYF_SpruceNeedles` | `M_Forest_Needles` |
| `RLYF_ExposedWood` | `M_Forest_ExposedWood` |

이 기존 재질들은 `C:\Users\gonut\School_p2\Assets\RELAY\Art\Forest\Materials`에 있다. 기존 지형·풀 FBX는 `.meta`를 유지했으면 이전 재질 연결도 유지된다.

- 새 `RLYX_` 재질은 외부 Material로 만들고 Shader를 `Universal Render Pipeline/Lit`로 지정한다. 아래 값은 Blender 외형에 맞추기 위한 시작값이며, 실제 게임 조명 아래에서는 조금 달라 보일 수 있다.

| 재질 이름 | Base Map / 색상 | Metallic | Smoothness | Normal Map |
|---|---|---:|---:|---|
| `RLYX_AgedConcrete` | `RLYX_AgedConcrete_BaseColor.png`, 색상 흰색 | 0 | 0.13 | 같은 이름의 `_Normal.png`, 강도 0.7 |
| `RLYX_DarkSteel` | `RLYX_DarkSteel_BaseColor.png`, 색상 흰색 | 0.78 | 0.31 | 같은 이름의 `_Normal.png`, 강도 0.7 |
| `RLYX_SealRubber` | 텍스처 없음, `#171916` | 0 | 0.05 | 없음 |
| `RLYX_FadedOchre` | 텍스처 없음, `#887640` | 0.15 | 0.16 | 없음 |
| `RLYX_RockMoss` | 텍스처 없음, `#424A32` | 0 | 0.03 | 없음 |

새 `RLYX_` 재질의 Surface Type은 **Opaque**, Alpha Clipping은 끈다. BaseColor PNG는 sRGB를 켜고, Normal PNG는 Texture Type을 **Normal map**으로 바꿔 Apply한다. 나뭇잎과 기존 숲길 재질의 투명도 설정까지 일괄 변경하지 않는다.

## 5. 충돌과 기존 회색 구조물

- 기존 `ElevatorShaft`의 회색 큐브 8개는 **Renderer와 Collider를 모두 유지**한다. 이번 모델은 지상 입구와 상단을 덮는 구조다. 큐브를 통째로 끄면 아래 약 30m의 승강로까지 사라질 수 있다.
- 기존 `MountainEnding/Ground`는 **Renderer 끔, Collider 켬** 상태를 유지한다.
- 기존 승강기 바닥·벽·문 Collider와 이동 스크립트의 연결을 유지한다.
- 새 지상 발판의 충돌이 필요하면 `EXIT_Landing`의 메시가 있는 오브젝트에만 Mesh Collider를 넣고 **Convex를 끈다**. Rigidbody는 추가하지 않는다.
- `EXIT_SealTrim`, `ELEVATOR_LandingApron`, `EXIT_Headwall`에는 Collider를 자동으로 추가하지 않는다. 특히 틈 마감에는 움직이는 바닥과 가까이 맞물리는 시각용 부분이 있다.

## 6. 플레이 확인 순서

1. 아래층에서 출발해 승강기가 정상적으로 올라오는지 확인한다.
2. 올라오는 동안 바닥 테두리도 함께 움직이고, 지형이 승강기 통로를 가로막지 않는지 확인한다.
3. 도착 후 양쪽 문이 끝까지 열리고 닫히는지 확인한다.
4. 문 앞과 좌우 가장자리에서 아래를 내려다보고, 숲길로 걸어 나가 본다. 발판에서 걸리거나 떨어지는 곳이 없어야 한다.
5. 숲길에서 뒤를 돌아 산비탈과 입구가 기존 빈 배경을 가리는지 확인한다.
6. Console에 새 오류가 없는지 확인한다.

FBX 형상 검사에서는 지형 구멍, 승강기·문 레일의 이동 공간, 발판과 지형의 겹침을 확인했다. 최종적인 걷기·탑승·문 작동은 이 순서로 Unity에서 확인한다.
