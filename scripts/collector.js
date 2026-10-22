/* 인스타그램 키워드 검색 측정기 — 크롬에서 인스타그램에 로그인한 탭의 개발자 도구 콘솔에서 실행
 *
 * 방식: 키워드 검색 결과 화면이 이미 갖고 있는 게시물 데이터(게시일·좋아요·댓글·조회수·캡션·계정)를 읽습니다.
 *       키워드당 요청은 검색 1번뿐이라 게시물 상세 API를 반복 호출하던 방식보다 계정 부담이 훨씬 작습니다.
 *
 * 1) setup: TD_SETUP([{trend:'치이카와', query:'치이카와', tok:['치이카와']}, ...])  ← data/trends.json의 trend·query로 만듦
 * 2) 매 페이지에서 TD_NEXT() 실행 → 측정 후 다음 검색어로 이동 (페이지가 바뀌면 이 파일을 다시 붙여넣고 TD_NEXT())
 * 3) 끝나면 TD_EXPORT() → raw JSON을 복사해 raw_YYYYMMDD.json으로 저장 → python scripts/build_trends.py raw_YYYYMMDD.json
 */
window.TD_SETUP = (list) => { localStorage.setItem('TDQ', JSON.stringify(list)); localStorage.setItem('TDP', '0'); localStorage.setItem('TDR', '{}'); return list.length + '개 대기'; };
window.TD_EXPORT = () => localStorage.getItem('TDR');
window.TD_NEXT = async () => {
  const Q = JSON.parse(localStorage.getItem('TDQ') || '[]'); let p = +(localStorage.getItem('TDP') || 0);
  if (p >= Q.length) return 'DONE';
  const cur = new URLSearchParams(location.search).get('q');
  let msg = '';
  if (location.pathname.startsWith('/explore/search/keyword') && cur === Q[p].query) {
    const GX = () => {
      const a = document.querySelector('a[href*="/p/"],a[href*="/reel/"]'); if (!a) return null;
      const k = Object.keys(a).find((k) => k.startsWith('__reactFiber')); let f = a[k], d = 0, mi = null, env = null;
      while (f && d < 120) { const pr = f.memoizedProps; if (pr && Array.isArray(pr.mediaItems) && !mi) mi = pr.mediaItems; if (!env && pr && pr.value && pr.value.environment && pr.value.environment.getStore) env = pr.value.environment; if (!env && pr && pr.environment && pr.environment.getStore) env = pr.environment; f = f.return; d++; }
      return mi && env ? {mi, env} : null;
    };
    let X = null; for (let i = 0; i < 20; i++) { X = GX(); if (X && X.mi.length >= 24) break; await new Promise((r) => setTimeout(r, 700)); }
    const tok = (Q[p].tok || [Q[p].query]).map((t) => t.toLowerCase());
    let rows = [];
    if (X) {
      const src = X.env.getStore().getSource();
      rows = X.mi.slice(0, 24).map((it) => { try {
        const m = src.get(it.mediaRef.__id); const u = (m.user && src.get(m.user.__ref)) || {}; const cp = m.caption && src.get(m.caption.__ref);
        const cap = ((cp && cp.text) || '').toLowerCase(); const ai = /(^|[^a-z])ai([^a-z]|$)|인공지능/.test(cap) ? 1 : 0;
        return [m.code, m.taken_at, m.like_count || 0, m.comment_count || 0, m.view_count || 0, u.username, u.is_verified ? 1 : 0, ai, '', tok.some((t) => cap.includes(t)) ? 1 : 0, m.media_type];
      } catch (e) { return [it.code, 'err']; } });
    }
    const R = JSON.parse(localStorage.getItem('TDR') || '{}'); R[Q[p].trend] = {query: Q[p].query, rows}; localStorage.setItem('TDR', JSON.stringify(R));
    msg = `${Q[p].trend} n=${rows.length}`; p++; localStorage.setItem('TDP', String(p));
  }
  if (p < Q.length) setTimeout(() => { location.href = '/explore/search/keyword/?q=' + encodeURIComponent(Q[p].query); }, 100);
  return msg + ' > ' + p + '/' + Q.length;
};
