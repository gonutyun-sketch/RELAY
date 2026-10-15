# RELAY 출구 터미널 모델 — 수동 연결

이 패키지는 작은 CRT 모니터, 키보드, 금속 받침대로 이루어진 출구 제어 단말기다. 모델 제작은 Unity 프로젝트 밖에서 진행했다. 아래 단계는 사용자가 Unity에서 직접 적용한다.

현재 저장된 씬에는 `Environment > EXIT_Module > EXIT_Terminal`이 있고, Local Position은 `(2.1, 0, 0.55)`, Rotation은 `(0,0,0)`, Scale은 `(1,1,1)`이다. 이 루트와 ExitTerminal 컴포넌트를 유지한다.

## 1. 파일 가져오기

Play를 정지하고 현재 씬을 저장한다.

Project의 `Assets/RELAY/Art` 밑에 `ExitTerminal`을 만들고 그 안에 `Models`, `Textures`, `Materials` 폴더를 만든다.

- 패키지의 `textures` 안 PNG 3개 → Unity의 `Textures`.
- 패키지의 `exports` 안 FBX 4개 → Unity의 `Models`.
- `.blend`는 편집용 원본이다. Unity에는 FBX를 사용한다.

FBX의 Model 탭은 Scale Factor 1, Convert Units ON, Bake Axis Conversion OFF, Generate Colliders OFF로 둔다. 실제 모델 단위는 m이고 높이는 약 1.55m, 받침대 폭은 0.82m다.

## 2. 텍스처 설정

| 텍스처 | Texture Type | sRGB | Alpha Source | Max Size |
|---|---|---|---|---|
| TERMINAL_BaseColor | Default | ON | Input Texture Alpha | 2048 |
| TERMINAL_MetallicSmoothness | Default | OFF | Input Texture Alpha | 2048 |
| TERMINAL_Roughness | Default | OFF | Input Texture Alpha | 2048 |

세 텍스처의 **Alpha Is Transparency는 OFF**로 둔다. Filter Mode는 Bilinear, Mip Maps는 ON이다. 값을 바꿨다면 Apply한다.

Unity URP 연결에는 BaseColor와 MetallicSmoothness 두 장을 사용한다. Roughness는 Blender 원본과 다른 도구에서 사용할 수 있도록 함께 제공한 파일이며, URP Normal Map 칸에 넣지 않는다.

MetallicSmoothness는 **R 채널에 금속성, A 채널에 매끄러움**이 들어 있다. sRGB를 끄고 알파를 유지해야 표면이 정상적으로 나온다.

## 3. 외부 Material 4개 만들기

Unity의 `Materials` 폴더에서 Create → Material로 아래 4개를 직접 만든다. 모두 Shader는 **Universal Render Pipeline/Lit**, Surface Type은 Opaque, Alpha Clipping은 OFF다.

| Material 이름 | Base Map / Base Color | Metallic | Smoothness |
|---|---|---:|---:|
| RLYT_Surface | TERMINAL_BaseColor / 흰색 FFFFFF | 아래 설명의 텍스처 | 1 |
| RLYT_Ink | 텍스처 없음 / 242D28 | 0 | 0.20 |
| RLYT_Legend | 텍스처 없음 / D5D2BD | 0 | 0.21 |
| RLYT_CRTScreen | 텍스처 없음 / 08140F | 0 | 0.84 |

RLYT_Surface에서:

1. Workflow Mode가 Metallic인지 확인한다.
2. Base Map에 `TERMINAL_BaseColor`를 넣고 옆 색은 흰색, Alpha 255로 둔다.
3. Metallic Map에 `TERMINAL_MetallicSmoothness`를 넣는다.
4. Smoothness의 Source 선택이 보이면 **Metallic Alpha**로 둔다. Smoothness 값은 **1**이다. 실제 부위별 거칠기는 텍스처 알파가 결정한다.
5. Tiling `(1,1)`, Offset `(0,0)`.
6. Emission OFF. 별도 Normal Map은 없다.

RLYT_CRTScreen은 검은 곡면 CRT 표면이다. 투명한 보호판을 위에 겹치는 구조가 아니므로 **Opaque를 유지한다**. 화면 문자는 기존 WorldStatus / TerminalScreen UI가 표시한다.

FBX 원본 선택 → Materials 탭의 Remapped Materials에서 각 이름에 방금 만든 **외부 Material**을 연결하고 Apply한다.

| FBX | 연결할 재질 |
|---|---|
| TERMINAL_Body | RLYT_Surface / RLYT_Ink / RLYT_Legend |
| TERMINAL_Keys | RLYT_Surface / RLYT_Legend / RLYT_Ink |
| TERMINAL_EnterKey | RLYT_Surface / RLYT_Ink |
| TERMINAL_Screen | RLYT_CRTScreen |

FBX를 펼쳐서 나오는 내장 Material을 다른 FBX의 외부 Material 칸에 넣지 않는다. 위에서 직접 만든 `.mat` 파일을 사용해야 예전의 `sub-asset ... cannot be used as an external material` 오류를 피할 수 있다.

## 4. 기존 EXIT_Terminal 아래에 모델 배치

