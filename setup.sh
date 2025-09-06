# 依存関係をインストール
uv sync

# playwright のブラウザをインストール
uv run playwright install

echo "✅ セットアップ完了"
echo "次のコマンドで実行できます:"
echo "uv run python export_kindle_highlights/main.py --headful --output highlights.csv"
