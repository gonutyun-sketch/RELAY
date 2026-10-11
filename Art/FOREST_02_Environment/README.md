# RELAY — 안개 낀 산속 침엽수림

## 2026-10-10 지형 면 방향 수정

기존 `Forest_Ground`의 22,704개 면이 아래를 향하던 오류를 수정했습니다. 현재 원본 `.blend`와 `exports/FOREST_Terrain.fbx`는 수정본입니다. 기존 파일은 `fixes/TerrainFacing_20261010/before/`에 보관했습니다. 재발 방지를 위해 생성 코드에도 지형 면이 위를 향하는지 확인하는 검사를 추가했습니다.

이미 Unity에 가져왔다면 `fixes/TerrainFacing_20261010/FOREST_Terrain.fbx` 하나만 사용자가 기존 FBX 위에 덮어씁니다. 기존 `.meta`, 재질, 씬 오브젝트는 보존합니다. 위치, 크기, 재질 슬롯 이름과 면 개수는 같습니다. 실제 내보낸 FBX를 다시 가져와 바닥과 길의 모든 면이 위를 향하는지 확인했습니다. Unity 적용과 플레이 검증은 아직 수행하지 않았습니다. 먼저 바닥 표시를 복구한 후 엘리베이터 가장자리의 남는 틈 및 통과 영역을 확인하고, 지형 Collider를 연결합니다.

나무, 지형, 산길, 바위, 고사리, 풀, 쓰러진 나무와 먼 산을 함께 배치한 **숲 전체 Blender 장면**입니다. 파일을 Unity 프로젝트에 자동 적용하지 않았습니다.

## 먼저 볼 파일

- `RELAY_MountainForest.blend`: 수정 가능한 전체 장면. 나무 140그루는 공유 메시를 사용하며, 텍스처를 파일 안에 포함했습니다.
- `previews/FOREST_Player_Exit.png`: 엘리베이터 출구 쪽, 눈높이 약 1.68m에서 본 실제 Blender 렌더.
- `previews/FOREST_Path_and_Valley.png`: 길을 따라 약 8m 들어간 지점의 렌더.
- `previews/FOREST_Ground_Detail.png`: 나무 단면, 뿌리, 바위, 관목 등을 가까이서 확인하는 렌더.
- `previews/FOREST_Layout_Overview.png`: 전체 배치 확인용 시점. 구조를 보기 쉽게 안개를 끈 그림입니다.
- `exports/`: 같은 원점을 사용하는 FBX 7개.
- `RELAY_Forest_UnityFiles.zip`: FBX 7개, 필요한 PNG 11개, 이 안내서를 함께 담은 연결용 묶음입니다. 압축을 풀고 사용합니다.
- `textures/`: 이 장면에 필요한 텍스처. 이전 나무 패키지의 텍스처도 여기에 복사했습니다.
- `checks/environment_fbx_audit.json`: 실제 내보낸 FBX 검사 결과. Unity 실행 검사와는 다릅니다.

`FOREST_Draft.png`는 수정 전 작업 이미지입니다. 최종 모습은 위의 Player Exit / Path and Valley 이미지를 기준으로 봅니다.

## 모델 구성

| FBX | 포함된 부분 |
|---|---|
| FOREST_Terrain | 숲 바닥과 완만하게 휘는 산길 |
| FOREST_Rockwork | 큰 바위와 작은 돌 |
| FOREST_Undergrowth | 고사리, 풀, 잔가지, 쓰러진 나무, 그루터기, 드러난 뿌리, 관목, 낙엽, 바위 표면 이끼 |
| FOREST_Trees_Near | 가까운 고밀도 나무 2그루 |
| FOREST_Trees_Mid | 중간 거리 나무 12그루 |
| FOREST_Trees_Far | 배경용 나무 126그루 |
| FOREST_Ridges | 여러 겹의 먼 능선 |

FBX마다 배치를 이미 넣었으므로 나무 140개를 Unity에서 다시 일일이 배치할 필요가 없습니다. Blender 원본에서는 개별 나무 위치를 수정할 수 있습니다. 나무 종류는 현재 가문비나무 계열 1종이며 크기, 폭, 방향, 기울기와 군집 배치를 달리했습니다.

