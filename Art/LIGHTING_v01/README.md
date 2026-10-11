# RELAY — 조명 모델 v01

2026-10-08 외장 FBX 재질 할당을 수정했다. 초기 출력은 재질 슬롯 이름 네 개가 있었지만 모든 면이 첫 슬롯에 할당되어 있었다. 현재 `exports`의 Housing 두 파일은 네 재질을 실제 부위에 나누어 사용한다. 검사 결과는 `checks/material_fix_validation.json`에 있으며, 초기 검사보다 우선한다. Unity 프로젝트의 기존 FBX에는 자동으로 반영하지 않았다. 사용자가 기존 `LIGHT_LinearHousing.fbx`, `LIGHT_BulkheadHousing.fbx` 두 파일만 같은 경로에 덮어쓰고 기존 `.meta`를 보존한 뒤 재질을 연결한다. Lens/Glass 교체는 필요 없다.

실험실과 광산 엘리베이터에 사용할 두 종류의 천장 조명이다. 2026-10-06 저장된 Unity 씬을 읽어 기존 네 조명의 설치 높이와 전원 연결에 맞췄다. 제작물은 Unity 프로젝트 밖에 있으며 Unity 파일은 수정하지 않았다.

| 모델 | 용도 | 실제 전체 크기, 폭 × 깊이 × 길이 |
|---|---|---|
| Linear | 실험실의 WorkLeft, WorkRight, Exit | 약 0.556 × 0.175 × 1.703 m |
| Bulkhead | 광산 엘리베이터 Cabin | 약 0.422 × 0.168 × 0.791 m |

Linear는 도장한 금속 몸체, 여섯 개의 고정 클립, 고무 패킹, 유백색 확산판, 보호 유리, 케이블 인입부로 구성했다. Bulkhead는 둥근 주물 외장과 유리 보호망을 사용해 다른 실루엣을 갖는다. 볼트와 브래킷은 조립되는 위치에 배치했다.

## 파일

- `RELAY_Lighting.blend`: 부품별로 편집할 수 있는 모델 원본. `01_SOURCE_Edit_parts_here`에 부품이 있고, `02_EXPORT_MESHES`에는 숨겨진 출력용 메시가 있다.
- `RELAY_Lighting_Review.blend`: 조명, 카메라, 단순한 천장 배경을 포함한 감상용 파일. 모델 원본과 구분된다. F12로 전체 모습을 렌더할 수 있다.
- `exports/`: Unity에 직접 가져올 FBX 여섯 개. 각 모델을 Housing / Lens / Glass로 분리했다.
- `previews/`: 실제 Blender 모델에서 렌더한 전체 이미지, 각 모델 확대 이미지, 점등 표현 참고 이미지.
- `UNITY_HANDOFF.md`: 기존 씬에서 사용자가 직접 교체할 순서, 재질 값, 전원 연결, 조정 권장 위치.
- `checks/validation.json`: 실제 FBX 재가져오기와 파일 검사 결과.
- `checks/scene_reference.json`: 모델 크기를 정할 때 읽은 저장된 씬의 조명 위치와 참조.
- `manifest.json`: 부품별 실제 크기, 삼각형 수, 재질 슬롯.

두 모델의 삼각형 수 합계는 47,524개다. FBX에는 카메라나 실제 Light 컴포넌트가 들어 있지 않으며 외부 텍스처 파일에 의존하지 않는다. 고정용 금속 부품, 발광판, 유리는 각각 UV가 있는 별도 메시로 출력된다.

## 기존 전원과의 연결

축과 단위는 Unity 기준 미터, X=폭, Y=높이, Z=길이다. 피벗은 천장에 닿는 면이며 발광면은 아래(-Y)를 향한다. 기존 Fixture 아래에 세 FBX를 넣을 때 각각 로컬 Position `(0, 0.05, 0)`, Rotation `(0, 0, 0)`, Scale `(1, 1, 1)`을 사용한다.

Lens는 한 개의 메시와 한 개의 재질 슬롯으로 구성했다. 기존 `M_LightFace`를 연결하고 기존 `CorePowerVisual`의 Lens 참조만 새 렌더러로 바꾸면 현재 전원 제어 방식에 연결할 수 있다. 실제 Light는 기존 것을 유지한다. 자세한 조작은 `UNITY_HANDOFF.md`에 있다.

Blender의 점등 참고 이미지는 Blender 조명 환경에서 만든 모습이다. Unity에 자동 설치되거나 작동 확인된 화면이 아니며, Unity에서는 재질을 연결하고 사용자가 Play에서 전원·엘리베이터 이동을 확인해야 한다. FBX 재질만으로 유리 투명도나 발광 표현이 그대로 옮겨진다고 가정하지 않는다.

## 재생성

`build_lighting.py`는 별도 Blender 백그라운드 프로세스에서 이 폴더의 `.blend`, FBX와 manifest를 생성한다. `render_previews.py`는 원본을 읽어 미리보기와 Review 파일만 만든다. `validate_lighting.py`는 내보낸 파일을 다시 읽고 검사한다. 세 파일 모두 Unity를 실행하거나 Unity 프로젝트에 쓰는 작업을 하지 않는다.
