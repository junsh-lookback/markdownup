# -*- coding: utf-8 -*-
"""定数定義とmarkdownライブラリの利用可能性チェック"""

from pathlib import Path

# デフォルト設定
DEFAULT_PORT = 8000
FALLBACK_PORTS = [8001, 8080, 8888, 9000, 3000]
PID_BASE_DIR = Path.home() / '.markdownup'
PID_INSTANCES_DIR = PID_BASE_DIR / 'instances'
LATEST_PID_FILE = PID_BASE_DIR / 'latest_port'

# Markdownライブラリの利用可能性チェック
try:
    import markdown  # noqa: F401
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
