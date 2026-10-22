"""인스타 측정 원본 → data/trends.json 갱신 (유행 단계 재판정)

사용법:
  python scripts/build_trends.py raw_YYYYMMDD.json [--date 2026-10-29]

raw 파일 형식 (scripts/collector.js가 만드는 것):
  { "<트렌드 이름>": {"query": "...", "rows": [[code, taken_at, likes, comments, views, user, verified, ai, music, relevant, media_type], ...]}, ... }

판정 규칙 (대시보드 ANALYSIS LOGIC과 동일):
  관련 게시물 < 12  → 측정 불충분
  최근 14일 비중 ≥ 50% → 유행 초기
  최근 30일 비중 ≥ 30% → 유행 중
  그 외 → 유행 지남
지난 측정값은 prev_stage / prev_recent14 로 남겨 주간 변화를 볼 수 있게 함.
"""
import json, sys, time, datetime, argparse, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRENDS = ROOT / 'data' / 'trends.json'


def stage(rel, d14, d30):
    if rel < 12:
        return '측정 불충분'
    if d14 / rel >= 0.5:
        return '유행 초기'
    if d30 / rel >= 0.3:
        return '유행 중'
    return '유행 지남'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('raw')
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    a = ap.parse_args()
    raw = json.load(open(a.raw, encoding='utf-8'))
    trends = json.load(open(TRENDS, encoding='utf-8'))
    now = time.time()
    changed = 0
    for t in trends:
        m = raw.get(t['trend'])
        if not m:
            continue
        ok = [r for r in m['rows'] if len(r) > 1 and r[1] != 'err']
        rel = [r for r in ok if r[9]]
        d14 = sum(1 for r in rel if now - r[1] < 14 * 86400)
        d30 = sum(1 for r in rel if now - r[1] < 30 * 86400)
        n = len(rel)
        t['prev_stage'], t['prev_recent14'] = t.get('stage'), t.get('recent14')
        t.update(stage=stage(n, d14, d30), related=n,
                 recent14=round(d14 / n, 2) if n else None, recent30=round(d30 / n, 2) if n else None,
                 engagement=sum((r[2] or 0) + (r[3] or 0) for r in rel),
                 accounts=len({r[5] for r in rel}), verified=sum(1 for r in rel if r[6]),
                 query=m.get('query', t.get('query')), measured=a.date)
        top = max(rel, key=lambda r: r[2] or 0, default=None)
        if top:
            t.update(top_post=f'https://www.instagram.com/p/{top[0]}/', top_user=top[5],
                     top_date=datetime.date.fromtimestamp(top[1]).isoformat(), top_likes=top[2])
        changed += 1
    json.dump(trends, open(TRENDS, 'w', encoding='utf-8'), ensure_ascii=False)
    from collections import Counter
    print(f'{changed}개 갱신 ·', dict(Counter(t['stage'] for t in trends)))


if __name__ == '__main__':
    main()
