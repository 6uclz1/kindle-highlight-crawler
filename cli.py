
"""Kindleハイライトクローラーのコマンドラインインターフェース。

このスクリプトは、プロジェクト内の各機能を実行するための統一された
コマンドラインインターフェース（CLI）を提供します。

argparseを利用してサブコマンドベースのインターフェースを構築しており、
以下の機能を提供します。
- Kindleハイライトのスクレイピング (`scrape-highlights`)
- Kindleライブラリの書籍リストのスクレイピング (`scrape-library`)
- ハイライトCSVのJSON形式への変換 (`format-json`)
- ハイライトCSVの分析とレポート生成 (`analyze`)
- ノートブックページのDOM構造のデバッグ (`debug-dom`)
- Obsidianへのエクスポート (`export-to-obsidian`)
"""

import argparse
import asyncio
import sys
from pathlib import Path

# --- パス設定 ---
# 各スクリプトのディレクトリをPythonパスに追加します。
# これにより、各ディレクトリ内の `main.py` をモジュールとしてインポートできます。
ROOT = Path(__file__).parent
sys.path.append(str(ROOT / 'scrape_notebook_highlight_to_csv'))
sys.path.append(str(ROOT / 'scrape_library_booklist_to_csv'))
sys.path.append(str(ROOT / 'format_highlights_csv_to_json'))
sys.path.append(str(ROOT / 'analyze_highlights_csv_to_report'))
sys.path.append(str(ROOT / 'debug_notebook_dom'))
sys.path.append(str(ROOT / 'export_highlights_to_obsidian'))

# --- メインスクリプトのインポート ---
# 各スクリプトのmain関数を、別名でインポートします。
# これにより、CLIの各サブコマンドから対応するスクリプトの処理を呼び出せます。
from scrape_notebook_highlight_to_csv import main as scrape_highlights_main
from scrape_library_booklist_to_csv import main as scrape_library_main
from format_highlights_csv_to_json import main as format_json_main
from analyze_highlights_csv_to_report import main as analyze_main
from debug_notebook_dom import main as debug_dom_main
from export_highlights_to_obsidian import main as export_to_obsidian_main


def run_scrape_highlights(args: argparse.Namespace) -> None:
    """Kindleのハイライトをスクレイピングするコマンドを実行します。

    `scrape_notebook_highlight_to_csv` ディレクトリの `main` 関数を呼び出します。
    この関数は非同期で実行されるため、 `asyncio.run` を使用します。

    Args:
        args (argparse.Namespace): argparseによってパースされたコマンドライン引数。
                                   `headful` と `output` 属性を持ちます。
                                   型: argparse.Namespace (名前空間)
    """
    print("Kindleハイライトのスクレイピングを開始します...")
    # scrape_highlights_main.main は非同期関数のため asyncio.run で実行
    asyncio.run(scrape_highlights_main.main(args))
    print("スクレイピングが完了しました。")


def run_scrape_library(args: argparse.Namespace) -> None:
    """Kindleライブラリの書籍リストをスクレイピングするコマンドを実行します。

    `scrape_library_booklist_to_csv` ディレクトリの `main` 関数を呼び出します。

    Args:
        args (argparse.Namespace): argparseによってパースされたコマンドライン引数。
                                   このコマンドでは使用されません。
                                   型: argparse.Namespace (名前空間)
    """
    print("Kindleライブラリの書籍リストのスクレイピングを開始します...")
    scrape_library_main.main()
    print("スクレイピングが完了しました。")


def run_format_json(args: argparse.Namespace) -> None:
    """ハイライトのCSVファイルをJSON形式に変換するコマンドを実行します。

    `format_highlights_csv_to_json` ディレクトリの `main` 関数を呼び出します。

    Args:
        args (argparse.Namespace): argparseによってパースされたコマンドライン引数。
                                   このコマンドでは使用されません。
                                   型: argparse.Namespace (名前空間)
    """
    print("ハイライトCSVのJSONへの変換を開始します...")
    format_json_main.main()
    print("変換が完了しました。")


def run_analyze(args: argparse.Namespace) -> None:
    """ハイライトのCSVファイルを分析し、レポートを生成するコマンドを実行します。

    `analyze_highlights_csv_to_report` ディレクトリの `main` 関数を呼び出します。

    Args:
        args (argparse.Namespace): argparseによってパースされたコマンドライン引数。
                                   このコマンドでは使用されません。
                                   型: argparse.Namespace (名前空間)
    """
    print("ハイライトCSVの分析とレポート生成を開始します...")
    analyze_main.main()
    print("分析が完了しました。")


