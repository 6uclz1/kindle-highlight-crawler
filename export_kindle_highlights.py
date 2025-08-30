#!/usr/bin/env python3
"""
export_kindle_highlights_scroll_click.py

左一覧をスクロールして対象を可視化してからクリックし、その書籍に紐づくハイライトを取得して CSV 出力します。
"""

import asyncio
import argparse
import csv
import os
import re
import time
import unicodedata
from typing import List, Dict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://read.amazon.co.jp/notebook/"
USER_DATA_DIR = "user_data"
DEFAULT_TIMEOUT = 20000  # ms

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

async def get_candidate_titles(page) -> List[str]:
    """左の一覧に相当する 'a' タグのうち '著者:' を含むテキストを抽出し、書名部分のみ返す"""
    try:
        await page.wait_for_selector("a", timeout=DEFAULT_TIMEOUT)
    except PlaywrightTimeoutError:
        return []

    texts = await page.eval_on_selector_all(
        "a",
        """els => els.map(e => (e.textContent||'').trim()).filter(t => t && t.includes('著者:'))"""
    )
    titles = []
    for t in texts:
        left = t.split("著者:")[0].strip()
        if left:
            titles.append(left)
    seen = set(); uniq = []
    for t in titles:
        if t not in seen:
            seen.add(t); uniq.append(t)
    return uniq

async def bring_into_view_by_scrolling(page, title: str) -> bool:
    """ページ内の a タグを探し、見つかったら最も近いスクロール可能な祖先をスクロールして可視化する。
       戻り値: 真=スクロールを試みた/見つけた、偽=見つからなかった
    """
    scroll_script = r'''
    (title) => {
      const anchors = Array.from(document.querySelectorAll('a'));
      for (const el of anchors) {
        try {
          if (!el || !(el.textContent || '').includes(title)) continue;
          // 見つけたら最も近いスクロール可能な祖先を探す
          let anc = el.parentElement;
          while (anc && anc !== document.body) {
            const style = window.getComputedStyle(anc);
            const overflowY = (style.overflowY || style.overflow || '').toLowerCase();
            if (overflowY === 'auto' || overflowY === 'scroll' || anc.scrollHeight > anc.clientHeight) {
              // スクロールして要素を中央付近に持ってくる
              const offset = el.offsetTop - Math.floor(anc.clientHeight / 2);
              anc.scrollTop = offset > 0 ? offset : 0;
              return true;
            }
            anc = anc.parentElement;
          }
          // フォールバック: 要素自身を中央にスクロール
          el.scrollIntoView({behavior:'auto', block:'center', inline:'nearest'});
          return true;
        } catch (e) {
          continue;
        }
      }
      return false;
    }
    '''
    try:
        return await page.evaluate(scroll_script, title)
    except Exception:
        return False

async def click_book_by_title(page, title: str) -> bool:
    """スクロール→可視化→クリックの一連を実行。成功したら True を返す。"""
    attempts = 10
    for attempt in range(attempts):
        # 1) スクロールで可視化を試みる（スクロール可能祖先を調整）
        _ = await bring_into_view_by_scrolling(page, title)
        await asyncio.sleep(1)  # アニメーションや差分読み込みの猶予

        # 2) Playwright 側でも要素を視界内にする（二重保証）
        try:
            anchors = page.locator("a", has_text=title)
            count = await anchors.count()
            # 優先：表示されている要素を探してクリック
            for i in range(count):
                el = anchors.nth(i)
                if await el.is_visible():
                    try:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(0.12)
                        await el.click(timeout=8000)
                        return True
                    except Exception:
                        # 個別にクリックできない場合は次へ
                        continue
            # 表示されていないが候補がある場合は最初の候補をスクロールしてクリックを試す
            if count > 0:
                el = anchors.first
                try:
                    await el.scroll_into_view_if_needed()
                    await asyncio.sleep(0.12)
                    await el.click(timeout=8000)
                    return True
                except Exception:
                    # 再試行ループへ
                    await asyncio.sleep(0.4)
                    continue
            # フォールバック: 部分一致のテキスト検索
            others = page.get_by_text(title, exact=False)
            other_count = await others.count()
            for i in range(other_count):
                el = others.nth(i)
                try:
                    await el.scroll_into_view_if_needed()
                    await asyncio.sleep(0.12)
                    await el.click(timeout=8000)
                    return True
                except Exception:
                    continue
        except Exception:
            pass

        # 少し待って再試行
        await asyncio.sleep(0.6)
    return False


