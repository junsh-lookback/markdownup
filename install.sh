#!/bin/bash
# markdownup インストールスクリプト
# .txt拡張子を避けるため、依存パッケージを直接インストールし、
# python -m markdownup で直接使用する方法を採用します

echo "=========================================="
echo "markdownup セットアップ"
echo "=========================================="

# 依存パッケージをインストール
echo "[1/2] 依存パッケージをインストール中..."
python -m pip install --user markdown pygments

if [ $? -ne 0 ]; then
    echo "[エラー] 依存パッケージのインストールに失敗しました"
    exit 1
fi

# セットアップ完了
echo "[2/2] セットアップ完了"
echo ""
echo "=========================================="
echo "使用方法:"
echo "=========================================="
echo "  python -m markdownup              # ヘルプを表示"
echo "  python -m markdownup --start      # サービスを起動"
echo "  python -m markdownup --stop       # サービスを停止"
echo ""
echo "便利なエイリアスを追加するには、以下を ~/.bashrc に追加してください:"
echo "  alias markdownup='python -m markdownup'"
echo "=========================================="
