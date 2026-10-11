# RELAY / FOREST 01 — Spruce A

## 오늘의 완성 범위

안개 낀 산속 침엽수림을 위한 첫 번째 나무 한 종류다. 약 11.82m 높이의 가문비나무형 침엽수이며, 굵은 줄기와 뿌리, 마른 하단 가지, 굽고 처진 큰 가지, 잔가지와 바늘잎을 포함한다. 중심 줄기는 조금 휘고 가지마다 길이와 높이, 방향이 다르다. 하단 뿌리는 지면 아래 약 8cm까지 이어지므로 나무 밑동을 지면 높이에 맞춘다.

숲 전체 지형, 바위, 추가 수종, 낙엽과 하층 식생, 바람, 안개 및 Unity 배치는 다음 회차 범위다. 이 모델 한 종류만 복제해 최종 숲을 채우는 것은 목표가 아니다. 첫 나무의 질감과 크기를 기준으로 다음 모델을 맞춘다.

## 파일

- `RELAY_FOREST_Spruce_A.blend`: 원본 모델. 나무껍질과 잎 텍스처를 내부에 패킹했다. LOD0 컬렉션만 기본 표시되며 다른 LOD는 숨겨져 있다.
- `RELAY_FOREST_Spruce_A_Review.blend`: 카메라, 검토 조명, 단색 지면을 포함한 미리보기 장면. 단색 지면은 숲 지형 모델이 아니다.
- `exports/FOREST_Spruce_A_LOD0.fbx`: 가까운 곳에서 볼 원본, 118,786 triangles.
- `exports/FOREST_Spruce_A_LOD1.fbx`: 중거리용, 52,866 triangles.
- `exports/FOREST_Spruce_A_LOD2.fbx`: 먼 거리용, 14,786 triangles.
- `textures/`: 2048px bark BaseColor / Normal / Roughness, RGBA 바늘잎 아틀라스, 재질 검토 이미지 및 검사 기록.
- `previews/`: 실제 Blender 모델의 전체 모습·줄기/뿌리·바늘잎 렌더.
- `checks/`: FBX 원시 구조 검사 및 파일 검증 자료.
- `manifest.json`: LOD별 메시 수치, 좌표 범위, 확인한 원본 씬/스크립트 해시.

각 LOD에는 Wood와 Needles 두 메시가 있다. 재질은 `RLYF_SpruceBark`, `RLYF_ExposedWood`, `RLYF_SpruceNeedles` 세 개다. LOD별 모델은 같은 원점을 사용하며 뿌리 중심이 `(0,0,0)`이다. 단위는 metre, Unity Y-up 기준이다. 기존 승강로와 같은 축 보정을 FBX에 적용했으므로 기본 배치는 Rotation `(0,0,0)`, Scale `(1,1,1)`이다. 실제 Unity 임포트 결과는 아직 확인하지 않았다.

## 이번 회차의 경계

모든 제작은 `C:\Users\gonut\RELAY_Art\FOREST_01_HeroTree`에서 이루어졌다. Unity UI, 씬, Inspector, 머티리얼, 스크립트에 직접 변경을 적용하지 않았다. 사용자 요청대로 엘리베이터 승강로 연결도 이번 회차에 진행하지 않았다.

## 나중에 직접 연결할 때의 재질 기준

이 절은 연결할 때 사용하는 참고용이다. 지금 Unity에 적용해야 한다는 뜻은 아니다.

세 재질 모두 기본 `Universal Render Pipeline/Lit`을 사용한다. 잎은 RGBA 이미지의 alpha로 윤곽을 자르는 방식이며, 잎 하나하나가 개별 3D 바늘 메시인 것은 아니다. 여러 방향으로 구부린 잎 면을 잔가지에 배치해 볼륨을 구성했다.

| 재질 | Base Map / Color | 나머지 기준 |
|---|---|---|
| SpruceBark | `RLYF_Bark_BaseColor.png`, 흰색 tint | Metallic 0, Smoothness 약 0.12, Normal Map `RLYF_Bark_Normal.png` strength 0.7 |
| ExposedWood | 텍스처 없음, `#9D8970` | Metallic 0, Smoothness 0.05 |
| SpruceNeedles | `RLYF_Needles_Atlas.png`, 흰색 tint | Surface Type Opaque, Alpha Clipping ON, Threshold 0.45, Render Face Both, Metallic 0, Smoothness 약 0.18 |

