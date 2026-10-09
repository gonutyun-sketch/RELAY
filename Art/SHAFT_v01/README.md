# RELAY mine shaft v01

실험실 아래에서 엘리베이터가 올라갈 때 철망 밖으로 암반, 흙층, 지지대와 케이블이 보이도록 만든 Blender 아트 패키지다. 이 폴더는 `C:\Users\gonut\School_p2` Unity 프로젝트와 분리되어 있으며, 모델 제작 과정에서 Unity 씬·스크립트·프로젝트 설정을 변경하지 않았다.

## 포함 파일

- `RELAY_MineShaft.blend`: 편집 가능한 원본. 이미지 텍스처가 패킹되어 있다.
- `RELAY_MineShaft_Review.blend`: 엘리베이터 케이지를 붙인 검토용 장면.
- `exports/SHAFT_RockShell.fbx`: 암반과 흙층.
- `exports/SHAFT_Steelwork.fbx`: 고정 철제 프레임, 층별 보강대와 레일.
- `exports/SHAFT_Details.fbx`: 케이블, 뿌리, 볼트, 브래킷, 바닥 자갈.
- `textures/`: Rock/Earth BaseColor와 OpenGL +Y Normal Map.
- `previews/`: 케이지 시점, 흙층 시점, 컷어웨이 검토 이미지.
- `checks/`: FBX 구조·축·UV·내벽 방향 독립 검사 보고서.

## Unity 수동 연결

Unity에서만 다음 작업을 한다. 모델을 `Assets/RELAY/Art/Shaft/Models`, 텍스처를 `Assets/RELAY/Art/Shaft/Textures`처럼 별도 폴더에 복사한다. `.blend`는 Unity의 `Assets` 안에 넣지 않는다.

1. 세 FBX를 선택하고 Import Scale을 `1`로 둔다. Generate Colliders는 끈다. 각 FBX의 Root Transform은 Position `0,0,0`, Rotation `0,0,0`, Scale `1,1,1`이어야 한다. Bake Axis Conversion은 기본값을 유지한다.
2. `RLYS_Rock`, `RLYS_Earth`, `RLYS_Steel`, `RLYS_Oxide`, `RLYS_Cable` 이름으로 URP/Lit 외부 머티리얼을 만든다. FBX 안의 서브 에셋 머티리얼을 외부 파일로 꺼내 쓰지 말고, 슬롯에 직접 외부 머티리얼을 넣는다. 이 방식은 `sub-asset ... cannot be used as an external material` 오류를 피한다.
3. BaseColor는 해당 PNG를 넣고 Tiling은 `1,1`로 둔다. Normal PNG의 Texture Type은 `Normal map`, 색상 공간은 Non-Color로 가져오며 Normal Strength는 약 `0.65`에서 시작한다. Rock Smoothness는 약 `0.14`, Earth는 약 `0.05`, Steel은 약 `0.28`, Oxide는 약 `0.10`, Cable은 약 `0.16`을 기준으로 조절한다.
4. 세 FBX 에셋의 **루트 오브젝트**를 기존 씬의 `Environment/EXIT_Module/ElevatorShaft` 아래에 넣는다. 세 루트 모두 Local Position `0,0,0`, Local Rotation `0,0,0`, Local Scale `1,1,1`이다. 이 패키지는 이전 엘리베이터 모델처럼 Unity에서 Y 180도를 추가할 필요가 없다.
5. 기존 `ElevatorShaft`의 회색 큐브 벽은 Mesh Renderer만 끄고 Box Collider와 오브젝트는 유지한다. `Shaft` 오브젝트를 움직이는 `ELEVATOR_Module` 아래로 옮기지 않는다. 승강로는 고정이고 엘리베이터 케이지가 기존처럼 `+Y`로 이동해야 한다.
6. 실험실 문 위치에서 플레이어가 진입할 수 있는지, 케이지의 철망 안쪽에서 암반이 보이는지, 상승 후 흙층과 뿌리가 보이는지 순서대로 Play Mode에서 확인한다. 암반이나 지지대가 실험실 벽을 뚫으면 FBX의 Transform을 임의로 회전하거나 스케일하지 말고 먼저 부모가 `ElevatorShaft`인지 확인한다.

## 좌표와 범위

모델 단위는 metre, Y-up이다. 승강로 높이는 약 `-1.46`에서 `34.45` m이고, 기존 케이지가 움직이는 경로 안쪽은 비워 두었다. 아래쪽은 암반 중심, 대략 `23.5 m` 이상부터 흙층 비중이 커지며 상부에는 드문 뿌리와 케이블 디테일이 있다. 진입구와 실험실 내부에 고정 지지대가 겹치지 않도록 분할했다.

## 검증 범위

세 FBX는 정점·삼각형·UV·노멀·재질 슬롯·원점·단위와 예상 좌표 범위를 검사했다. 중간 높이에서 표본으로 검사한 471개 암반 면은 모두 승강로 안쪽을 향했다. 이 검사는 Unity에서의 실제 임포트·조명·라이드 플레이테스트를 대신하지 않으므로, 마지막 확인은 Unity에서 직접 한다.
