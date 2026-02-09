#!/bin/bash
# markdownup インストールスクリプト（Linux/macOS 向け）
#
# 方法1: pip install --user . を試行
# 方法2: 失敗した場合は依存パッケージのみインストールし、
#         python -m markdownup で使用する方法にフォールバック

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "markdownup セットアップ"
echo "=========================================="

# --- 方法1: pip install --user . ---
echo ""
echo "[1/2] pip install --user . を実行中..."
pip install --user "$SCRIPT_DIR" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "[2/2] セットアップ完了（pip install 成功）"
    echo ""
    echo "=========================================="
    echo "使用方法:"
    echo "=========================================="
    echo "  markdownup              # ヘルプを表示"
    echo "  markdownup --start      # サービスを起動"
    echo "  markdownup --stop       # サービスを停止"
    echo ""
    echo "アンインストール:"
    echo "  pip uninstall markdownup"
    echo "=========================================="
    exit 0
fi

# --- 方法2: フォールバック ---
echo ""
echo "[!] pip install に失敗しました。依存パッケージのみインストールします。"
echo ""
echo "[1/2] 依存パッケージをインストール中..."
python -m pip install --user markdown pygments

if [ $? -ne 0 ]; then
    echo "[エラー] 依存パッケージのインストールに失敗しました"
    exit 1
fi

echo "[2/2] セットアップ完了（フォールバック）"
echo ""
echo "=========================================="
echo "使用方法（プロジェクトディレクトリで実行）:"
echo "=========================================="
echo "  cd $SCRIPT_DIR"
echo "  python -m markdownup              # ヘルプを表示"
echo "  python -m markdownup --start      # サービスを起動"
echo "  python -m markdownup --stop       # サービスを停止"
echo ""
echo "どこからでも使うにはエイリアスを ~/.bashrc に追加してください:"
echo "  echo \"alias markdownup='PYTHONPATH=$SCRIPT_DIR:\$PYTHONPATH python -m markdownup'\" >> ~/.bashrc"
echo "  source ~/.bashrc"
echo "=========================================="
