# RELAY — COOLING 앞·옆면 보호 커버 추가

기존 COOLING을 덮어쓰지 않고 네 부품을 추가합니다. Unity 작업은 사용자가 직접 합니다. 기존 계기판, 바늘, 스위치, 밸브, 스크립트와 Collider는 그대로 유지합니다.

## 1. 새 파일 가져오기

Play를 중지하고 씬을 저장합니다. 이 패키지의 `exports`에 있는 아래 FBX 네 개를 기존 `Assets/_STARTUP/Art/COOLING/Models`로 드래그합니다.

| 파일 | 역할 |
|---|---|
| COOLING_CoverFrame.fbx | 전면·측면 커버 고정 프레임, 고무 패킹, 볼트 |
| COOLING_FrontGlass.fbx | 계기판·스위치·밸브·온도 표시기 구멍이 있는 앞면 유리 |
| COOLING_LeftGlass.fbx | 왼쪽 유리 |
| COOLING_RightGlass.fbx | 오른쪽 유리 |

각 FBX의 Model 탭에서 **Generate Colliders를 끕니다**. 새 유리에 Collider를 추가하면 기존 조작부를 향한 클릭이 막힐 수 있습니다. `.blend` 원본을 Unity에 넣지 않습니다.

## 2. 기존 COOLING_Module 아래에 붙이기

네 모델을 모두 Hierarchy의 `Environment/COOLING_Module` 바로 아래에 넣습니다. 기존 `COOLING_Frame` FBX 내부가 아닙니다.

```text
Environment
└─ COOLING_Module
   ├─ COOLING_Frame            기존 모델 유지
   ├─ 기존 조작부와 계기판      기존 연결 유지
   ├─ COOLING_CoverFrame        추가
   ├─ COOLING_FrontGlass        추가
   ├─ COOLING_LeftGlass         추가
   └─ COOLING_RightGlass        추가
```

새 모델 네 개 모두 다음 **로컬** Transform을 설정합니다.

| 항목 | X | Y | Z |
|---|---:|---:|---:|
| Position | 0 | 0 | 0 |
| Rotation | 0 | 180 | 0 |
| Scale | 1 | 1 | 1 |

기존 본체나 조작부는 숨기거나 이동하지 않습니다. 기존 `FLOW_Glass`의 로컬 Position Z **0.01**도 그대로 유지합니다. 새 앞면 유리에는 유량계 전체가 통과하는 구멍이 있어 계기판 유리를 두 겹으로 덮지 않습니다.

## 3. 기존 불투명 재질 연결

Project에서 `COOLING_CoverFrame.fbx`를 선택합니다. Materials 탭의 Remapped Materials에 기존 COOLING/Materials의 같은 이름 `.mat`를 연결하고 Apply합니다.

- RLYC_FramePaint
- RLYC_Rubber
- RLYC_Steel
- RLYC_PrintDark

FBX 내부의 내장 재질 대신 기존 독립 `.mat` 파일을 사용합니다. Inspector 자물쇠를 잠그면 폴더를 바꿔 재질을 드래그하기 편합니다. 연결 후 자물쇠를 풉니다.

## 4. 새 유리 재질 하나 만들기

기존 COOLING/Materials 안에 **새 Material**을 만들어 이름을 `RLYC_CoverGlass`로 설정합니다. 계기판용 `RLYC_MeterGlass`를 수정하지 않습니다.

| 항목 | 값 |
|---|---|
| Shader | Universal Render Pipeline/Lit |
| Workflow Mode | Metallic |
| Surface Type | Transparent |
| Blending Mode | Alpha |
| Preserve Specular Lighting | 켜기 |
| Render Face | Front |
| Base Map 색상 | HEX DCEAE6 |
| Alpha | 약 0.14, 0~255 표시라면 36 |
| Metallic | 0 |
| Smoothness | 0.91 |
| Alpha Clipping | 끄기 |
| Receive Shadows | 끄기 |
| Emission | 끄기 |

8자리 HEX로 입력하는 경우 `DCEAE624`입니다. 유리의 반사를 유지하기 위해 Preserve Specular Lighting을 켭니다. 표준 URP Lit를 사용하며 새 커스텀 셰이더는 필요하지 않습니다.

Project에서 `COOLING_FrontGlass`, `COOLING_LeftGlass`, `COOLING_RightGlass` FBX를 하나씩 선택합니다. Materials 탭의 **RLYC_CoverGlass 슬롯**에 방금 만든 같은 `.mat`를 연결하고 각각 Apply합니다.

Hierarchy에서 새 유리 모델 세 개의 실제 Mesh Renderer를 선택해 **Cast Shadows를 Off**로 설정합니다. FBX 루트에 Renderer가 없으면 펼쳐서 Mesh Renderer가 있는 자식을 선택합니다. 고정 프레임의 그림자는 유지합니다.

## 5. Game 화면 확인

1. 앞·옆면이 닫혀 보이면서 펌프와 배관이 유리 안으로 보이는지 봅니다.
2. FLOW 바늘과 숫자, 온도·압력 숫자가 이전처럼 읽히는지 확인합니다.
3. PUMP 스위치와 FLOW 밸브를 실제로 조작합니다. 동작과 클릭 위치가 이전과 같아야 합니다.
4. 정면과 비스듬한 각도에서 유리와 프레임이 깜빡이거나 겹쳐 보이지 않는지 확인합니다.
5. Console에 새 오류가 없는지 확인합니다. Play를 끝낸 뒤 저장합니다.

내부가 너무 흐리면 **RLYC_CoverGlass만** Alpha를 0.10(약 26/255)으로 낮춰 봅니다. 반사광이 지나치게 날카로우면 Smoothness를 0.85로 낮춥니다. 첫 적용에서는 위 기본값부터 확인합니다. 유리가 거의 안 보이면 먼저 Surface Type·재질 연결·Preserve Specular Lighting을 확인합니다.

## 검증 범위

`checks/validation.json`은 실제 FBX 재가져오기, 유리 구멍, 기존 기계와 유리의 겹침, 스위치·밸브의 회전 범위를 검사한 결과입니다. 원본 COOLING Blender 파일은 덮어쓰지 않습니다. 미리보기는 실제 모델을 Blender에서 렌더한 것으로 Unity의 실시간 게임 화면은 아닙니다. Unity에서의 투명도·반사·최종 클릭 동작은 위 과정으로 확인합니다.
