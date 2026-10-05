# RELAY CORE v01

기존 RELAY 게임에 사용자가 직접 연결할 중앙 코어 본체와 CORE 조작 캐비닛이다.
Unity 프로젝트 밖에서 제작했으며 Unity 씬·스크립트·Inspector는 수정하지 않았다.

## 완성 파일

- `RELAY_CORE_v01.blend`: 편집 가능한 부품과 재질, 중립 자세의 FBX용 메시, 별도 미리보기 장면.
- `exports/`: 직접 가져올 FBX 11개.
- `previews/CORE_hero.png`: 코어 본체와 조작 캐비닛의 실제 Blender 렌더.
- `previews/CORE_controls.png`: START 손잡이, 진행률 창, 고온·저온·가동 표시 외형.
- `previews/CORE_emission_study.png`: 발광용 표면에 파란 빛을 넣어 본 별도 렌더. 실제 게임의 전원 연출이 아니다.
- `UNITY_HANDOFF.md`: 기존 계층을 유지하는 수동 연결 순서와 URP 재질 값.
- `manifest.json`: 부품별 크기·원점·재질·삼각형 수·연결값.
- `checks/validation.json`, `checks/lever_sweep.json`: 외부 모델 검증 결과.

모델 총합은 101,654 triangles다. FBX 11개를 실제로 재수입해 크기와 원점을 확인했고,
게이지·경고등·상태 글자 영역이 가려지지 않는 것을 포함해 117개 검사를 통과했다.
START 손잡이는 X -25°부터 -155°까지 131개 자세에서 외장과 겹치지 않았고,
새 막대와 손잡이는 기존 클릭용 Collider 영역 안에 맞췄다.
Unity에서의 가져오기·재질·시야·입력·게임 진행은 사용자가 연결 후 직접 확인해야 한다.

## 외형과 기존 기능

중앙 본체는 현재 `Core_Block`의 3 × 3.5 × 3m 공간에 맞췄다.
밀폐 유리 챔버, 위·아래 전극과 절연체, 금속 지지 기둥, 후면 배관,
상단 전원 인입선, 하부 점검 덮개, 그레이팅과 노란 안전 난간을 포함한다.
챔버 중앙의 빈 공간은 향후 방전 연출을 위한 공간이다.

조작 캐비닛은 `CORE_Module`의 기존 1.8 × 2.4 × 1m 규격과 조작부 위치를 사용한다.
기존 레버 회전축·클릭 판정·진행률 막대·고온/저온/가동 렌더러·동적 상태 글자를 보존한다.
이름표는 앞서 만든 기계처럼 작은 두 나사 금속판으로 만들었다.

중앙 본체와 조작 캐비닛은 미리보기에서 나란히 배치했다.
실제 씬에서는 각각 기존 `Core_Block`과 `CORE_Module` 위치에 따로 붙인다.
렌더의 진행률 막대와 STANDBY는 위치 확인용이다. 이러한 미리보기 오브젝트는 FBX에 포함되지 않는다.

## 다음에 다룰 전원 연출

사용자 방향: POWER를 올리기 전에는 연구실 조명과 기기가 꺼져 있고,
POWER를 올린 뒤 코어가 빛나며 전기 방전과 함께 연구실 조명이 켜진다.
이번 작업에서는 이를 구현하지 않았다. `CORE_Emitter`와 `CORE_Glass`를 분리했으며
저장된 기본 모델의 Emission은 0이다. 방전·실내 조명·전원 상태 연동은 후속 작업이다.

## 원본 다시 생성

`build_core.py`는 `geometry.py`를 사용하며 파일이 있는 이 폴더에만 결과를 쓴다.
Blender 백그라운드 모드에서 실행하면 FBX와 blend를 생성한다.
`render_previews.py`는 저장된 모델을 열어 세 미리보기만 렌더한다.
`validate_core.py`와 `check_lever.py`는 검증 보고서를 이 폴더의 checks 안에 쓴다.

CORE 전용 재질 접두사는 `RLYK_`다. 기존 다른 기계 재질과 공유하거나 이름을 덮어쓰지 않는다.
`.blend`를 Unity Assets로 넣지 말고 `exports`의 FBX만 가져온다.
