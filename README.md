# TREND DASHBOARD · MLB

MLB MKT 콘텐츠 트렌드 전광판. 수집한 트렌드 키워드를 인스타그램 실제 콘텐츠로 분석해 유행 단계(유행 초기 · 유행 중 · 유행 지남)를 판정합니다.

- 화면: `index.html` (표지 → TREND RANK · FORMAT RANK · TREND KEYWORD · ANALYSIS LOGIC)
- 데이터: `data/trends.json`(트렌드 332개) · `data/formats.json`(포맷 13종) · `data/pipeline.json`(분석 5단계)
- 화면은 열 때마다 `data/*.json`을 새로 읽습니다. **데이터 파일만 바꾸면 화면이 바뀝니다.**

## GitHub Pages로 링크 만들기 (처음 한 번)
1. GitHub에서 새 저장소 만들기 (예: `trend-dashboard`)
2. 저장소 화면 → **Add file → Upload files** → 이 폴더 안의 파일·폴더를 전부 끌어다 놓고 **Commit changes**
   (`.nojekyll`이 안 보이면 숨김 파일 표시를 켜고 함께 올리기)
3. **Settings → Pages** → Source: *Deploy from a branch*, Branch: `main` / `/(root)` → Save
4. 1~2분 뒤 `https://<아이디>.github.io/trend-dashboard/` 로 열림

> ⚠️ 무료 GitHub의 Pages 링크는 **누구나 볼 수 있는 공개 페이지**입니다. 사내 자료·인스타 계정명이 들어 있으니,
> 회사 GitHub(Enterprise, 비공개 Pages) 또는 팀 내부 공유용 링크인지 먼저 확인하세요.

## 주 1회 업데이트
1. 크롬(인스타그램 로그인) → `scripts/collector.js`로 키워드 검색 측정 → `raw_YYYYMMDD.json` 저장
2. `python scripts/build_trends.py raw_YYYYMMDD.json` → `data/trends.json` 갱신 (지난 단계는 `prev_stage`로 보존)
3. 바뀐 `data/trends.json`을 저장소에 다시 올리기 (Upload files 또는 `git push`)

## 판정 규칙
| 단계 | 기준 |
|---|---|
| 유행 초기 | 관련 게시물 중 최근 14일 게시 비중 50% 이상 |
| 유행 중 | 최근 30일 게시 비중 30% 이상 |
| 유행 지남 | 최근 30일 게시 비중 30% 미만 |
| 측정 불충분 | 관련 게시물 12개 미만 또는 검색 결과 없음 |