async def safe_click_and_wait(page, title, click_fn, wait_fn, timeout=20000, max_reloads=2):
    """
    安全にクリックしてコンテキスト出現を待つヘルパー。
    - click_fn(page, title) -> bool: クリック処理
    - wait_fn(page, title, timeout=...) -> bool: コンテキスト検出
    - コンソールに KPUtils / srsBaseHref 等のエラーが出たら reload -> 再試行する
    """
    for attempt in range(max_reloads + 1):
        error_count = 0

        # コンソールメッセージを監視して特定のエラー文字列をカウントする
        def _on_console(msg):
            nonlocal error_count
            try:
                # Playwright ConsoleMessage: use type and text()
                mtype = msg.type
                txt = msg.text if hasattr(msg, 'text') else msg.text()
                if mtype == "error":
                    if ("srsBaseHref" in txt) or ("KPUtils" in txt) or ("KPUtils.min.js" in txt):
                        error_count += 1
            except Exception:
                pass

        # attach handler
        try:
            page.on("console", _on_console)
        except Exception:
            # 一部の環境では page.on の挙動が異なる可能性があるため黙って続行
            pass

        ok = False
        try:
            ok = await click_fn(page, title)
        except Exception:
            ok = False

        # クリック自体に失敗したらリロードしてリトライ
        if not ok:
            try:
                await page.reload()
                try:
                    await page.wait_for_selector("a", timeout=16000)
                except Exception:
                    await asyncio.sleep(1.0)
            except Exception:
                await asyncio.sleep(1.0)
            try:
                page.off("console", _on_console)
            except Exception:
                pass
            continue

        # クリック成功後にコンテキストが出るか待つ（短めの総合待機）
        ctx_ok = False
        try:
            # wait_fn は内部で待機するため、ここでは全体タイムアウトだけ保証
            ctx_ok = await asyncio.wait_for(wait_fn(page, title, timeout=min(timeout, 15000)), timeout=20)
        except asyncio.TimeoutError:
            ctx_ok = False
        except Exception:
            ctx_ok = False

        # detach handler
        try:
            page.off("console", _on_console)
        except Exception:
            pass

        # コンソールエラーが発生していたらリロードして再試行
        if error_count > 0:
            try:
                await page.reload()
                try:
                    await page.wait_for_selector("a", timeout=8000)
                except Exception:
                    await asyncio.sleep(1.0)
            except Exception:
                await asyncio.sleep(1.0)
            continue

        if ctx_ok:
            return True

        # コンテキストが得られなかった場合もリロードして再試行
        try:
            await page.reload()
            try:
                await page.wait_for_selector("a", timeout=8000)
            except Exception:
                await asyncio.sleep(1.0)
        except Exception:
            await asyncio.sleep(1.0)

    return False

