# inspect_dom.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://read.amazon.co.jp/notebook/"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()
        print(f"Opening: {url}")
        await page.goto(url)

        print("ログイン後に Enter を押してください...")
        input()

        # ページの主要なノードを調べる
        html = await page.content()
        print("=== ページタイトル ===")
        print(await page.title())

        print("=== 主要なdivクラス一覧 ===")
        div_classes = await page.eval_on_selector_all("div", "els => els.map(e => e.className).filter(c => c)")
        unique_classes = sorted(set(div_classes))
        for cls in unique_classes[:50]:  # 長すぎないように50件まで
            print(cls)

        print("=== aタグ内テキスト（抜粋） ===")
        links = await page.eval_on_selector_all("a", "els => els.map(e => e.textContent.trim()).filter(t => t)")
        for link in links[:30]:
            print("-", link)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
