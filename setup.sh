# 必要ライブラリをインストール
uv add playwright beautifulsoup4 tqdm

# playwright のブラウザをインストール
uv run playwright install

echo "✅ セットアップ完了"
echo "次のコマンドで実行できます:"
echo "uv run python export_kindle_highlights.py --headful --output highlights.csv"