async def wait_for_book_context(page, title: str, timeout=20000) -> bool:
    """クリック後、対象書籍のコンテキスト（ヘッダ等）が表示されたかを検証する"""
    def norm(s: str) -> str:
        if not s:
            return ""
        s = unicodedata.normalize("NFKC", s)
        s = re.sub(r"[\u3000\s]+", " ", s)  # 全角スペース含めて圧縮
        s = re.sub(r"[“”\"'「」『』\(\)\[\]\s]+", " ", s)
        return s.strip()

    def token_list(s: str):
        s2 = re.sub(r"[^\w\u3000-\u30FF\u4E00-\u9FFF\-]", " ", s)  # 英数＋日本語ブロックを残す
        toks = [t for t in re.split(r"\s+", s2) if len(t) >= 2]
        return toks

    n_title = norm(title or "")
    title_toks = token_list(n_title)

    # まずは注釈コンテナかハイライトが出るまで短く待つ（SPA の遅延対処）
    try:
        await page.wait_for_selector("div.kp-notebook-annotation-container, div.kp-notebook-highlight, #kp-notebook-annotations-asin", timeout=min(timeout, 8000))
    except PlaywrightTimeoutError:
        # 続行して別手段で判定
        pass

    # 1) document.title / page.title()
    try:
        ptitle = norm(await page.title())
        if n_title and (n_title in ptitle or ptitle in n_title):
            return True
    except Exception:
        pass

    # 2) 見出し系セレクタを拡充（h1/h2/h3 と Kindle 固有クラス）
    header_selectors = [
        "div.kp-notebook-header", "h1", "h2", "h3",
        ".kp-notebook-metadata", ".kp-notebook-metadata h3",
        ".kp-notebook-print-override", ".kp-notebook-header h2",
        ".kp-notebook-viewer h1", ".kp-notebook-title",
        "h3.kp-notebook-selectable", ".a-spacing-top-small h3"
    ]
    for hs in header_selectors:
        try:
            loc = page.locator(hs)
            cnt = await loc.count()
            for i in range(min(cnt, 8)):
                try:
                    raw = await loc.nth(i).inner_text()
                except Exception:
                    continue
                t = norm(raw)
                if not t:
                    continue
                # 直接部分一致
                if n_title and (n_title in t or t in n_title):
                    return True
                # トークン一致（閾値: タイトルトークンの半分以上が表示内に含まれる）
                if title_toks:
                    got_toks = token_list(t)
                    common = sum(1 for tok in title_toks if any(tok in g for g in got_toks))
                    if common >= max(1, (len(title_toks) + 1) // 2):
                        return True
        except Exception:
            continue

    # 3) body 全文（範囲を広げる）
    try:
        body_text = norm(await page.locator("body").inner_text())
        if n_title and (n_title in body_text or any(tok in body_text for tok in title_toks)):
            return True
    except Exception:
        pass

    # 4) ハイライト一覧や hidden ASIN があるなら OK（UI上は注釈が見えている）
    try:
        asin = await page.locator("#kp-notebook-annotations-asin").get_attribute("value")
        if asin:
            # 少なくとも注釈コンテナ内にハイライト要素があれば OK と見なす
            try:
                cnt = await page.locator("div.kp-notebook-annotation-container .kp-notebook-highlight, .kp-notebook-highlight").count()
                if cnt and cnt > 0:
                    return True
            except Exception:
                return True
    except Exception:
        pass

    # 5) デバッグ用（必要なら有効化）
    # await page.screenshot(path=f"debug_fail_{int(time.time())}.png")
    # html = await page.content(); open('debug_fail.html','w',encoding='utf-8').write(html)

    return False

async def extract_annotations_for_current_book(page) -> List[Dict]:
        """現在表示されている書籍のハイライトをページ内 JS で抽出して返す"""

        extract_js = r'''
        () => {
            function norm(s){ return (s||"").replace(/\s+/g,' ').trim(); }
            const container = document.querySelector('div.kp-notebook-annotation-container') || document.body;
            const nodeList = container.querySelectorAll('.kp-notebook-annotation, .kp-notebook-highlight, li');
            const results = [];
            nodeList.forEach(n => {
                try {
                    const full = norm(n.innerText || "");
                    if (!full || full.length < 1) return;

                                // 近傍のメタデータ要素から位置情報を探す（例: #annotationHighlightHeader や .kp-notebook-metadata）
                                let location = "";
                                try {
                                    // 1) 祖先ノード内を検索
                                    let anc2 = n;
                                    while (anc2 && anc2 !== document && anc2 !== document.body) {
                                        if (anc2.querySelector) {
                                            const meta = anc2.querySelector('#annotationHighlightHeader, .kp-notebook-metadata');
                                            if (meta && meta.innerText) {
                                                const mm = norm(meta.innerText);
                                                const locM = mm.match(/(位置|Location|Loc|ページ|Page)[:：\s]*([0-9\-–,]+)/i);
                                                if (locM) { location = locM[2].trim(); break; }
                                            }
                                        }
                                        anc2 = anc2.parentElement;
                                    }

                                    // 2) 前方の兄弟要素に metadata があるか探す
                                    if (!location) {
                                        let sib = n.previousElementSibling;
                                        while (sib) {
                                            if ((sib.id && sib.id === 'annotationHighlightHeader') || (sib.classList && sib.classList.contains('kp-notebook-metadata'))) {
                                                const mm = norm(sib.innerText || sib.textContent || "");
                                                const locM = mm.match(/(位置|Location|Loc|ページ|Page)[:：\s]*([0-9\-–,]+)/i);
                                                if (locM) { location = locM[2].trim(); break; }
                                            }
                                            if (sib.querySelector) {
                                                const inside = sib.querySelector('#annotationHighlightHeader, .kp-notebook-metadata');
                                                if (inside && inside.innerText) {
                                                    const mm = norm(inside.innerText);
                                                    const locM = mm.match(/(位置|Location|Loc|ページ|Page)[:：\s]*([0-9\-–,]+)/i);
                                                    if (locM) { location = locM[2].trim(); break; }
                                                }
                                            }
                                            sib = sib.previousElementSibling;
                                        }
                                    }

                                    // 3) フォールバック: 文書内のメタ要素から最も近いものを選ぶ
                                    if (!location) {
                                        const metas = Array.from(document.querySelectorAll('#annotationHighlightHeader, .kp-notebook-metadata')).filter(e => e && e.innerText && /(位置|Location|Loc|ページ|Page)/.test(e.innerText));
                                        if (metas.length) {
                                            let best = null; let bestDist = Infinity;
                                            const nrect = n.getBoundingClientRect ? n.getBoundingClientRect() : {top:0,bottom:0};
                                            metas.forEach(m => {
                                                try {
                                                    const r = m.getBoundingClientRect();
                                                    const dist = Math.abs((r.top + r.bottom)/2 - (nrect.top + nrect.bottom)/2);
                                                    if (dist < bestDist) { bestDist = dist; best = m; }
                                                } catch (e) {}
                                            });
                                            if (best && best.innerText) {
                                                const mm = norm(best.innerText);
                                                const locM = mm.match(/(位置|Location|Loc|ページ|Page)[:：\s]*([0-9\-–,]+)/i);
                                                if (locM) location = locM[2].trim();
                                            }
                                        }
                                    }
                                } catch (e) {
                                    // ignore
                                }

                                            // 最終フォールバック: ノード自身のテキストに位置情報が含まれているか確認
                                            if (!location) {
                                                const locM2 = full.match(/(位置|Location|Loc|ページ|Page)[:：\s]*([^\n|\|]+)/i);
                                                if (locM2) location = locM2[2].trim();
                                            }

                                            // 位置文字列を正規化して数値部分のみを取り出す（例: '位置: 114' -> '114'）
                                            try {
                                                if (location) {
                                                    // remove non-numeric leading/trailing characters except range/delimiters
                                                    const m = location.match(/([0-9]+(?:[\-–,][0-9]+)*)/);
                                                    if (m) location = m[1]; else location = location.replace(/[^0-9\-–,]/g,'').trim();
                                                }
                                            } catch (e) {
                                                // ignore
                                            }

                    // メモ（Note）抽出
                    const noteM = full.match(/(Note|メモ|注釈)[:：\s]*([^\n]+)/i);
                    const note = noteM ? noteM[2].trim() : "";

                    // セクション見出しを祖先から取得
                    let section = "";
                    let anc = n;
                    while (anc && anc !== document.body) {
                        if (/H[1-6]/i.test(anc.tagName)) { section = norm(anc.innerText); break; }
                        anc = anc.parentElement;
                    }

                    // ハイライト本文は full から位置・メモ表記を取り除く
                    let highlight = full;
                    if (location) highlight = highlight.replace(location, "");
                    if (note) highlight = highlight.replace(note, "");
                    highlight = highlight.replace(/(位置|Location|Loc|ページ|Page)[:：]*/ig, '');
                    highlight = highlight.replace(/(Note|メモ|注釈)[:：]*/ig, '');
                    highlight = highlight.replace(/\|/g,' ');
                    highlight = highlight.replace(/\s+/g,' ').trim();

                    results.push({section, location, highlight, note});
                } catch (e) {
                    // 個別要素の解析失敗は無視
                }
            });
            const seen = new Set();
            const uniq = [];
            for (const r of results) {
                const key = (r.highlight||"").slice(0,300);
                if (!key || seen.has(key)) continue;
                seen.add(key);
                uniq.push(r);
            }
            return uniq;
        }
        '''

        try:
                items = await page.evaluate(extract_js)
                normalized = []
                for it in items:
                        normalized.append({
                                "section": normalize_whitespace(it.get("section", "")),
                                "location": normalize_whitespace(it.get("location", "")),
                                "highlight": normalize_whitespace(it.get("highlight", "")),
                                "note": normalize_whitespace(it.get("note", "")),
                        })
                return normalized
        except Exception:
                return []

async def main(args):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(USER_DATA_DIR, headless=not args.headful,
                                                             viewport={"width":1200,"height":900})
        page = await context.new_page()
        print("Opening:", BASE_URL)
        await page.goto(BASE_URL)
        if args.headful:
            input("ヘッドフルモード: ブラウザで Amazon にログイン後、Enter を押してください...")

        try:
            await page.wait_for_selector("a", timeout=DEFAULT_TIMEOUT)
        except PlaywrightTimeoutError:
            print("左一覧の要素が見つかりません。ページ構造が変わっている可能性があります。")
            await context.close()
            return

        titles = await get_candidate_titles(page)
        if not titles:
            print("書籍候補が検出できませんでした。")
            await context.close()
            return

        print(f"検出した書籍数: {len(titles)} 件（上限 500 件）")
        titles = titles[:500]

        # 出力先ファイルを事前に決め、既存の CSV から処理済みの書籍を読み取って続行可能にする
        path = args.output
        seen = set()
        write_header = True
        if os.path.exists(path) and os.path.getsize(path) > 0:
            try:
                with open(path, "r", newline="", encoding="utf-8-sig") as rf:
                    reader = csv.reader(rf)
                    header = next(reader, None)
                    # 既存行から Book 列を取得（ヘッダがあることを期待）
                    book_idx = 0
                    if header:
                        # try to find Book column index
                        for i, h in enumerate(header):
                            if h and h.strip().lower().startswith("book"):
                                book_idx = i
                                break
                    for row in reader:
                        try:
                            b = row[book_idx]
                        except Exception:
                            b = row[0] if row else ""
                        if b:
                            seen.add(normalize_whitespace(b))
                write_header = False
            except Exception:
                # 読み込み失敗でも続行（既存ファイルが壊れている可能性がある）
                seen = set()
                write_header = True

        # 出力ファイルを追記モードで開いて、各書籍処理後に追記する
        try:
            out_f = open(path, "a", newline="", encoding="utf-8-sig")
        except Exception:
            print(f"出力ファイルを開けません: {path}")
            await context.close()
            return
        writer = csv.writer(out_f)
        if write_header:
            writer.writerow(["Book", "Section", "Location", "Highlight", "Note"]) 
            out_f.flush()
            try:
                os.fsync(out_f.fileno())
            except Exception:
                pass

        for idx, title in enumerate(titles, start=1):
            if normalize_whitespace(title) in seen:
                print(f"[{idx}/{len(titles)}] スキップ済み: {title}")
                continue
            print(f"[{idx}/{len(titles)}] 処理中: {title}")
            # safe_click_and_wait を使用してコンソールエラーやハングを回避しつつクリック
            ok = await safe_click_and_wait(page, title, click_book_by_title, wait_for_book_context, timeout=DEFAULT_TIMEOUT, max_reloads=2)
            if not ok:
                print("  -> クリック/検出に失敗しました（スキップ）")
                try:
                    await page.goto(BASE_URL)
                    await page.wait_for_selector("a", timeout=10000)
                except Exception:
                    pass
                continue

            # ここから：コンテキスト検出前に少し待ち、複数回リトライする
            ctx_ok = False
            for attempt_ctx in range(3):
                # 試行ごとに待機を増やす（0.5s, 1.0s, 1.5s）
                await asyncio.sleep(0.5 * (attempt_ctx + 1))
                # 非同期読み込みがあれば完了を待う（失敗しても無視）
                try:
                    await page.wait_for_load_state('networkidle', timeout=3000)
                except Exception:
                    pass
                try:
                    ctx_ok = await wait_for_book_context(page, title, timeout=15000)
                except Exception:
                    ctx_ok = False
                if ctx_ok:
                    break
                # 次の試行前に短く待機
                await asyncio.sleep(0.6)

            if not ctx_ok:
                print("  -> 対象書籍のコンテキスト検出に失敗しました（スキップ）")
                try:
                    await page.goto(BASE_URL)
                    await page.wait_for_selector("a", timeout=10000)
                except Exception:
                    pass
                continue
            items = await extract_annotations_for_current_book(page)
            print(f"  -> 抽出件数: {len(items)}")
            # 一冊分を即時追記
            for it in items:
                try:
                    writer.writerow([title, it["section"], it["location"], it["highlight"], it["note"]])
                except Exception:
                    # 保険: 文字列化して書き込む
                    writer.writerow([str(title), str(it.get("section","")), str(it.get("location","")), str(it.get("highlight","")), str(it.get("note",""))])
            out_f.flush()
            try:
                os.fsync(out_f.fileno())
            except Exception:
                pass
            seen.add(normalize_whitespace(title))
            try:
                await page.goto(BASE_URL)
                await page.wait_for_selector("a", timeout=10000)
            except Exception:
                await asyncio.sleep(1.0)

        out_f.close()
        print(f"処理が完了しました。出力ファイル: {path}")
        await context.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Kindle highlights per book (scroll + click).")
    parser.add_argument("--headful", action="store_true", help="Open browser so you can login interactively.")
    parser.add_argument("--output", "-o", default="highlights.csv", help="CSV output path")
    args = parser.parse_args()
    asyncio.run(main(args))