## 다음 작업: Unity에서 사용자가 직접 연결

1. Unity의 Play를 끄고 현재 씬을 저장합니다. 이 문서는 자동 설치 도구가 아닙니다.
2. `exports`의 FBX 7개와 `textures`의 필요한 PNG를 프로젝트 안의 원하는 아트 폴더로 복사합니다. `.blend`는 Unity 밖에 두고 원본 제작 파일로 보관합니다.
3. 기존 `MountainEnding` 아래에 빈 오브젝트 `Forest_Visual`을 만듭니다. Local Position / Rotation은 `(0,0,0)`, Scale은 `(1,1,1)`로 둡니다.
4. FBX 7개를 `Forest_Visual` 아래에 넣고, 각각 Local Position / Rotation `(0,0,0)`, Scale `(1,1,1)`인지 확인합니다. 모델 Import Scale Factor도 `1`입니다. 임의로 Y축을 180도 돌리지 않습니다.
5. 아래 표대로 URP/Lit 외부 재질을 만들고 모델의 재질 슬롯과 연결합니다. FBX 내부 재질을 다른 FBX의 외부 재질로 지정하지 않습니다.
6. 배치가 맞는지 확인한 다음에만 기존 회색 지형/산의 **Mesh Renderer**를 끕니다. 기존 엔딩 제어 오브젝트는 보존합니다.
7. 실제 플레이로 출구, 이동, 충돌, 엔딩 발동을 확인합니다. 이 패키지 제작 과정에서 Unity는 실행하거나 조작하지 않았습니다.

### 기존 엔딩에서 유지할 것

- 현재 `MountainEnding`의 World Position은 `(0,30,-10)`입니다. 이 루트는 엘리베이터 도착 위치와 연결되어 있으므로 위치·회전·크기를 그대로 둡니다.
- `EndingArea`와 엔딩 스크립트, 연결된 참조를 유지합니다.
- **기존 `Ridge_Far`는 엔딩 시선 목표입니다. 삭제하거나 Transform을 옮기지 말고 외형의 Mesh Renderer만 끕니다.** 새 산 모델이 이 Transform을 대체하지 않습니다.
- 기존 경계벽은 충돌을 담당하므로 GameObject 전체를 끄지 않습니다. 외형만 숨깁니다.
- 현재 이동 범위 안에서 중앙 길 높이는 대략 ±1.5cm입니다. 새 지형 전체에 맞는 충돌은 사용자가 연결해야 합니다.

### 바닥과 나무 충돌

새 `FOREST_Terrain` 메시 자식에 정적 Mesh Collider를 추가하고 `Convex`는 끕니다. 새 바닥에서 서고 걸을 수 있음을 확인한 뒤 기존 `Ground`의 Collider를 끕니다. 중복 바닥 Collider를 계속 켜두지 않습니다. 원래 바닥을 먼저 삭제하지 않습니다.

잎과 고사리 전체에 Mesh Collider를 붙이지 않습니다. 가까운 줄기는 별도의 단순 Capsule Collider, 필요한 큰 바위는 단순 Collider를 사용합니다. 현재 파일에는 Unity Collider 컴포넌트나 LOD Group이 들어 있지 않습니다. 플레이어 충돌 확인이 남아 있습니다.

## URP 재질 연결값

모두 Metallic `0`입니다. BaseColor는 sRGB, Normal 파일은 Texture Type `Normal map`으로 설정합니다. Normal은 OpenGL +Y 기준입니다. 아래 Smoothness 값은 시작값입니다.

