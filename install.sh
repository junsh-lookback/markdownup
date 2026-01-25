#!/bin/bash
# markdownup インストールスクリプト
# .txt拡張子を避けるため、依存パッケージを直接インストールし、
# スクリプトを直接使用する方法を採用します

echo "=========================================="
echo "markdownup セットアップ"
echo "=========================================="

# 依存パッケージをインストール
echo "[1/3] 依存パッケージをインストール中..."
python -m pip install --user markdown pygments

if [ $? -ne 0 ]; then
    echo "[エラー] 依存パッケージのインストールに失敗しました"
    exit 1
fi

# markdownup.py を実行可能にする
echo "[2/3] スクリプトを設定中..."
chmod +x markdownup.py 2>/dev/null || true

# エイリアスまたはシンボリックリンクの作成を提案
echo "[3/3] セットアップ完了"
echo ""
echo "=========================================="
echo "使用方法:"
echo "=========================================="
echo "  python markdownup.py --help"
echo "  python markdownup.py -d ./"
echo ""
echo "便利なエイリアスを追加するには、以下を ~/.bashrc に追加してください:"
echo "  alias markdownup='python $(pwd)/markdownup.py'"
echo ""
echo "または、パスにシンボリックリンクを作成:"
echo "  ln -s $(pwd)/markdownup.py ~/.local/bin/markdownup"
echo "=========================================="