네 FBX 모두 `Environment > EXIT_Module > EXIT_Terminal`의 **직접 자식**으로 넣는다. 작은 Cube인 MonitorBody나 Keyboard의 자식으로 넣으면 부모 Scale 때문에 작아진다.

| 새 모델 | Local Position X,Y,Z | Local Rotation X,Y,Z | Local Scale X,Y,Z |
|---|---|---|---|
| TERMINAL_Body | 0, 0, 0 | 0, 180, 0 | 1, 1, 1 |
| TERMINAL_Keys | 0, 0, 0 | 0, 180, 0 | 1, 1, 1 |
| TERMINAL_Screen | 0, 0, 0 | 0, 180, 0 | 1, 1, 1 |
| TERMINAL_EnterKey | -0.1072, 0.939, 0.363 | 0, 180, 0 | 1, 1, 1 |

Enter 키만 Position이 다르다. 키 중앙을 원점으로 분리했기 때문에 이 값을 사용한다. 0,0,0으로 넣으면 바닥에 생긴다. 나중에 누름 애니메이션을 추가할 때는 이 키의 Local Y를 약 0.003~0.004 낮췄다가 되돌리면 된다. 이번 모델 패키지에 키 누름 기능은 포함하지 않았다.

기존 임시 Cube 6개에서 **Mesh Renderer 체크만 OFF**로 한다.

```text
Stand
Neck
MonitorBody
ScreenFace
KeyboardTray
Keyboard
```

오브젝트 전체 Active 체크와 Box Collider는 유지한다. 기존 Collider가 조준과 플레이어 충돌을 담당한다. 새 FBX에 Rigidbody를 추가하지 않는다.

새 키보드는 모니터 아래에서 손이 들어갈 공간을 확보하도록 조금 앞으로 나와 있다. 숨겨 둔 기존 충돌용 Cube 두 개의 Transform만 아래처럼 맞춘다.

| 기존 Cube | Local Position | Local Scale |
|---|---|---|
| KeyboardTray | 0, 0.847, 0.195 | 0.82, 0.07, 0.73 |
| Keyboard | 0, 0.90, 0.39 | 0.80, 0.08, 0.30 |

두 Cube 모두 Rotation은 `(0,0,0)`이고 Mesh Renderer OFF다. 다른 부모나 방의 크기는 바꾸지 않는다.

## 5. 화면 위치

기존 `EXIT_Terminal > StatusCanvas`는 아래 값과 연결한다.

| 항목 | 값 |
|---|---|
| Render Mode | World Space |
| Width / Height | 640 / 320 |
| Local Position | 0, 1.25, 0.245 |
| Local Rotation | 0, 180, 0 |
| Local Scale | 0.001, 0.001, 0.001 |

StatusCanvas 밑의 WorldStatus 텍스트와 ExitTerminal의 World Status 참조는 앞서 제공한 기능 안내대로 연결한다. 현재 모델의 유리 가장 앞쪽은 Local Z 약 0.2335이고 글자는 Z 0.245에 놓이므로 표면에 묻히지 않는다.

모델 미리보기의 수열 문자는 Blender의 별도 검토용 오브젝트다. FBX에는 들어 있지 않다. 게임에서는 실제 터미널 UI가 부팅과 입력을 처리한다. 기능 연결이 아직 진행 중이라면 먼저 아래 기존 안내의 UI·Inspector 연결을 마친다.

`C:\Users\gonut\RELAY_Art\EXIT_TERMINAL_v01\적용안내.md`

## 6. 짧게 확인

- 바닥에 받침대가 닿고 모델이 실험실 쪽을 바라본다.
- 키보드와 황갈색 Enter 키가 같은 높이에 놓인다.
- 본체가 흰 단색이면 RLYT_Surface의 Base Map과 FBX Material Remap을 확인한다.
- 얼굴 전체가 보라색이면 Material Shader가 URP/Lit인지 확인한다.
- 기존 Cube가 모델 앞을 가리면 Cube의 Mesh Renderer만 껐는지 확인한다.
- 모니터가 반대로 보이면 새 FBX의 Rotation Y 180과 부모 EXIT_Terminal의 Rotation 0을 확인한다.
- 코어 완료 전 물리적 모니터 문자가 꺼져 있고, 완료 후에는 기존 터미널 기능으로 조준/입력/승인이 된다.

## 패키지 구성과 검증 범위

- RELAY_ExitTerminal.blend: 수정 가능한 원본. 텍스처를 파일 내부에도 포함했다.
- exports: 게임용 FBX 4개. 조명·카메라·검토용 수열 문자는 제외했다.
- textures: 2048×2048 PNG 3개.
- previews: Blender에서 실제 모델을 렌더링한 전체/상세 이미지.
- manifest.json: 부품 원점, 위치, 재질 이름, 폴리곤 수 기록.
- checks/validation.json: FBX 재수입, 축/크기, UV, 텍스처 채널, 화면 가림, 키보드 공간 검사 결과.

Unity 씬을 자동으로 수정하거나 직접 실행한 검증은 하지 않았다. 실제 게임 화면의 재질·충돌·입력은 위 수동 연결 후 확인한다.
