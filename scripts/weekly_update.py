#!/usr/bin/env python3
"""TREND DASHBOARD 매일 갱신 — 신규 키워드 점수화 + 유행 단계 갱신 + 집계.

사용:
  python3 weekly_update.py --data <data 폴더> --date YYYY-MM-DD \
      [--cands cands.json --newout new_out.tsv] [--stageout stage_out.tsv] --outdir out

입력
  data/trends.json, data/formats.json, data/pipeline.json, data/keyword_pool.json
  cands.json   : 이번 회차 신규 후보 [{trend, query, format, category, source, seen}]
                 (지난주 미통과 재측정 후보도 같은 형식, source 앞에 '재측정 · ')
  new_out.tsv  : 신규 후보 측정 결과. 칸: trend, 해시태그 게시물, 게시물 n, 캡션 일치,
                 계정 수, 인증 계정, 좋아요+댓글(전체), 6개월 내 게시, 관련 14일, 관련 30일,
                 관련 좋아요+댓글, 관련 계정, 관련 인증, [대표 코드, 대표 날짜, 대표 좋아요, 대표 계정]
  stage_out.tsv: 기존 트렌드 유행 단계 재측정 결과(주간 지침 4단계 형식).
                 칸: trend, n, 관련, 관련14, 관련30, 좋아요+댓글, 계정, 인증, [대표 코드, 날짜, 좋아요, 계정]
출력(outdir): trends.json, formats.json, pipeline.json, keyword_pool.json, last_update.json, summary.json
"""
import argparse, json, math, os, re, datetime as dt

# 10/16 점수 기준(323개)에서 고정한 환산 범위 — 새 키워드도 같은 자로 잰다
SCALE = {
    'vol': (0.0, 6.60744494317638),           # log10(1+해시태그 게시물)
    'rea': (2.95375969173323, 6.75437081445632),  # log10(1+상위24 좋아요+댓글)
    'spr': (0.0416666666666667, 1.0),          # (계정-인증)/게시물
    'rec': (0.0, 1.0),                         # 6개월 내 게시/게시물
}
W = {'vol': 0.3, 'rea': 0.3, 'spr': 0.2, 'rec': 0.2}
COND = dict(n=12, accounts=8, match=0.25)


def to10(x, k):
    lo, hi = SCALE[k]
    v = 1 + 9 * (x - lo) / (hi - lo)
    return max(1.0, min(10.0, v))


def stage_of(rel, r14, r30):
    if rel < 12:
        return '측정 불충분'
    if r14 / rel >= 0.5:
        return '유행 초기'
    if r30 / rel >= 0.3:
        return '유행 중'
    return '유행 지남'


def norm(s):
    return re.sub(r"[\s·‘’'\"()\-_/.,?!:]", '', (s or '').lower())


