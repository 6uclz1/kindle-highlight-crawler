import os
import csv
import time
import requests
from playwright.sync_api import sync_playwright
from pathlib import Path

ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / '_out' / "books.csv"
SESSION_FILE = ROOT / 'user_data' / 'my-kindle-scraper-session.json'
DEBUG_HTML_PATH = ROOT / '_out' / 'my-kindle-scraper-debug.html'

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        viewport_size = {'width': 1920*2, 'height': 1080*2}
        if os.path.exists(SESSION_FILE):
            context = browser.new_context(storage_state=str(SESSION_FILE), viewport=viewport_size)
        else:
            context = browser.new_context(viewport=viewport_size)

        page = context.new_page()
        page.goto("https://read.amazon.co.jp/kindle-library")

        if not os.path.exists(SESSION_FILE):
            print("👉 Amazonにログインしてください...")
            page.wait_for_load_state("networkidle")
            time.sleep(30)
            context.storage_state(path=str(SESSION_FILE))
            print(f"✅ セッションを {SESSION_FILE} に保存しました")

        # ページを下までスクロールして全件読み込み（アイテム数が増えなくなるまで待つ）
        # ページ内でスクロール可能な親要素を探してそこをスクロールし、
        # タイトルを持つ実アイテムの数が増えなくなるまで待つ（JS 実行）
        scroll_js = r'''
        () => {
                const selector = 'ul#cover li[role="listitem"]';
                const sleep = ms => new Promise(res => setTimeout(res, ms));

                function countItems(){
                    return Array.from(document.querySelectorAll(selector)).filter(li=>{
                        const titleNode = li.querySelector('div[id^="title-"] p');
                        return titleNode && titleNode.textContent.trim().length > 0;
                    }).length;
                }

                function findScrollParent(el){
                    let cur = el;
                    while(cur && cur !== document.body){
                        if (cur.scrollHeight > cur.clientHeight) return cur;
                        cur = cur.parentElement;
                    }
                    return window;
                }

                return new Promise(async (resolve) => {
                    const list = document.querySelector('ul#cover');
                    const scroller = list ? findScrollParent(list) : window;
                    let prev = -1;
                    let stable = 0;
                    const maxRounds = 200;
                    for (let i = 0; i < maxRounds; i++) {
                        if (scroller === window) {
                            window.scrollTo(0, document.body.scrollHeight);
                        } else {
                            scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'auto' });
                        }
                        // 読み込み待ち
                        await sleep(1000);
                        const c = countItems();
                        if (c !== prev) {
                            prev = c;
                            stable = 0;
                        } else {
                            stable += 1;
                        }
                        // 連続して同じ件数が3回続いたら完了とみなす（余裕を持たせる）
                        if (stable >= 3) break;
                        // 少しだけ追加待機して確実に読み込みを反映
                        await sleep(400);
                    }
                    resolve(prev);
                });
            }
        '''
    
        try:
            page.evaluate(scroll_js)
            page.wait_for_selector("ul#cover li[role='listitem']", timeout=60000)
        except Exception:
            # JS 実行や待機に失敗しても処理を継続させる
            pass

        # JSで書籍データを直接抽出
        extract_js = r'''
        () => {
            function norm(s){ return (s||"").replace(/\s+/g,' ').trim(); }
                const results = [];
                const items = document.querySelectorAll('ul#cover li[role="listitem"]');
                items.forEach(li => {
                    const titleNode = li.querySelector('div[id^="title-"] p');
                    const authorNode = li.querySelector('div[id^="author-"] p');
                    const imgNode = li.querySelector('img[id^="cover-"]');

                    const title = norm(titleNode ? titleNode.textContent : "");
                    const author = norm(authorNode ? authorNode.textContent : "");
                    const img = imgNode ? imgNode.src : "";

                    if (title) {
                        results.push({title, author, img});
                    }
                });
                return results;
            }
        '''
        books = page.evaluate(extract_js)
        print("✅ ブラウザ内で抽出した件数:", len(books))

        with open(DEBUG_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(page.content())
        browser.close()
            
    # CSV 書き込み
    rows = []
    for b in books:
        title, author = b["title"], b["author"]
        rows.append([title, author])

    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Author"])
        writer.writerows(rows)

    print(f"✅ 書籍一覧を {CSV_PATH} に保存しました（{len(rows)} 件）")

if __name__ == "__main__":
    main()
