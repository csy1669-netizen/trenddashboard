# TREND DASHBOARD · MLB

MLB MKT 콘텐츠 트렌드 전광판. 수집한 트렌드 키워드를 인스타그램 실제 콘텐츠로 분석해 유행 단계(유행 초기 · 유행 중 · 유행 지남)를 판정합니다.

- 화면: `index.html` (표지 → TREND RANK · FORMAT RANK · TREND KEYWORD · ANALYSIS LOGIC)
- 데이터: `data/trends.json`(트렌드 360개, 매일 갱신) · `data/formats.json`(포맷 13종) · `data/pipeline.json`(분석 5단계)
- 화면은 열 때마다 `data/*.json`을 새로 읽습니다. **데이터 파일만 바꾸면 화면이 바뀝니다.**

## GitHub Pages로 링크 만들기 (처음 한 번)
1. GitHub에서 새 저장소 만들기 (예: `trend-dashboard`)
2. 저장소 화면 → **Add file → Upload files** → 이 폴더 안의 파일·폴더를 전부 끌어다 놓고 **Commit changes**
   (`.nojekyll`이 안 보이면 숨김 파일 표시를 켜고 함께 올리기)
3. **Settings → Pages** → Source: *Deploy from a branch*, Branch: `main` / `/(root)` → Save
4. 1~2분 뒤 `https://<아이디>.github.io/trend-dashboard/` 로 열림

> ⚠️ 무료 GitHub의 Pages 링크는 **누구나 볼 수 있는 공개 페이지**입니다. 사내 자료·인스타 계정명이 들어 있으니,
> 회사 GitHub(Enterprise, 비공개 Pages) 또는 팀 내부 공유용 링크인지 먼저 확인하세요.

## 자동 업데이트 (매일 15:00)
- **매일 13:21** Claude 예약 작업이 시작합니다(크롬이 켜진 PC 필요).
  1. 캐릿 전광판·아티클, 고구마팜에서 새 트렌드 키워드 탐색 → 키워드 풀과 중복 제거
  2. 신규 후보만 인스타 검색 상위 24개로 측정 → 측정 조건(게시물 12↑ · 계정 8↑ · 캡션 일치 25%↑) 통과 시 점수·순위·유행 단계를 매겨 추가
  3. `scripts/weekly_update.py`로 계산 → 대시보드와 `data/*.json` 갱신
- **매주 월요일**(월요일에 PC가 꺼져 있었으면 다음 실행일)에는 전체 트렌드의 유행 단계를 다시 측정합니다. 인스타 과부하를 막기 위해 다른 날은 신규 후보만 검색합니다.
- **매일 15:00** PC가 바뀐 `data/*.json`을 GitHub에 push → 링크에 자동 반영

## 판정 규칙
| 단계 | 기준 |
|---|---|
| 유행 초기 | 관련 게시물 중 최근 14일 게시 비중 50% 이상 |
| 유행 중 | 최근 30일 게시 비중 30% 이상 |
| 유행 지남 | 최근 30일 게시 비중 30% 미만 |
| 측정 불충분 | 관련 게시물 12개 미만 또는 검색 결과 없음 |
