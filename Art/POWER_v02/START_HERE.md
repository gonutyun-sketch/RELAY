# RELAY — POWER v02

POWER 패널 외형을 다시 만든 버전입니다. Unity 프로젝트에는 적용하지 않았습니다.
기존 v01도 그대로 남아 있습니다.

## 먼저 볼 파일

- `previews/POWER_v02_hero.png`: 전체 외형
- `previews/POWER_v02_front.png`: 정면 배치
- `previews/POWER_v02_operated.png`: 레버를 내린 상태
- `RELAY_POWER_v02.blend`: 편집 가능한 Blender 원본

전면은 고정 계기판, 오른쪽은 정비용 덮개입니다. 판금 외함·도장판·검은 수지 손잡이·붉은 레버 그립의 재질을 구분했습니다. 환기구는 실제로 뚫려 있고, 안쪽에는 어두운 가림판이 있습니다. 부품 전체에 은색 테두리나 같은 잡음을 반복해서 넣지 않았습니다.

## Blender 원본 구성

- `01_EDITABLE_PARTS`: 실제 모델. 개별 부품과 모서리 수정자를 유지합니다. 글자는 폰트 파일 없이 열 수 있도록 메시로 변환했습니다.
- `02_EXPORT_MESHES`: FBX용으로 합쳐 놓은 메시. 중복해서 보이지 않도록 숨겨져 있습니다.
- `03_PREVIEW_ONLY`: 미리보기 카메라, 조명, 바닥. 게임에 가져갈 부품이 아닙니다.

1 Blender 단위 = 1m입니다. 각 FBX는 조립 위치가 아니라 해당 부품의 회전축을 원점으로 내보냈습니다. 기존 스크립트가 사용하는 축과 각도를 유지했습니다.

## Unity에 직접 적용할 때의 연결 위치

한 번에 모두 바꾸기 전에 AUX 하나로 크기와 방향을 확인하세요. AI는 Unity를 조작하거나 파일을 수정하지 않았으며, 실제 Unity 가져오기와 플레이 검증은 아직 하지 않았습니다.

| FBX 파일 | 기존 부모 오브젝트 | 새 메시의 Local Position / Rotation / Scale |
|---|---|---|
| POWER_Cabinet | POWER_Module | 0,0,0 / 0,0,0 / 1,1,1 |
| AUX_Housing | AUX_Switch | 0,0,0 / 0,0,0 / 1,1,1 |
| AUX_Handle | AUX_Switch/HandlePivot | 0,0,0 / 0,0,0 / 1,1,1 |
| MAIN_Housing | MAIN_Lever | 0,0,0 / 0,0,0 / 1,1,1 |
| MAIN_Handle | MAIN_Lever/HandlePivot | 0,0,0 / 0,0,0 / 1,1,1 |
| VOLTAGE_Housing | VOLTAGE_Dial | 0,0,0 / 0,0,0 / 1,1,1 |
| VOLTAGE_Knob | VOLTAGE_Dial/PointerPivot | 0,0,0 / 0,0,0 / 1,1,1 |
| BALANCE_Housing | BALANCE_Dial | 0,0,0 / 0,0,0 / 1,1,1 |
| BALANCE_Knob | BALANCE_Dial/PointerPivot | 0,0,0 / 0,0,0 / 1,1,1 |
| Gauge_Housing | VOLTAGE_Gauge | 0,0,0 / 0,0,0 / 1,1,1 |
| Gauge_Needle | VOLTAGE_Gauge/NeedlePivot | 0,0,0 / 0,0,0 / 1,1,1 |
| Gauge_Glass (선택) | VOLTAGE_Gauge | 0,0,0 / 0,0,0 / 1,1,1 |

기존 Body처럼 Scale이 변형된 Cube 아래에 넣으면 새 모델도 찌그러집니다. 표에 적힌 기능 루트나 Pivot 바로 아래에 넣으세요. 기존 Mesh Renderer만 꺼서 비교하고, 스크립트·Collider·Pivot·Readout은 유지하세요. 실제 프로젝트의 이름이 다르면 먼저 연결 대상을 확인하세요.

## 재질

Blender 미리보기와 URP는 재질을 그대로 공유하지 않습니다. Unity에서는 URP/Lit 재질을 직접 연결해야 합니다. FBX와 함께 `textures` 폴더도 가져오세요.

전면 판 재질 `RLY02_FasciaPaint`:

1. `POWER_Fascia_BaseColor.png`를 Base Map에 연결합니다. sRGB를 켜고 Tint는 흰색으로 둡니다.
2. `POWER_Fascia_MetallicSmoothness.png`는 sRGB를 끕니다. R에 Metallic, A에 Smoothness가 들어 있습니다.
3. 이 파일을 Metallic Map에 연결하고 Smoothness Source를 Metallic Alpha로, Smoothness 배율을 1로 설정합니다.

나머지 주요 재질은 텍스처 없이 색상과 표면 값으로 구성됩니다. Blender 원본에도 값이 저장되어 있습니다.

| 재질 | sRGB 색상 | Metallic | Smoothness |
|---|---|---:|---:|
| ShellPaint | #59665F | 0 | 0.43 |
| CastIron | #343B36 | 0.25 | 0.35 |
| Steel | #77796E | 0.85 | 0.60 |
| OxidizedSteel | #3D403B | 0.65 | 0.42 |
| BlackPolymer | #252821 | 0 | 0.63 |
| Gasket | #141813 | 0 | 0.21 |
| RedGrip | #76372B | 0 | 0.57 |
| DialEnamel | #D2CBAB | 0 | 0.30 |
| Ink | #262A22 | 0 | 0.25 |
| IvoryInk | #D5D1B8 | 0 | 0.42 |
| InspectionPaper | #C1B98A | 0 | 0.12 |
| BrassContact | #776E49 | 0.75 | 0.50 |

`Gauge_Glass`는 선택 부품입니다. Blender의 유리 투과 값이 FBX를 통해 URP 유리로 자동 변환되지는 않습니다. 처음에는 렌더러를 꺼 두세요. 나중에 URP/Lit에서 Surface Type=Transparent, Blending=Alpha, Base Color=#F0F1E9, Alpha 약 0.06, Metallic=0, Smoothness 약 0.9로 시작해 계기 가독성을 확인한 후 켜세요. 이는 얇은 투명판 표현이며 Blender와 같은 굴절 효과는 아닙니다. 기존 Readout 글자가 유리에 가려지지 않는지도 확인해야 합니다.

## 검증 범위

`validation.json`에는 FBX 재가져오기 후 크기·원점 비교와 UV 유무, 삼각형 수, MAIN 전체 회전 구간의 바닥·전면 판 간격이 기록됩니다. Blender 내 기하 검증입니다. Unity 런타임, 실제 게임 조명과 충돌 검증을 대신하지 않습니다.

`build_power.py`는 재생성용 제작 파일입니다. Unity 프로젝트에서 실행하는 코드가 아닙니다.