바늘잎 아틀라스의 Alpha Source는 Input Texture Alpha, Alpha Is Transparency는 ON으로 시작한다. Mip Maps를 유지하고, Mip Maps Preserve Coverage를 사용할 경우 Alpha Cutoff를 0.45로 맞춘다. 정상 출력 확인은 고품질 압축 또는 압축 없음에서 먼저 하고, 이후 실제 게임 성능을 보며 조절한다. 사각 잎 면이 그대로 보이면 먼저 Alpha Clipping과 alpha 입력을 확인한다. 잎이 한쪽에서 사라지면 Render Face Both를 확인한다.

Normal PNG는 Texture Type을 Normal map으로 지정한다. Roughness PNG는 Blender/원본용으로 제공한다. URP의 Metallic Map에 그대로 넣으면 안 된다. 위 표의 Smoothness 숫자로 시작하고, 별도 패킹이 필요할 때만 roughness를 1-roughness로 변환해 metallic/smoothness map의 alpha에 넣는다.

설정 의미 확인: [Unity 6.3 URP Lit 공식 문서](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/lit-shader.html).

LOD는 나중에 사용자가 LOD Group으로 연결한다. LOD0, LOD1, LOD2 세 모델을 같은 위치에 모두 표시해 두면 중복 렌더된다. 초기에 한 LOD씩 단독 확인하고, 각 LOD 단계에 Wood/Needles 두 Renderer를 함께 등록한다. 원본은 가까운 몇 그루에 쓰고 전체 숲은 낮은 LOD와 별도 배경 모델로 구성할 예정이다. 바람 변형, 자동 LOD Group, 콜라이더는 이번 FBX에 포함하지 않았다.

## 현재 엔딩 배치 기준 — 읽기 전용 확인

확인한 씬의 `MountainEnding` 원점은 world `(0,30,-10)`이며 지면은 local Y=0이다. 앞쪽 산을 보는 방향은 local +Z다. 기존 평지는 20×20m이고 후면의 엘리베이터 출구 폭은 2.4m다. 출구와 중앙 이동로를 비우고, 나무는 양옆에서 시선을 감싸게 배치한다. 나무 한 그루의 잎 포함 폭은 약 6m이므로 줄기 위치만 보고 통로를 확보했다고 판단하면 안 된다.

엔딩 판정은 산 방향을 바라보는지 확인하지만 나무가 시야를 가렸는지는 검사하지 않는다. 따라서 중심 전망을 잎으로 완전히 막지 않는 배치가 필요하다. 이 수치는 파일에서 읽어 확인한 것으로 Unity에서 이번 모델을 배치하거나 플레이 테스트한 결과는 아니다.

## 다음 제작 순서

1. **FOREST 01 / 현재**: 가까이 볼 기준 침엽수 A, 3단계 LOD와 질감.
2. **FOREST 02**: 산 정상의 지면과 좁은 길, 큰 바위 2~3개, 이끼 경계. 출구에서 산을 바라보는 구도를 먼저 고정.
3. **FOREST 03**: 수형이 다른 침엽수 B, 어린 나무, 고사목과 쓰러진 통나무. 같은 나무의 복제 패턴 줄이기.
4. **FOREST 04**: 고사리·풀·작은 돌·마른 가지 등 플레이어 발밑 디테일.
5. **최종 수동 연결**: 사용자가 Unity에서 배치, 안개·조명·바람·LOD·충돌과 엔딩 중 이동 확인. 실제 해상도와 성능을 측정한 뒤 밀도 조절.

각 회차는 모델 생성 → 실제 렌더 확인 → FBX 검증 → 파일 전달에서 마무리한다. 이번 나무도 그 기준으로 검토했으며, 숲 전체 또는 Unity에서의 최종 화질/성능이 완료됐다는 의미는 아니다.
