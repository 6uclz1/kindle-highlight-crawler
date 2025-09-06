# Kindle Highlight Export (kindle-highlight-crawler)

## 概要
このリポジトリは、Amazon Kindle の "ノートブック"（ハイライト／メモ）をブラウザ自動操作で取得し、CSV に出力するための試作ツール群です。主に Playwright を使ってブラウザ操作を行い、ページ内の DOM からハイライトを抽出します。

> 目的: ローカル環境で自分の Kindle ハイライトをスクレイピングしてローカル CSV に保存するための補助ツール。


## プロジェクト構造
各スクリプトは、その処理内容を示すディレクトリに分かれています。

- `scrape-notebook-highlight-to-csv/`: KindleのノートブックからハイライトをCSV形式で抽出するスクリプト
- `scrape-library-booklist-to-csv/`: Kindleライブラリから書籍一覧をCSV形式で抽出するスクリプト
- `format-highlights-csv-to-json/`: ハイライトのCSVをJSON形式に変換するスクリプト
- `format-highlights-csv-to-min-json/`: ハイライトのCSVを最小化されたJSON形式に変換するスクリプト
- `debug-notebook-dom/`: ノートブックページのDOM構造を調査するためのデバッグ用スクript
- `analyze-highlights-csv-to-report/`: ハイライトのCSVデータを分析し、レポートを生成するスクリプト
- `user_data/`: ブラウザのユーザーデータ（プロファイル）を置くディレクトリ
- `_out/`: 出力ファイルが保存されるディレクトリ
- `setup.sh`: 環境セットアップを自動化するシェルスクリプト
- `pyproject.toml`, `uv.lock`: パッケージ仕様・ロックファイル


## 前提・必要環境
- macOS または Linux/Windows に Python 3.13 以上
- `uv`（uv パッケージ／実行環境）を使った開発フローを想定しています。リポジトリ内の `setup.sh` は `uv` を利用します。
- Playwright（ブラウザ自動化）と Playwright のブラウザバイナリ

ローカルに `uv` をインストールしていない場合は、プロジェクト方針に合わせて `pip` 環境や venv を使っても構いません。


## セットアップ（推奨）
リポジトリルートで以下を実行します（`setup.sh` に自動化済み）：

```bash
# 実行権限がない場合は事前に chmod +x setup.sh
./setup.sh
```

`setup.sh` は以下を行います（要 `uv`）：
- `pyproject.toml` に基づいて依存関係をインストール (`uv sync`)
- Playwright のブラウザをインストール

手動の場合の要点:
- Python 環境を有効にする（venv など）
- 依存をインストール: `uv sync`
- Playwright のブラウザをインストール: `uv run playwright install`


## 実行例
各スクリプトは、プロジェクトのルートディレクトリから実行します。

- **Kindleハイライトのエクスポート:**
  ```bash
  uv run python scrape_notebook_highlight_to_csv/main.py --headful --output _out/highlights.csv
  ```

- **Kindleライブラリの書籍一覧をエクスポート:**
  ```bash
  uv run python scrape_library_booklist_to_csv/main.py
  ```

- **CSVをJSONに変換:**
  ```bash
  uv run python format_highlights_csv_to_json/main.py
  ```

- **DOM構造の調査:**
  ```bash
  uv run python debug_notebook_dom/main.py
  ```

- **ハイライトデータのプロファイリング:**
  ```bash
  uv run python analyze_highlights_csv_to_report/main.py
  ```

- **Obsidian形式へのエクスポート:**
  ```bash
  uv run python export_highlights_to_obsidian/main.py
  ```

注: 上のコマンドは `uv` を使う想定です。`uv` を使わない場合は、仮想環境を有効にして `python <スクリプトパス>` のように実行してください。


## 動作の流れ（大まか）
1. Playwright で `https://read.amazon.co.jp/notebook/` を開く
2. ログイン（必要に応じて手動で行う）
3. 左ペインの書籍一覧をスクロールして目的の書籍を可視化
4. 書籍をクリックして注釈（ハイライト）コンテキストを読み込む
5. ページ内のハイライト情報を抽出して CSV 出力


## 設計・開発メモ
- `scrape-notebook-highlight-to-csv/main.py` は非同期 Playwright コードで実装されています。SPA（Single Page Application）の遅延読み込みや、UI の微妙な DOM 変化に耐えるため、可視化→クリック→待機のロジックを持たせています。
- スクリプトはまだ開発中で、エッジケース（大量の書籍、遅延、要素の変化）で調整が必要です。


## プライバシー・安全性
- `user_data/` にブラウザのプロフィール（Cookie・セッション）が保存されます。これによりログイン状態を再利用できますが、個人情報が含まれるため絶対に公開リポジトリに含めないでください。本リポジトリの `.gitignore` で除外済みです。
- スクレイピングは Amazon の利用規約に従って行ってください。個人的なバックアップ用途に限定することを推奨します。


## トラブルシューティング
- Playwright がブラウザを見つけない／起動しない: `uv run playwright install` を実行してブラウザをインストールしてください。
- ログインが必要なページで自動ログインが機能しない場合は、ヘッドフルモードで手動ログインしてから続行してください。
- 権限エラーや profile 関連の競合が出た場合は、`user_data/` をクリアして再作成してください（個人データはバックアップしてから）。


## コントリビューション
小さな修正や改善は歓迎します。まず issue を立てるか、簡単な PR を送ってください。大きな設計変更がある場合は事前に相談してください。


## ライセンスと著作権
リポジトリに明示的なライセンスファイルがない場合は、利用者間で合意したライセンスを追加してください。内部利用であれば慣例に従ってください。