def run_debug_dom(args: argparse.Namespace) -> None:
    """KindleのノートブックページのDOMをデバッグするコマンドを実行します。

    `debug_notebook_dom` ディレクトリの `main` 関数を呼び出します。
    この関数は非同期で実行されるため、 `asyncio.run` を使用します。

    Args:
        args (argparse.Namespace): argparseによってパースされたコマンドライン引数。
                                   このコマンドでは使用されません。
                                   型: argparse.Namespace (名前空間)
    """
    print("DOMのデバッグを開始します...")
    # debug_dom_main.main は非同期関数のため asyncio.run で実行
    asyncio.run(debug_dom_main.main())
    print("デバッグが完了しました。")


def run_export_to_obsidian(args: argparse.Namespace) -> None:
    """Obsidianへのエクスポートを実行します。

    `export_highlights_to_obsidian` ディレクトリの `main` 関数を呼び出します。

    Args:
        args (argparse.Namespace): argparseによってパースされたコマンドライン引数。
                                   `input` と `output` 属性を持ちます。
                                   型: argparse.Namespace (名前空間)
    """
    print("Obsidianへのエクスポートを開始します...")
    export_to_obsidian_main.export_to_obsidian(args.input, args.output)
    print("エクスポートが完了しました。")


def main() -> None:
    """CLIアプリケーションのエントリーポイント。

    argparseを使用してコマンドライン引数を解析し、
    対応するサブコマンドの関数を実行します。
    """
    # --- パーサーのセットアップ ---
    parser = argparse.ArgumentParser(
        description="KindleハイライトクローラーのCLIツール",
        epilog="各コマンドの詳細は `COMMAND --help` で確認できます。"
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help="実行するコマンド")

    # --- `scrape-highlights` コマンドの定義 ---
    parser_scrape_highlights = subparsers.add_parser(
        'scrape-highlights',
        help='Kindleノートブックからハイライトをスクレイピングします。',
        description='KindleのWebサイトにログインし、指定された書籍のハイライトをCSVファイルに出力します。'
    )
    parser_scrape_highlights.add_argument(
        '--headful',
        action='store_true',
        help='ブラウザをGUIモードで実行します。ログイン操作を手動で行う場合に便利です。'
    )
    parser_scrape_highlights.add_argument(
        '--output',
        default='_out/highlights.csv',
        help='出力先のCSVファイルパス。 (デフォルト: _out/highlights.csv)'
    )
    parser_scrape_highlights.set_defaults(func=run_scrape_highlights)

    # --- `scrape-library` コマンドの定義 ---
    parser_scrape_library = subparsers.add_parser(
        'scrape-library',
        help='Kindleライブラリから書籍リストをスクレイピングします。',
        description='Kindleライブラリページにアクセスし、所有している書籍の一覧をCSVファイルに出力します。'
    )
    parser_scrape_library.set_defaults(func=run_scrape_library)

    # --- `format-json` コマンドの定義 ---
    parser_format_json = subparsers.add_parser(
        'format-json',
        help='ハイライトCSVをJSON形式に変換します。',
        description='`scrape-highlights`で生成されたCSVファイルを読み込み、書籍ごとにグループ化されたJSONファイルを出力します。'
    )
    parser_format_json.set_defaults(func=run_format_json)

    # --- `analyze` コマンドの定義 ---
    parser_analyze = subparsers.add_parser(
        'analyze',
        help='ハイライトCSVを分析し、レポートを生成します。',
        description='ハイライトの統計情報（書籍ごとの件数、文字数など）を分析し、テキストファイル形式のレポートを生成します。'
    )
    parser_analyze.set_defaults(func=run_analyze)

    # --- `debug-dom` コマンドの定義 ---
    parser_debug_dom = subparsers.add_parser(
        'debug-dom',
        help='ノートブックページのDOM構造をデバッグ出力します。',
        description='開発者向け。KindleノートブックページのDOM構造をコンソールに出力し、セレクタの確認などに使用します。'
    )
    parser_debug_dom.set_defaults(func=run_debug_dom)

    # --- `export-to-obsidian` コマンドの定義 ---
    parser_export_to_obsidian = subparsers.add_parser(
        'export-to-obsidian',
        help='ハイライトをObsidian形式のMarkdownファイルにエクスポートします。',
        description='書籍ごとにMarkdownファイルを作成し、ハイライトを書き出します。'
    )
    parser_export_to_obsidian.add_argument(
        '--input',
        default='_out/highlights.csv',
        help='入力元のCSVファイルパス。 (デフォルト: _out/highlights.csv)'
    )
    parser_export_to_obsidian.add_argument(
        '--output',
        default='_out/obsidian',
        help='出力先のディレクトリパス。 (デフォルト: _out/obsidian)'
    )
    parser_export_to_obsidian.set_defaults(func=run_export_to_obsidian)

    # --- 引数の解析と実行 ---
    args = parser.parse_args()
    if hasattr(args, 'func'):
        # `set_defaults` で設定された `func` 属性（実行する関数）を呼び出す
        args.func(args)
    else:
        # サブコマンドが指定されなかった場合（通常は `required=True` で発生しない）
        parser.print_help()


if __name__ == '__main__':
    main()