def read_tsv(p):
    rows = []
    if not p or not os.path.exists(p):
        return rows
    for line in open(p, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.strip():
            rows.append(line.split('\t'))
    return rows


def num(x):
    try:
        return int(float(x))
    except Exception:
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--date', required=True)
    ap.add_argument('--cands')
    ap.add_argument('--newout')
    ap.add_argument('--stageout')
    ap.add_argument('--outdir', required=True)
    a = ap.parse_args()
    D = lambda f: json.load(open(os.path.join(a.data, f), encoding='utf-8'))
    trends, formats, pipeline, pool = D('trends.json'), D('formats.json'), D('pipeline.json'), D('keyword_pool.json')
    try:
        prev_last = D('last_update.json')
    except Exception:
        prev_last = {}
    prev_pipe = {x.get('step'): x for x in pipeline}
    today = a.date
    md = f"{int(today[5:7])}/{int(today[8:10])}"
    os.makedirs(a.outdir, exist_ok=True)
    byname = {t['trend']: t for t in trends}
    prev_counts = {}
    for t in trends:
        prev_counts[t['stage']] = prev_counts.get(t['stage'], 0) + 1

    # ---- 1) 기존 트렌드 유행 단계 갱신
    stage_rows = read_tsv(a.stageout)
    posts_stage = 0
    for r in stage_rows:
        t = byname.get(r[0])
        if not t:
            continue
        n, rel, r14, r30 = num(r[1]), num(r[2]), num(r[3]), num(r[4])
        posts_stage += n
        t['prev_stage'] = t.get('stage')
        t['prev_recent14'] = t.get('recent14')
        t['stage'] = stage_of(rel, r14, r30)
        t['related'] = rel
        t['recent14'] = round(r14 / rel, 2) if rel else None
        t['recent30'] = round(r30 / rel, 2) if rel else None
        t['engagement'], t['accounts'], t['verified'] = num(r[5]), num(r[6]), num(r[7])
        t['measured'] = today
        if len(r) >= 12 and r[8]:
            t['top_post'] = f'https://www.instagram.com/p/{r[8]}/'
            t['top_date'], t['top_likes'], t['top_user'] = r[9], num(r[10]), r[11]

    # ---- 2) 신규 후보 점수화
    cands = json.load(open(a.cands, encoding='utf-8')) if a.cands else []
    cmap = {c['trend']: c for c in cands}
    new_rows = read_tsv(a.newout)
    poolidx = {norm(p['keyword']): p for p in pool}
    added, failed, posts_new = [], [], 0
    scored_existing, removed = [], []
    for r in new_rows:
        c = cmap.get(r[0])
        if not c:
            continue
        hc, n, match, acc, ver, eng_all, in6, r14, r30, rel_eng, rel_acc, rel_ver = [num(x) for x in r[1:13]]
        rel = match
        posts_new += n
        ok = n >= COND['n'] and acc >= COND['accounts'] and n and match / n >= COND['match']
        key = norm(c['trend'])
        pe = poolidx.get(key)
        if not pe:
            pe = {'id': len(pool) + 1, 'keyword': c['trend'], 'filter': '후보', 'type': c.get('format'),
                  'source': c.get('source'), 'mentions': 1, 'first_seen': c.get('seen') or today,
                  'last_seen': c.get('seen') or today}
            pool.append(pe)
            poolidx[key] = pe
        pe.update({'query': c['query'], 'last_measured': today, 'tries': pe.get('tries', 0) + 1,
                   'status': '측정 통과' if ok else ('검색 결과 없음' if n == 0 else '측정 미통과')})
        if not ok:
            failed.append({'trend': c['trend'], 'n': n, 'match': match, 'accounts': acc})
            old = byname.get(c['trend'])
            if old is not None and old.get('score') is None:  # 점수 없는 트렌드가 조건 미통과 → 목록에서 빼고 풀에 남김
                trends.remove(old)
                del byname[c['trend']]
                removed.append(c['trend'])
            continue
        v = {'vol': to10(math.log10(1 + hc), 'vol'), 'rea': to10(math.log10(1 + eng_all), 'rea'),
             'spr': to10((acc - ver) / n, 'spr'), 'rec': to10(in6 / n, 'rec')}
        score = round(sum(v[k] * W[k] for k in W), 2)
        row = {'trend': c['trend'], 'category': c['category'], 'format': c['format'], 'rank': None,
               'score': score, 'volume': round(v['vol'], 1), 'reaction': round(v['rea'], 1),
               'spread': round(v['spr'], 1), 'recency': round(v['rec'], 1), 'hashtag_posts': hc,
               'top24_likes': eng_all, 'origin': f"신규 ({md} 탐색 · {c.get('source', '')})",
               'stage': stage_of(rel, r14, r30), 'recent14': round(r14 / rel, 2) if rel else None,
               'recent30': round(r30 / rel, 2) if rel else None, 'related': rel, 'engagement': rel_eng,
               'accounts': rel_acc, 'verified': rel_ver, 'query': c['query'], 'measured': today,
               'is_new': True, 'added': today, 'prev_stage': None}
        if len(r) >= 17 and r[13]:
            row.update({'top_post': f'https://www.instagram.com/p/{r[13]}/', 'top_date': r[14],
                        'top_likes': num(r[15]), 'top_user': r[16]})
        else:
            row.update({'top_post': None, 'top_date': None, 'top_likes': None, 'top_user': None})
        old = byname.get(c['trend'])
        if old is not None:
            if old.get('score') is None:  # 점수 없이 단계만 재던 트렌드 → 점수·순위 부여
                keep = {k: old[k] for k in ('origin', 'added', 'is_new', 'prev_stage') if k in old}
                old.update(row)
                old.update(keep)
                scored_existing.append(old)
            continue
        trends.append(row)
        byname[row['trend']] = row
        added.append(row)

    # 신규 표시: 추가 후 7일 동안
    td = dt.date.fromisoformat(today)
    for t in trends:
        if t.get('added'):
            t['is_new'] = (td - dt.date.fromisoformat(t['added'])).days < 7

    # ---- 3) 종합 순위 다시 매기기 (점수 있는 트렌드 전체)
    scored = sorted([t for t in trends if t.get('score') is not None],
                    key=lambda t: (-t['score'], t['trend']))
    for i, t in enumerate(scored, 1):
        t['prev_rank'] = t.get('rank')
        t['rank'] = i
    trends.sort(key=lambda t: (t['rank'] is None, t['rank'] or 0, t['trend']))

    # ---- 4) 포맷 집계
    fmeta = {f['format']: f for f in formats}
    groups = {}
    for t in scored:
        groups.setdefault(t['format'], []).append(t)
    for name, f in fmeta.items():
        g = groups.get(name, [])
        top5 = [t['score'] for t in g[:5]]
        f['score'] = round(sum(top5) / len(top5), 2) if top5 else 0
        f['trends'] = len([t for t in trends if t['format'] == name])
        f['in_top30'] = len([t for t in g if t['rank'] <= 30])
        f['in_top100'] = len([t for t in g if t['rank'] <= 100])
        f['top_trends'] = ' · '.join(t['trend'] for t in g[:3])
    for i, f in enumerate(sorted(formats, key=lambda f: -f['score']), 1):
        f['format_rank'] = i
    formats.sort(key=lambda f: f['format_rank'])

    # ---- 5) 파이프라인 (5단계)
    counts = {}
    for t in trends:
        counts[t['stage']] = counts.get(t['stage'], 0) + 1
    measured_now = len(stage_rows) + len(new_rows)
    posts_now = posts_stage + posts_new
    full_day = bool(stage_rows)  # 전체 유행 단계 재측정한 날(주 1회)
    full_measured = today if full_day else prev_last.get('full_measured', prev_last.get('measured', today))
    fmd = f"{int(full_measured[5:7])}/{int(full_measured[8:10])}"
    p2 = prev_pipe.get(2, {})
    pipeline = [
        {'step': 1, 'name': '키워드 자동 수집', 'value': f'{len(pool):,}개', 'count': len(pool),
         'detail': f'누적 키워드 풀 · 매일 캐릿 전광판·아티클, 고구마팜에서 탐색 · 오늘 신규 후보 {len(cands)}개',
         'tools': 'Python 크롤링 · Claude in Chrome · Apify · YouTube API · NAVER API', 'date': md},
        ({'step': 2, 'name': '인스타 콘텐츠 수집', 'value': f'{measured_now:,}개', 'count': measured_now,
         'detail': f'키워드별 인스타 검색 상위 24개 · 게시물 {posts_now:,}건 (검색 화면 데이터 읽기, 키워드당 요청 1회)',
         'tools': 'Claude in Chrome · JavaScript · Meta API', 'date': md} if full_day else
         {'step': 2, 'name': '인스타 콘텐츠 수집', 'value': p2.get('value', f'{measured_now:,}개'), 'count': p2.get('count', measured_now),
         'detail': f"{p2.get('detail', '').split(' · 오늘')[0]} · 오늘 신규 후보 {len(new_rows)}개 측정",
         'tools': p2.get('tools', 'Claude in Chrome · JavaScript · Meta API'), 'date': p2.get('date', fmd)}),
        {'step': 3, 'name': '점수화 · 순위 측정', 'value': f'{len(scored):,}개', 'count': len(scored),
         'detail': f'측정 조건 통과 → 볼륨·반응·확산·최근성 가중합 · 매일 신규 통과분 추가 후 전체 순위 재정렬 · 오늘 신규 통과 {len(added)}개',
         'tools': 'Python 점수화 스크립트 · Claude 포맷 분류', 'date': md},
        {'step': 4, 'name': '유행 단계 측정', 'value': f'{len(trends):,}개', 'count': len(trends),
         'detail': f"게시일 분포로 판정 · 유행 초기 {counts.get('유행 초기', 0)} · 유행 중 {counts.get('유행 중', 0)} · 유행 지남 {counts.get('유행 지남', 0)} · 단계 측정 {fmd}",
         'tools': 'Claude in Chrome · Python', 'date': md},
        {'step': 5, 'name': '자동화 · 대시보드 업데이트', 'value': '매일 15:00', 'count': 0,
         'detail': '매일 13:21 Claude 예약 작업 시작 → 신규 키워드 탐색·인스타 측정·점수·단계 판정 → 15:00까지 대시보드 반영 → 15:00 GitHub 자동 반영',
         'tools': 'Claude 예약 작업 · Windows 작업 스케줄러 · GitHub Pages', 'date': md},
    ]

    last = {'measured': today, 'trends': len(trends), 'scored': len(scored), 'pool': len(pool),
            'new_candidates': len(cands), 'new_added': len(added), 'stages': counts,
            'discovered_until': today, 'full_measured': full_measured, 'by': 'Claude (매일 예약 측정)'}
    summary = {'scored_existing': [{'trend': t['trend'], 'score': t['score'], 'rank': t['rank'], 'stage': t['stage']} for t in scored_existing],
               'removed': removed,
               'added': [{'trend': t['trend'], 'score': t['score'], 'rank': t['rank'], 'stage': t['stage'],
                          'recent14': t['recent14'], 'format': t['format']} for t in added],
               'failed': failed, 'stages_now': counts, 'stages_prev': prev_counts,
               'new_early': [t['trend'] for t in trends if t['stage'] == '유행 초기' and (t.get('prev_stage') not in ('유행 초기', None) or t.get('added') == today)],
               'dropped': [t['trend'] for t in trends if t.get('prev_stage') in ('유행 초기', '유행 중') and t['stage'] == '유행 지남'],
               'posts': posts_now, 'measured': measured_now, 'full_day': full_day, 'full_measured': full_measured}
    for name, obj in [('trends.json', trends), ('formats.json', formats), ('pipeline.json', pipeline),
                      ('keyword_pool.json', pool), ('last_update.json', last), ('summary.json', summary)]:
        json.dump(obj, open(os.path.join(a.outdir, name), 'w', encoding='utf-8'), ensure_ascii=False,
                  indent=None if name in ('trends.json', 'keyword_pool.json') else 1)
    print(json.dumps({k: summary[k] for k in ('stages_now', 'posts', 'measured')}, ensure_ascii=False))
    print('added', len(added), [t['trend'] for t in added])
    print('failed', len(failed))
    print('scored_existing', [(t['trend'], t['rank'], t['stage']) for t in scored_existing])
    print('removed', removed)


if __name__ == '__main__':
    main()
