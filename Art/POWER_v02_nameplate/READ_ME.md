# RELAY POWER v02 — 명판만 수정

기존 v02의 POWER 명판과 명판 고정 나사 두 개만 수정했습니다.

- 명판: 350 × 100 × 3mm, 검은 회색 에나멜 표면
- 글자: POWER 한 줄, 가운데 배치, 대문자 높이 35mm
- 작은 설명 문구와 큰 빈 여백 제거
- 기존 계기·스위치·레버·외함·기타 글자·재질·회전축 유지

`RELAY_POWER_v02_nameplate.blend`를 열면 전체 수정본을 볼 수 있습니다.
`previews/POWER_nameplate_detail.png`는 명판 확대, `POWER_nameplate_hero.png`는 전체 모습입니다.

부품 FBX 중 바뀐 파일은 `exports/POWER_Cabinet.fbx` 하나입니다. 나머지 11개는 이전 v02와 파일 내용이 같습니다. 기존 v02를 이미 가져왔다면 명판을 포함한 외함만 교체하면 됩니다. Unity는 직접 수정하지 않았습니다.

추가된 재질은 다음 두 개입니다. Unity에서 직접 URP/Lit 재질을 연결할 경우의 값입니다.

| 재질 | 색상 | Metallic | Smoothness |
|---|---|---:|---:|
| RLY02_NameplateEnamel | #30352F | 0 | 0.38 |
| RLY02_NameplatePrint | #C8C7B4 | 0 | 0.24 |

회전축 연결과 기존 재질 설정은 v02 안내와 같습니다. 검증 결과는 `nameplate_validation.json`에 기록되어 있습니다. Blender 내 검사이며 실제 Unity 플레이 검증은 포함하지 않습니다.
