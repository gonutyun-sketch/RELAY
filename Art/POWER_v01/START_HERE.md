# RELAY — POWER 모델 v01

Unity 프로젝트 밖에서 제작한 첫 POWER 모델 세트입니다. Unity 씬/스크립트/Inspector는 수정하지 않았습니다.

## 파일

- `RELAY_POWER_v01.blend`: 편집 가능한 조립 모델과 미리보기 조명/카메라.
- `exports/`: 기존 회전축에 부착할 고정부/가동부 FBX 11개.
- `textures/`: 공유 Base Color 텍스처. FBX와 함께 보관하세요.
- `previews/`: 렌더링 미리보기.
- `manifest.json`: 부품별 삼각형 수, 기존 부모 기준 위치.

`PREVIEW_ONLY` 컬렉션의 바닥/조명/카메라는 모델용 미리보기이며 게임에 가져올 부품이 아닙니다.

## 보조 퍼즐 정리 — 사용자가 Unity에서 직접 수행

1. Play를 종료합니다.
2. Hierarchy의 `Environment/ARCHIVE_Module` 전체를 삭제합니다. 배선도, 텍스트, 슬라이더, 검사 버튼, 보조 조명이 이 루트 아래에 있습니다.
3. Project 창에서 `ArchiveCircuit.cs`, `ArchiveBridge.cs`를 삭제합니다. Unity에서 삭제하면 관련 .meta도 함께 정리됩니다.
4. 기존 `MachineSlider`, `Interactable`, `PlayerInteractor`는 유지합니다. 다른 기계가 사용합니다.
5. 한글 폰트는 다른 텍스트가 참조할 수 있으므로 함께 일괄 삭제하지 않습니다.
6. 씬을 저장하고 Console 오류가 없는지 확인합니다.

## 모델 설계 기준

캐비닛은 기존 1.8 × 2.4 × 1m 블록에 맞췄습니다. 단위는 미터입니다.

| 부품 | 기존 Unity 부모 | 새 모델의 로컬 위치 |
|---|---|---|
| POWER_Cabinet | POWER_Module | 0, 0, 0 |
| AUX_Housing | AUX_Switch | 0, 0, 0 |
| AUX_Handle | AUX_Switch/HandlePivot | 0, 0, 0 |
| MAIN_Housing | MAIN_Lever | 0, 0, 0 |
| MAIN_Handle | MAIN_Lever/HandlePivot | 0, 0, 0 |
| VOLTAGE_Housing | VOLTAGE_Dial | 0, 0, 0 |
| VOLTAGE_Knob | VOLTAGE_Dial/PointerPivot | 0, 0, 0 |
| BALANCE_Housing | BALANCE_Dial | 0, 0, 0 |
| BALANCE_Knob | BALANCE_Dial/PointerPivot | 0, 0, 0 |
| Gauge_Housing | VOLTAGE_Gauge | 0, 0, 0 |
| Gauge_Needle | VOLTAGE_Gauge/NeedlePivot | 0, 0, 0 |

가동부는 중립 자세로 내보냈습니다. 기존 스크립트가 기존 Pivot을 회전시킵니다. Blender 조립 미리보기에는 현재 게임의 초기 각도를 적용했습니다.

## Unity에서 가져올 때

아직 Unity 가져오기/실행 검증은 하지 않았습니다. 사용자가 먼저 AUX 한 개로 방향과 크기를 확인한 뒤 나머지를 적용합니다.

1. `exports`와 `textures`를 프로젝트의 새 모델 폴더로 복사합니다. `.blend`는 작업 원본으로 이 폴더에 두고 FBX를 가져오는 방식을 권장합니다.
2. FBX Model 탭: Scale Factor 1, Convert Units 켜기, Bake Axis Conversion 켜기, Import Cameras/Lights 끄기. Normals는 Import.
3. AUX_Housing을 기존 AUX_Switch 아래에 넣고 위치/회전 0, Scale 1로 시작합니다.
4. AUX_Handle을 기존 HandlePivot 아래에 넣고 위치/회전 0, Scale 1로 시작합니다.
5. 글씨가 방 안쪽을 향하고, 고정부 뒤가 패널에 닿으며, 회전 중심이 일치하는지 확인합니다. 방향이 다르면 기존 게임 로직의 Pivot을 돌리지 말고 새 Visual 자식에서만 교정합니다. 임의로 가로/세로 크기를 늘리지 않습니다.
6. 겹쳐 있는 기존 회색 Mesh Renderer만 끕니다. Collider와 스크립트, Pivot 오브젝트는 남깁니다. 이름표는 새 모델과 겹치는 것만 숨깁니다.
7. AUX 최초 클릭/켜기/끄기가 정상인지 확인한 뒤 나머지를 적용합니다.

크기가 바뀐 기존 Cube(Body/Panel)의 자식으로 새 모델을 넣으면 모델 크기가 뒤틀립니다. 반드시 표에 적힌 단위 Scale의 부모 아래에 넣습니다.

전압계 아래 검은 창은 기존 동적 Readout 텍스트용 자리입니다. 바늘은 실제 전압을 따라 기존 스크립트가 회전시킵니다. Readout은 삭제하지 않고 새 창과 앞뒤 위치/크기를 맞춥니다.

## 재질

렌더는 Blender Cycles 기준이며 Unity 조명/URP에서 동일한 화면이 자동 보장되는 것은 아닙니다.
Unity에서 각 재질을 URP/Lit로 지정하고 같은 이름의 BaseColor PNG를 Base Map에 연결합니다.

| 재질 | Metallic | Smoothness |
|---|---:|---:|
| PaintedSteel | 0.60 | 0.57 |
| ExposedSteel | 0.82 | 0.64 |
| BlackMetal | 0.70 | 0.58 |
| Bakelite | 0 | 0.45 |
| OxideRed | 0.25 | 0.55 |
| AgedBrass | 0.70 | 0.58 |
| MeterEnamel | 0.10 | 0.43 |
| SafetyOchre | 0.15 | 0.50 |

텍스트, 눈금, 볼트 홈은 모델에 포함했습니다. 공유 텍스처는 미세한 표면 흔적용이며 베벨과 부품 형상은 실제 메시입니다.

## 아직 남은 것

- 사용자 Unity 가져오기/회전 방향/시야 가독성 확인.
- Unity 조명에 맞춘 최종 재질 조정.
- 필요하면 메시/재질 수 최적화 및 LOD.
- COOLING, SIGNAL, CORE, 광산 엘리베이터, 연구실 구조물과 야외 에셋은 별도 제작 단계입니다.

## 참고

Unity 축 변환 설정: https://docs.unity3d.com/6000.0/Documentation/Manual/FBXImporter-Model.html