| 재질 | Base Map | Normal Map | Smoothness | 추가 설정 |
|---|---|---|---:|---|
| RLYF_ForestFloor | RLYF_MossFloor_BaseColor | RLYF_Floor_Normal | 0.16 | Opaque, Repeat |
| RLYF_TroddenPath | RLYF_Path_Cutout | 없음 | 0.15 | Opaque + Alpha Clipping, Threshold 0.45, Clamp |
| RLYF_DampGranite | RLYF_Rock_BaseColor | RLYF_Rock_Normal | 0.14 | Opaque, Repeat |
| RLYF_SpruceBark | RLYF_Bark_BaseColor | RLYF_Bark_Normal | 0.12 | Opaque, Repeat |
| RLYF_SpruceNeedles | RLYF_Needles_Atlas | 없음 | 0.19 | Opaque + Alpha Clipping, Threshold 0.45, Render Face Both |
| RLYF_ExposedWood | 단색 #9D8970 | 없음 | 0.05 | Opaque |
| RLYF_DistantStone | 단색 #646E70 | 없음 | 0.04 | Opaque |
| RLYF_CutWood | RLYF_LogEnd_BaseColor | RLYF_LogEnd_Normal | 0.11 | Opaque, Clamp |

길의 Cutout 텍스처는 **길 전체 길이용 UV**를 사용합니다. Base Map Tiling은 `(1,1)`로 두고, 바닥 Normal 텍스처를 그대로 넣지 않습니다. 바닥의 반복 좌표와 다릅니다. 일반 BaseColor 버전은 제작 참고용으로 함께 보관했습니다.

고사리/풀/잔가지는 FBX의 `RLYF_Fern_*`, `RLYF_Sedge_*`, `RLYF_DryTwigs` 단색 슬롯을 사용합니다. 추가된 관목, 낙엽, 바위 이끼는 `RLYF_Bilberry_*`, `RLYF_LeafLitter_*`, `RLYF_RockMoss_*` 슬롯입니다. 필요하면 URP/Lit로 바꾸고 원래 색을 유지합니다. 고사리, 풀, 관목 잎은 Render Face `Both`를 권장합니다.

`RLYF_Bark_Roughness.png`는 Blender 원본용입니다. Unity의 Smoothness에 그대로 넣지 않습니다. 직접 변환하지 않는 단계에서는 위의 고정 Smoothness를 사용합니다.

## 현재 완성 범위와 남은 확인

- 숲 전체 배치, 3D 메시, 텍스처, 원본 `.blend`, 7개 FBX와 렌더를 제공했습니다.
- Blender의 안개, 하늘, 조명은 미리보기용입니다. **FBX를 넣는 것만으로 Unity 화면이 렌더와 같아지지는 않습니다.** Unity 안개·조명·노출은 수동 연결 후 맞춰야 합니다.
- 가까운/중간/먼 나무는 정해진 밀도로 내보냈습니다. 거리마다 자동 교체되는 LOD Group은 아직 없습니다. 바람 애니메이션도 없습니다.
- 실제 Unity 프레임 속도, 충돌과 엔딩 작동은 미확인입니다. 합쳐진 배경 나무는 개별 나무 단위 컬링이 되지 않으므로 성능을 보고 구역 분할/LOD를 조정할 수 있습니다.
- 기존 Unity 씬과 스크립트는 수정하지 않았고, 이번 파일의 GitHub 업로드는 수행하지 않았습니다.

전체 연결은 위 순서대로 한 번에 배치한 다음, 재질 → 충돌 → 조명/안개 → 실제 엔딩 플레이 확인 순서로 진행합니다.

## 이번 모델 검증

최종 FBX 7개를 직접 파싱한 검사에서 모두 통과했습니다. 정확한 전체/부분별 삼각형 수는 `manifest.json`과 `checks/environment_fbx_audit.json`에 기록합니다. 좌표/면의 유효성, 퇴화된 면, UV, 법선, 재질 연결, 미터 단위와 원점을 확인했습니다. 면 개수는 전체 숲의 정적 메시 합계이며 Unity에서의 프레임 속도 측정값이 아닙니다. 입체 이끼는 가까운 바위 6개에 집중하고 먼 바위에는 텍스처를 사용합니다.

Blender 원본은 텍스처가 포함되어 단독으로 열 수 있습니다. 제작 스크립트를 처음부터 재실행하려면 형제 폴더인 `FOREST_01_HeroTree`도 필요합니다. GitHub에 보관할 때는 원본/모델/텍스처를 보관하고 편의용 ZIP은 중복으로 올리지 않는 편이 좋습니다.
