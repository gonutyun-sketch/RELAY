# 지형 교체 파일

이 폴더의 `FOREST_Terrain.fbx`는 바닥 면 방향만 수정한 교체용 파일입니다.

1. Unity Play를 끄고 씬을 저장합니다.
2. 탐색기에서 이 FBX 파일을 복사합니다.
3. `C:\Users\gonut\School_p2\Assets\RELAY\Art\Forest\exports`에 붙여넣고 같은 파일을 덮어씁니다.
4. 기존 `FOREST_Terrain.fbx.meta`와 재질 파일은 그대로 둡니다. 기존 모델을 삭제하거나 새 오브젝트로 추가하지 않습니다.
5. Unity 재가져오기가 끝나면 바닥 재질은 Opaque / Alpha Clipping Off / Render Face Front로 유지합니다.
6. 엘리베이터에서 나와 바닥과 양옆 가장자리를 확인합니다. 바닥이 복구된 뒤에도 보이는 틈은 별도로 위치를 확인해야 합니다.

이 교체는 지형 형태와 위치를 바꾸거나 엘리베이터 틈을 새 구조물로 덮는 작업이 아닙니다. 먼저 아래를 향한 면 때문에 지형이 보이지 않던 원인을 제거합니다. Collider는 이 파일에 포함되지 않으며 Unity 설정과 플레이 테스트는 사용자가 직접 진행합니다.

`before`는 Unity 밖 원본 제작 파일의 수정 전 백업입니다. Unity로 가져올 필요가 없습니다.
