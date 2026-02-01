#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdownビューワーサーバー
UTF-8エンコーディングでMarkdownファイルを配信します

使用例:
    # サーバーを起動（HTMLに変換）
    python markdownup.py
    
    # 特定のディレクトリをルートとして起動
    python markdownup.py --directory /path/to/docs
    python markdownup.py --header
    
    # サービス停止
    python markdownup.py --stop

    # サービス起動（バックグラウンド）
    python markdownup.py --start
    python markdownup.py --start --port 8080
    python markdownup.py --start -d ~/Documents/notes -p 8080 --header
    
    # 最適な表示を得るには
    pip install markdown pygments
"""

import http.server
import socketserver
import socket
from pathlib import Path
import urllib.parse
import argparse
import sys
import os
import signal
import re
import importlib.util

def githubish_slugify(value: str, separator: str = "-") -> str:
    """
    見出し文字列から安全なアンカーIDを生成する。
    - ASCII文字（a-z, 0-9）とハイフンのみを保持
    - 日本語や記号は除去または置換
    - 例: "5.5 ES10a Functions（IPA ⇔ eUICC の ISD-R）" -> "5-5-es10a-functions-ipa-euicc-isd-r"
    """
    import unicodedata
    # 小文字化して前後の空白を削除
    v = (value or "").strip().lower()
    # 日本語などのUnicodeを正規化してASCIIに近い形にする（可能な場合）
    # ただし、今回は「文字化けしない文字」を目指すため、非ASCIIは基本的に除去
    
    # 記号をスペースに置換
    v = re.sub(r"[()（）【】\[\]<>:;,/\\\\.．・⇔<=>+]", " ", v)
    
    # 非ASCII文字（日本語など）を除去
    v = "".join(c for c in v if ord(c) < 128)
    
    # 英数字以外をセパレータに置換
    v = re.sub(r"[^a-z0-9]+", separator, v)
    
    # 連続するセパレータを1つにまとめ、前後のセパレータを削除
    v = re.sub(re.escape(separator) + r"{2,}", separator, v).strip(separator)
    
    return v

try:
    import markdown
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.toc import TocExtension
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.nl2br import Nl2BrExtension
    from markdown.extensions.sane_lists import SaneListExtension
    from markdown.extensions.attr_list import AttrListExtension
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# デフォルト設定
DEFAULT_PORT = 8000
FALLBACK_PORTS = [8001, 8080, 8888, 9000, 3000]
PID_BASE_DIR = Path.home() / '.markdownup'
PID_INSTANCES_DIR = PID_BASE_DIR / 'instances'
LATEST_PID_FILE = PID_BASE_DIR / 'latest_port'

# HTML テンプレート
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja" style="color-scheme: light;">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.0/github-markdown.min.css">
    <style>
        .markdown-body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
            background-color: #ffffff;
            color: #24292f;
        }}
        @media (max-width: 767px) {{
            .markdown-body {{
                padding: 15px;
            }}
        }}
        body {{
            background-color: #ffffff;
            color: #24292f;
        }}
        /* コードブロックのライトモード強制 */
        .markdown-body pre {{
            background-color: #f6f8fa !important;
            color: #24292f !important;
        }}
        .markdown-body code {{
            background-color: #f6f8fa !important;
            color: #24292f !important;
        }}
        .markdown-body pre code {{
            background-color: transparent !important;
        }}
        /* テーブルのライトモード強制 */
        .markdown-body table {{
            background-color: #ffffff !important;
        }}
        .markdown-body table tr {{
            background-color: #ffffff !important;
            border-top: 1px solid #d0d7de !important;
        }}
        .markdown-body table tr:nth-child(2n) {{
            background-color: #f6f8fa !important;
        }}
        .markdown-body table th,
        .markdown-body table td {{
            background-color: transparent !important;
            color: #24292f !important;
            border: 1px solid #d0d7de !important;
        }}
        .markdown-body table th {{
            background-color: #f6f8fa !important;
        }}
        .file-list {{
            max-width: 980px;
            margin: 45px auto;
            padding: 20px;
        }}
        .file-list h1 {{
            border-bottom: 2px solid #eaecef;
            padding-bottom: 10px;
        }}
        .file-item {{
            display: block;
            padding: 12px 16px;
            margin: 8px 0;
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            text-decoration: none;
            color: #0969da;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .file-item:hover {{
            background-color: #e6f2ff;
            border-color: #0969da;
            transform: translateX(4px);
        }}
        .dir-section {{
            margin: 24px 0;
        }}
        .dir-section h2 {{
            font-size: 1.2rem;
            margin-bottom: 10px;
        }}
        .dir-link {{
            background-color: #eaf3ff;
            border-color: #8ea1df;
        }}
        
        /* 見出しホバー効果（折りたたみ可能な位置を示す） */
        .markdown-body h2:hover,
        .markdown-body h3:hover,
        .markdown-body h4:hover {{
            color: #0969da;
            cursor: default;
        }}
        
        /* ========== 設定ボタン ========== */
        .mdf2h-settings-btn {{
            position: fixed;
            top: 20px;
            left: 20px;
            padding: 8px 16px;
            font-size: 14px;
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            cursor: pointer;
            z-index: 1000;
            transition: all 0.2s;
        }}
        .mdf2h-settings-btn:hover {{
            background-color: #e6f2ff;
            border-color: #0969da;
        }}
        
        /* ========== 設定ダイアログ ========== */
        .mdf2h-settings-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 2000;
        }}
        .mdf2h-settings-overlay.show {{
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .mdf2h-settings-dialog {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 24px;
            min-width: 320px;
            max-width: 90%;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }}
        .mdf2h-settings-dialog h2 {{
            margin: 0 0 16px 0;
            font-size: 1.2rem;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 8px;
        }}
        .mdf2h-settings-group {{
            margin: 16px 0;
        }}
        .mdf2h-settings-group label {{
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .mdf2h-settings-group .mdf2h-radio-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .mdf2h-settings-group .mdf2h-radio-option {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 6px 8px;
            border-radius: 4px;
            transition: background-color 0.15s;
        }}
        .mdf2h-settings-group .mdf2h-radio-option:hover {{
            background-color: #f6f8fa;
        }}
        .mdf2h-settings-group .mdf2h-radio-option input[type="radio"] {{
            margin: 0;
            cursor: pointer;
        }}
        .mdf2h-settings-group .mdf2h-radio-option span {{
            font-size: 14px;
        }}
        .mdf2h-settings-buttons button {{
            padding: 8px 16px;
            font-size: 14px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .mdf2h-settings-buttons .cancel {{
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
        }}
        .mdf2h-settings-buttons .cancel:hover {{
            background-color: #e6f2ff;
        }}
        .mdf2h-settings-buttons .save {{
            background-color: #0969da;
            border: 1px solid #0969da;
            color: #ffffff;
        }}
        .mdf2h-settings-buttons .save:hover {{
            background-color: #0860ca;
        }}
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true }});

        function decodeHashId(raw) {{
            try {{
                return decodeURIComponent(raw);
            }} catch (e) {{
                return raw;
            }}
        }}

        function scrollToHash() {{
            if (!window.location.hash) return;
            const raw = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : window.location.hash;
            const targetId = decodeHashId(raw);
            const target = document.getElementById(targetId);
            if (target) {{
                target.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }}

        // ========== 自動リロード（更新検知） ==========
        const AUTO_RELOAD_INTERVAL_MS = 2000;
        let autoReloadSig = null;
        let autoReloadTimer = null;

        async function fetchSignature() {{
            const path = window.location.pathname;
            const url = '/__sig__?path=' + encodeURIComponent(path);
            const response = await fetch(url, {{ cache: 'no-store' }});
            if (!response.ok) return null;
            return await response.json();
        }}

        async function initAutoReload() {{
            try {{
                const info = await fetchSignature();
                if (!info || !info.exists) return;
                autoReloadSig = info.sig;
                if (autoReloadTimer) clearInterval(autoReloadTimer);
                autoReloadTimer = setInterval(async () => {{
                    try {{
                        const now = await fetchSignature();
                        if (!now || !now.exists) return;
                        if (autoReloadSig !== null && now.sig !== autoReloadSig) {{
                            location.reload();
                        }}
                    }} catch (e) {{
                        // ignore
                    }}
                }}, AUTO_RELOAD_INTERVAL_MS);
            }} catch (e) {{
                // ignore
            }}
        }}

        // ページ読み込み後、複数のタイミングで試行
        window.addEventListener('load', () => {{
            scrollToHash();
            // Mermaid等の遅延レンダリングに対応
            setTimeout(scrollToHash, 100);
            setTimeout(scrollToHash, 500);
            setTimeout(scrollToHash, 1000);
            initAutoReload();
        }});
        window.addEventListener('hashchange', scrollToHash);
        
        // ========== ナビゲーションショートカット ==========
        let navInfo = null;
        
        async function loadNavInfo() {{
            try {{
                const currentPath = window.location.pathname;
                const response = await fetch('/__nav__?path=' + encodeURIComponent(currentPath));
                if (response.ok) {{
                    navInfo = await response.json();
                }}
            }} catch (e) {{
                console.warn('Failed to load nav info:', e);
            }}
        }}
        
        function navigateToParent() {{
            if (navInfo && navInfo.parent) {{
                window.location.href = navInfo.parent;
            }}
        }}
        
        // ========== フォーカス移動機能 ==========
        let focusableElements = [];
        let currentFocusIndex = -1;
        
        function initFocusableElements() {{
            focusableElements = Array.from(document.querySelectorAll('a[href], button, .file-item'));
            currentFocusIndex = -1;
        }}
        
        function focusNext() {{
            if (focusableElements.length === 0) return;
            currentFocusIndex = (currentFocusIndex + 1) % focusableElements.length;
            focusableElements[currentFocusIndex].focus();
            focusableElements[currentFocusIndex].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
        
        function focusPrev() {{
            if (focusableElements.length === 0) return;
            currentFocusIndex = currentFocusIndex <= 0 ? focusableElements.length - 1 : currentFocusIndex - 1;
            focusableElements[currentFocusIndex].focus();
            focusableElements[currentFocusIndex].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
        
        // ========== キーボードショートカット ==========
        document.addEventListener('keydown', (e) => {{
            // Ctrl+Alt+A: ルートへ移動
            if (e.ctrlKey && e.altKey && !e.shiftKey && (e.key === 'a' || e.key === 'A')) {{
                e.preventDefault();
                window.location.href = '/';
                return;
            }}
            
            // Ctrl+Shift+↑: 親ディレクトリへ移動（Windowsでは Ctrl+Alt+↑ がシステムに取られるため代替）
            if (e.ctrlKey && e.shiftKey && !e.altKey && e.key === 'ArrowUp') {{
                e.preventDefault();
                navigateToParent();
                return;
            }}
            
            // Ctrl+Alt+↑: 親ディレクトリへ移動（macOS向け）
            if (e.ctrlKey && e.altKey && e.key === 'ArrowUp') {{
                e.preventDefault();
                navigateToParent();
                return;
            }}
            
            // ↑↓キー（修飾キーなし）: フォーカス移動
            if (!e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey) {{
                if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    focusNext();
                }} else if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    focusPrev();
                }}
            }}
        }});
        
        // ========== 設定ダイアログ ==========
        const SETTINGS_KEY = 'markdownup_settings';
        
        function getSettings() {{
            try {{
                const saved = localStorage.getItem(SETTINGS_KEY);
                if (saved) {{
                    return JSON.parse(saved);
                }}
            }} catch (e) {{
                console.warn('Failed to load settings:', e);
            }}
            return {{ h1h2Margin: 'none', contentMargin: 'normal' }};
        }}
        
        function saveSettings(settings) {{
            try {{
                localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
            }} catch (e) {{
                console.warn('Failed to save settings:', e);
            }}
        }}
        
        const marginMap = {{
            'large': '72px',
            'normal': '48px',
            'small': '24px',
            'none': '0px'
        }};
        
        // グローバルスコープに公開（onclick/onchange属性から呼び出すため）
        window.applyH1H2Margin = function(value) {{
            const settings = getSettings();
            settings.h1h2Margin = value;
            saveSettings(settings);
            document.documentElement.style.setProperty('--mdf2h-presentation-h1h2-margin', marginMap[value] || '0px');
        }};
        
        window.applyContentMargin = function(value) {{
            const settings = getSettings();
            settings.contentMargin = value;
            saveSettings(settings);
            document.documentElement.style.setProperty('--mdf2h-presentation-margin', marginMap[value] || '24px');
        }};
        
        window.openSettingsDialog = function() {{
            const overlay = document.querySelector('.mdf2h-settings-overlay');
            if (overlay) {{
                const settings = getSettings();
                // ラジオボタンの状態を復元
                const h1h2Radio = document.querySelector(`input[name="h1h2margin"][value="${{settings.h1h2Margin || 'none'}}"]`);
                if (h1h2Radio) h1h2Radio.checked = true;
                const contentRadio = document.querySelector(`input[name="contentmargin"][value="${{settings.contentMargin || 'normal'}}"]`);
                if (contentRadio) contentRadio.checked = true;
                overlay.classList.add('show');
            }}
        }};
        
        window.closeSettingsDialog = function() {{
            const overlay = document.querySelector('.mdf2h-settings-overlay');
            if (overlay) {{
                overlay.classList.remove('show');
            }}
        }};
        
        // 初期化
        window.addEventListener('load', () => {{
            loadNavInfo();
            initFocusableElements();
        }});
        
        // オーバーレイクリックで閉じる
        document.addEventListener('click', (e) => {{
            if (e.target.classList.contains('mdf2h-settings-overlay')) {{
                window.closeSettingsDialog();
            }}
        }});
        
        // Escキーで閉じる
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                window.closeSettingsDialog();
            }}
        }});
    </script>
</head>
<body>
    {settings_section}
    <article class="markdown-body">
        {content}
    </article>
</body>
</html>"""

# 設定ボタンとダイアログのHTML（ルートディレクトリのみに表示）
SETTINGS_SECTION_HTML = """<button class="mdf2h-settings-btn" onclick="openSettingsDialog()">⚙️ 設定</button>
    <div class="mdf2h-settings-overlay">
        <div class="mdf2h-settings-dialog">
            <h2>設定</h2>
            <div class="mdf2h-settings-group">
                <label>プレゼン時の全体マージン（H1/H2含む）</label>
                <div class="mdf2h-radio-group">
                    <label class="mdf2h-radio-option"><input type="radio" name="h1h2margin" value="large" onchange="applyH1H2Margin(this.value)"><span>大きく (72px)</span></label>
                    <label class="mdf2h-radio-option"><input type="radio" name="h1h2margin" value="normal" onchange="applyH1H2Margin(this.value)"><span>普通 (48px)</span></label>
                    <label class="mdf2h-radio-option"><input type="radio" name="h1h2margin" value="small" onchange="applyH1H2Margin(this.value)"><span>小さく (24px)</span></label>
                    <label class="mdf2h-radio-option"><input type="radio" name="h1h2margin" value="none" onchange="applyH1H2Margin(this.value)"><span>なし (0px)</span></label>
                </div>
            </div>
            <div class="mdf2h-settings-group">
                <label>プレゼン時の配下コンテンツマージン</label>
                <div class="mdf2h-radio-group">
                    <label class="mdf2h-radio-option"><input type="radio" name="contentmargin" value="large" onchange="applyContentMargin(this.value)"><span>大きく (72px)</span></label>
                    <label class="mdf2h-radio-option"><input type="radio" name="contentmargin" value="normal" onchange="applyContentMargin(this.value)"><span>普通 (48px)</span></label>
                    <label class="mdf2h-radio-option"><input type="radio" name="contentmargin" value="small" onchange="applyContentMargin(this.value)"><span>小さく (24px)</span></label>
                    <label class="mdf2h-radio-option"><input type="radio" name="contentmargin" value="none" onchange="applyContentMargin(this.value)"><span>なし (0px)</span></label>
                </div>
            </div>
        </div>
    </div>"""


class PrettyMarkdownHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """MarkdownをHTMLに変換して表示するハンドラー"""
    
    # クラス変数: --header オプションが有効かどうか
    header_mode = False
    # スクリプトのディレクトリパス（credits.md の読み込みに使用）
    script_dir = Path(__file__).parent
    # 起動時に指定されたベースディレクトリ名
    base_dir_name = ''
    
    def do_GET(self):
        """GETリクエスト処理"""
        # パスをデコードして正規化
        parsed = urllib.parse.urlparse(self.path)
        path_str = urllib.parse.unquote(parsed.path).strip('/')
        query_params = urllib.parse.parse_qs(parsed.query)
        local_path = Path('.') / path_str
        
        # 0. __credits__ エンドポイント（スクリプトディレクトリの credits.md を返す）
        if path_str == '__credits__' and self.header_mode:
            self.send_credits_md()
            return
        
        # 0.1. __logo__ エンドポイント（スクリプトディレクトリの images/logo.png を返す）
        if path_str == '__logo__' and self.header_mode:
            self.send_logo_image()
            return
        
        # 0.5. __nav__ エンドポイント（ナビゲーション情報を返す）
        if path_str == '__nav__':
            nav_path = query_params.get('path', [''])[0]
            self.send_nav_info(nav_path)
            return

        # 0.6. __sig__ エンドポイント（更新検知用シグネチャを返す）
        if path_str == '__sig__':
            sig_path = query_params.get('path', [''])[0]
            self.send_sig_info(sig_path)
            return
        
        # 1. ディレクトリの場合
        if local_path.is_dir():
            self.send_directory_listing(local_path)
            return
        
        # 2. Markdownファイルの場合
        if path_str.endswith('.md') and local_path.exists():
            self.send_markdown_as_html(local_path)
            return
        
        # 3. その他（画像など）は標準の処理に任せる
        super().do_GET()
    
    def send_credits_md(self):
        """スクリプトディレクトリの credits.md をMarkdownとして返す"""
        credits_path = self.script_dir / 'credits.md'
        if credits_path.exists():
            try:
                with open(credits_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_no_cache_headers()
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f'Error reading credits.md: {e}')
        else:
            self.send_error(404, 'credits.md not found')
    
    def send_logo_image(self):
        """スクリプトディレクトリの images/logo.png を返す"""
        logo_path = self.script_dir / 'images' / 'logo.png'
        if logo_path.exists():
            try:
                with open(logo_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_no_cache_headers()
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f'Error reading logo.png: {e}')
        else:
            self.send_error(404, 'images/logo.png not found')
    
    def send_nav_info(self, current_path):
        """ナビゲーション情報をJSONで返す（前後ページ、親ディレクトリ）"""
        import json
        
        result = {
            'parent': None,
            'prevPage': None,
            'nextPage': None
        }
        
        try:
            # パスを正規化（末尾の/を除去）
            current_path = current_path.strip('/')
            if not current_path:
                # ルートの場合
                self._send_json(result)
                return
            
            current_item = Path('.') / current_path
            
            # ディレクトリの場合
            if current_item.is_dir():
                # 親ディレクトリ
                if current_item != Path('.'):
                    parent = current_item.parent
                    if parent == Path('.'):
                        result['parent'] = '/'
                    else:
                        result['parent'] = '/' + str(parent).replace('\\', '/') + '/'
                self._send_json(result)
                return
            
            # ファイルの場合
            # 親ディレクトリ
            if current_item.parent != Path('.'):
                result['parent'] = '/' + str(current_item.parent).replace('\\', '/') + '/'
            else:
                result['parent'] = '/'
            
            # 同ディレクトリ内のMarkdownファイルをファイル名順で取得
            if current_item.suffix.lower() == '.md':
                parent_dir = current_item.parent
                md_files = sorted([
                    f for f in parent_dir.iterdir()
                    if f.is_file() and f.suffix.lower() == '.md' and not f.name.startswith('.')
                ], key=lambda f: f.name.lower())
                
                # 現在のファイルのインデックスを探す
                try:
                    current_index = next(
                        i for i, f in enumerate(md_files)
                        if f.name == current_item.name
                    )
                    
                    # 前のページ
                    if current_index > 0:
                        prev_file = md_files[current_index - 1]
                        result['prevPage'] = '/' + str(prev_file).replace('\\', '/')
                    
                    # 次のページ
                    if current_index < len(md_files) - 1:
                        next_file = md_files[current_index + 1]
                        result['nextPage'] = '/' + str(next_file).replace('\\', '/')
                except StopIteration:
                    pass
            
            self._send_json(result)
            
        except Exception as e:
            self._send_json({'error': str(e)})

    def send_sig_info(self, requested_path):
        """更新検知用のシグネチャをJSONで返す（ファイル/ディレクトリ）"""
        import hashlib

        try:
            # ブラウザの pathname（例: "/foo/bar.md" や "/foo/"）を想定
            p = (requested_path or '').split('?', 1)[0]
            p = urllib.parse.unquote(p)
            p = p.lstrip('/')

            base_dir = Path('.').resolve()
            target = (Path('.') / p) if p else Path('.')

            # パストラバーサルを拒否（base_dir配下のみ許可）
            try:
                target_resolved = target.resolve()
                target_resolved.relative_to(base_dir)
            except Exception:
                self._send_json({'exists': False})
                return

            if target_resolved.is_dir():
                # ディレクトリ一覧に影響するもの（直下の非隠しディレクトリ + .md ファイル）でシグネチャ生成
                items = list(target_resolved.iterdir())
                dirs = [d for d in items if d.is_dir() and not d.name.startswith('.')]
                files = [f for f in items if f.is_file() and f.suffix.lower() == '.md']

                entries = []
                for d in dirs:
                    try:
                        entries.append(('d', d.name, d.stat().st_mtime_ns))
                    except Exception:
                        entries.append(('d', d.name, 0))
                for f in files:
                    try:
                        entries.append(('f', f.name, f.stat().st_mtime_ns))
                    except Exception:
                        entries.append(('f', f.name, 0))

                entries.sort(key=lambda x: x[1].lower())
                h = hashlib.sha1()
                try:
                    h.update(b'DIR\0')
                    h.update(str(target_resolved.stat().st_mtime_ns).encode('ascii', errors='ignore'))
                    h.update(b'\n')
                except Exception:
                    pass
                for kind, name, mtime_ns in entries:
                    h.update(kind.encode('ascii', errors='ignore'))
                    h.update(b'\0')
                    h.update(name.encode('utf-8', errors='replace'))
                    h.update(b'\0')
                    h.update(str(mtime_ns).encode('ascii', errors='ignore'))
                    h.update(b'\n')

                self._send_json({'exists': True, 'kind': 'dir', 'sig': h.hexdigest()})
                return

            if target_resolved.is_file():
                try:
                    sig = str(target_resolved.stat().st_mtime_ns)
                except Exception:
                    sig = '0'
                self._send_json({'exists': True, 'kind': 'file', 'sig': sig})
                return

            self._send_json({'exists': False})
        except Exception as e:
            self._send_json({'exists': False, 'error': str(e)})
    
    def _send_json(self, data):
        """JSONレスポンスを送信"""
        import json
        response = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_no_cache_headers()
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def send_directory_listing(self, dir_path):
        """指定されたディレクトリ直下のファイルとフォルダを表示"""
        try:
            rel_path = dir_path.relative_to(Path('.'))
        except ValueError:
            rel_path = Path('.')
            
        # ルートの場合はベースディレクトリ名を表示、それ以外は相対パスを表示
        if str(rel_path) == '.':
            display_path = self.base_dir_name if self.base_dir_name else '/'
        else:
            # パスデリミタを / で統一
            display_path = self.base_dir_name + '/' + str(rel_path).replace('\\', '/')
        
        items = list(dir_path.iterdir())
        
        # フォルダとファイルを分離（ドットファイルは除外）、更新日時の新しい順にソート
        dirs = [d for d in items if d.is_dir() and not d.name.startswith('.')]
        dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
        
        files = [f for f in items if f.is_file() and f.suffix.lower() == '.md']
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        content = f'<div class="file-list"><h1>📂 {display_path}</h1>'
        
        # 「一つ上へ」のリンク（ルート以外の場合）
        if str(rel_path) != '.':
            parent_link = '/' if str(rel_path.parent) == '.' else '/' + str(rel_path.parent).replace('\\', '/') + '/'
            content += f'<a class="file-item dir-link" href="{parent_link}">⬆️ 一つ上の階層へ</a>'

        if not dirs and not files:
            content += '<p>表示できるファイルやフォルダがありません。</p>'
        else:
            # フォルダを表示
            for d in dirs:
                # リンクは常に末尾に / をつける
                try:
                    d_rel = d.relative_to(Path('.'))
                    d_rel_str = str(d_rel).replace('\\', '/')
                    content += f'<a class="file-item dir-link" href="/{d_rel_str}/">📁 {d.name}/</a>'
                except ValueError:
                    continue
            
            # ファイルを表示
            for f in files:
                try:
                    f_rel = f.relative_to(Path('.'))
                    f_rel_str = str(f_rel).replace('\\', '/')
                    content += f'<a class="file-item" href="/{f_rel_str}">📝 {f.name}</a>'
                except ValueError:
                    continue
        
        content += '</div>'
        
        # ルートディレクトリのみ設定ボタンを表示
        is_root = str(rel_path) == '.'
        settings_section = SETTINGS_SECTION_HTML if is_root else ''
        
        html = HTML_TEMPLATE.format(
            title=f'Index of {display_path}',
            content=content,
            settings_section=settings_section
        )
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_no_cache_headers()
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_markdown_as_html(self, file_path):
        """MarkdownファイルをHTMLに変換して送信"""
        try:
            # ファイルのエンコーディングを自動検出して読み込み
            # utf-8-sig を先に試行してBOM付きUTF-8を正しく処理する
            encodings_to_try = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp', 'latin-1']
            md_content = None
            used_encoding = None
            
            for encoding in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        md_content = f.read()
                    used_encoding = encoding
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            if md_content is None:
                # どのエンコーディングでも読めなかった場合は、バイナリモードで読み込んでエラー文字を置換
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                md_content = raw_data.decode('utf-8', errors='replace')
                used_encoding = 'utf-8 (with errors replaced)'
            
            # Mermaidブロックを一時的にプレースホルダーに置換
            mermaid_blocks = []
            def save_mermaid(match):
                mermaid_blocks.append(match.group(1))
                return f'<!--MERMAID_PLACEHOLDER_{len(mermaid_blocks) - 1}-->'
            
            # ```mermaid ... ``` ブロックを抽出
            md_content = re.sub(
                r'```mermaid\s*\n(.*?)```',
                save_mermaid,
                md_content,
                flags=re.DOTALL
            )
            
            # 強制改ページマーカー: 行頭から8つ以上のハイフンのみの行を検出
            # 印刷時にpage-breakとして機能するdivに変換
            # 注: markdownは ---（3つ以上）を<hr>に変換するため、
            #     8つ以上のハイフンをHTMLコメント形式のプレースホルダーに置換
            #     （___はMarkdownで斜体として解釈されるため使用不可）
            md_content = re.sub(
                r'^-{8,}$',
                '<!--PAGEBREAK8-->',
                md_content,
                flags=re.MULTILINE
            )
            
            if MARKDOWN_AVAILABLE:
                # markdown パッケージを使用
                # 拡張機能をインスタンスとして直接渡すことで、entry_points.txt の検索を回避
                # （暗号化環境等でentry_points.txtが読めない場合の対策）
                extensions = [
                    FencedCodeExtension(),
                    TableExtension(),
                    TocExtension(slugify=githubish_slugify, separator='-'),
                    CodeHiliteExtension(),
                    Nl2BrExtension(),
                    SaneListExtension(),
                    AttrListExtension()
                ]
                # pymdownx.tildeもインスタンスとして追加（インストールされている場合のみ）
                try:
                    from pymdownx.tilde import DeleteSubExtension
                    extensions.append(DeleteSubExtension())
                except ImportError:
                    pass  # pymdownxがインストールされていない場合は無視
                
                html_content = markdown.markdown(
                    md_content,
                    extensions=extensions
                )
            else:
                # フォールバック: HTML変換
                html_content = self.simple_markdown_to_html(md_content)
            
            # Mermaidブロックを復元（<pre class="mermaid">形式で）
            for i, block in enumerate(mermaid_blocks):
                html_content = html_content.replace(
                    f'<!--MERMAID_PLACEHOLDER_{i}-->',
                    f'<pre class="mermaid">{block}</pre>'
                )
            
            # 強制改ページマーカーを復元
            # markdownライブラリが<p>タグで囲む場合があるため、両方のパターンを処理
            html_content = html_content.replace(
                '<p><!--PAGEBREAK8--></p>',
                '<div class="page-break"></div>'
            )
            html_content = html_content.replace(
                '<!--PAGEBREAK8-->',
                '<div class="page-break"></div>'
            )
            
            # 見出しIDは markdown.extensions.toc が付与する（extension_configsでslugifyを調整）
            
            html = self.get_html_template().format(
                title=file_path.name,
                content=html_content,
                header_mode='true' if self.header_mode else 'false'
            )
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_no_cache_headers()
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f'Error: {str(e)}')

    def send_no_cache_headers(self):
        """キャッシュされないようHTTPヘッダーを追加"""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
    
    def get_html_template(self):
        """HTMLテンプレートを返す（Ctrl+P印刷対応）"""
        return '''<!DOCTYPE html>
<html lang="ja" style="color-scheme: light;">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.0/github-markdown.min.css">
    <style>
        .markdown-body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
            background-color: #ffffff;
            color: #24292f;
        }}
        @media (max-width: 767px) {{
            .markdown-body {{
                padding: 15px;
            }}
        }}
        body {{
            background-color: #ffffff;
            color: #24292f;
        }}
        /* コードブロックのライトモード強制 */
        .markdown-body pre {{
            background-color: #f6f8fa !important;
            color: #24292f !important;
        }}
        .markdown-body code {{
            background-color: #f6f8fa !important;
            color: #24292f !important;
        }}
        .markdown-body pre code {{
            background-color: transparent !important;
        }}
        /* テーブルのライトモード強制 */
        .markdown-body table {{
            background-color: #ffffff !important;
        }}
        .markdown-body table tr {{
            background-color: #ffffff !important;
            border-top: 1px solid #d0d7de !important;
        }}
        .markdown-body table tr:nth-child(2n) {{
            background-color: #f6f8fa !important;
        }}
        .markdown-body table th,
        .markdown-body table td {{
            background-color: transparent !important;
            color: #24292f !important;
            border: 1px solid #d0d7de !important;
        }}
        .markdown-body table th {{
            background-color: #f6f8fa !important;
        }}
        .file-list {{
            max-width: 980px;
            margin: 45px auto;
            padding: 20px;
        }}
        .file-list h1 {{
            border-bottom: 2px solid #eaecef;
            padding-bottom: 10px;
        }}
        .file-item {{
            display: block;
            padding: 12px 16px;
            margin: 8px 0;
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            text-decoration: none;
            color: #0969da;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .file-item:hover {{
            background-color: #e6f2ff;
            border-color: #0969da;
            transform: translateX(4px);
        }}
        .dir-section {{
            margin: 24px 0;
        }}
        .dir-section h2 {{
            font-size: 1.2rem;
            margin-bottom: 10px;
        }}
        .dir-link {{
            background-color: #eaf3ff;
            border-color: #8ea1df;
        }}
        
        /* 見出しホバー効果（折りたたみ可能な位置を示す） */
        .markdown-body h1:hover,
        .markdown-body h2:hover,
        .markdown-body h3:hover,
        .markdown-body h4:hover {{
            color: #0969da;
            cursor: default;
        }}
        
        /* 見出しフォーカス時のハイライト */
        .markdown-body h1:focus,
        .markdown-body h2:focus,
        .markdown-body h3:focus,
        .markdown-body h4:focus {{
            color: #0969da;
            outline: none;
        }}
        
        /* ロゴ表示（画面右上、印刷時は非表示） */
        /* 固定サイズ・固定位置（ブラウザの拡大縮小に影響されない） */
        .mdf2h-logo {{
            position: fixed;
            top: 40px;
            right: 40px;
            width: 180px;
            height: auto;
            opacity: 0.8;
            z-index: 1000;
            transition: opacity 0.2s;
        }}
        .mdf2h-logo:hover {{
            opacity: 1;
        }}
        @media print {{
            .mdf2h-logo {{
                display: none;
            }}
        }}
        
        /* 印刷用要素 - 画面では非表示 */
        .mdf2h-print-toc {{
            display: none;
        }}
        .mdf2h-print-credits {{
            display: none;
        }}
        
        /* 強制改ページマーカー - 画面では非表示 */
        .page-break {{
            display: none;
        }}
        
        /* 印刷用スタイル */
        @media print {{
            /* ページ設定 */
            @page {{
                size: auto;
                margin: 15mm 12mm 18mm 12mm;
                @bottom-center {{
                    content: counter(page) " / " counter(pages);
                    font-size: 10pt;
                }}
            }}
            
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .markdown-body {{
                max-width: 100%;
                padding: 0;
                padding-top: 50px; /* creditsとの重なりを避ける */
            }}
            
            /* credits - 最初のページ右上のみ（absoluteで最初のページ内に配置） */
            .mdf2h-print-credits {{
                display: block;
                position: absolute;
                top: 0;
                right: 0;
                text-align: right;
                font-size: 9pt;
                line-height: 1.4;
                padding: 0;
                margin: 0;
            }}
            .mdf2h-print-credits p {{
                margin: 0;
                padding: 0;
            }}
            
            /* 見出しマーク（H2〜H4）*/
            .markdown-body h2::before {{
                content: "■ ";
            }}
            .markdown-body h3::before {{
                content: "● ";
            }}
            .markdown-body h4::before {{
                content: "・ ";
            }}
            
            /* 目次 */
            .mdf2h-print-toc {{
                display: block;
                page-break-after: always;
                margin-bottom: 2em;
                padding-top: 0;
            }}
            .mdf2h-print-toc > h2 {{
                font-size: 1.5em;
                margin-bottom: 1em;
                border-bottom: none;
                padding-bottom: 0;
            }}
            .mdf2h-print-toc > h2::before {{
                content: none; /* 目次タイトルにはマークを付けない */
            }}
            .mdf2h-print-toc > ul {{
                list-style: none;
                padding-left: 1.5em; /* 目次タイトルからインデント */
            }}
            .mdf2h-print-toc li {{
                margin: 0.3em 0;
                line-height: 1.6;
            }}
            .mdf2h-print-toc li.toc-h2::before {{
                content: "■ ";
            }}
            .mdf2h-print-toc li.toc-h3 {{
                padding-left: 1.5em;
                font-size: 0.95em;
            }}
            .mdf2h-print-toc li.toc-h3::before {{
                content: "● ";
            }}
            .mdf2h-print-toc li.toc-h4 {{
                padding-left: 3em;
                font-size: 0.9em;
            }}
            .mdf2h-print-toc li.toc-h4::before {{
                content: "・ ";
            }}
            .mdf2h-print-toc a {{
                color: #000;
                text-decoration: none;
            }}
            
            /* H2の前で改ページ */
            .markdown-body > h2 {{
                page-break-before: always;
            }}
            /* 目次直後と最初のH2は改ページしない */
            .mdf2h-print-toc + h2,
            .markdown-body > h1 + h2 {{
                page-break-before: avoid;
            }}
            
            /* 見出しの直後で改ページしない */
            h1, h2, h3, h4 {{
                page-break-after: avoid;
            }}
            
            /* テーブルは途中で改ページしない */
            table, pre, blockquote {{
                page-break-inside: avoid;
            }}
            
            /* 強制改ページマーカー（--------） */
            .page-break {{
                display: block;
                page-break-before: always;
                height: 0;
                margin: 0;
                padding: 0;
                border: none;
            }}
        }}

        /* ========== コードブロック: Copyボタン ==========
           - クリックでコピーはボタン押下で実行
           - 印刷時は非表示 */
        .mdf2h-codewrap {{
            position: relative;
        }}
        .mdf2h-copy-btn {{
            position: absolute;
            top: 8px;
            right: 8px;
            padding: 6px;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(27, 31, 36, 0.2);
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.9);
            color: #57606a;
            cursor: pointer;
            z-index: 5;
            transition: all 0.15s;
        }}
        .mdf2h-copy-btn:hover {{
            background: rgba(255, 255, 255, 1);
            color: #24292f;
        }}
        .mdf2h-copy-btn svg {{
            width: 16px;
            height: 16px;
        }}

        /* ========== トースト通知 ==========
           - pointer-events:none で操作を邪魔しない */
        .mdf2h-toast {{
            position: fixed;
            right: 16px;
            bottom: 16px;
            max-width: min(420px, calc(100vw - 32px));
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.5;
            color: #fff;
            background: rgba(0, 0, 0, 0.86);
            box-shadow: 0 6px 20px rgba(0,0,0,0.18);
            opacity: 0;
            transform: translateY(8px);
            transition: opacity 160ms ease, transform 160ms ease;
            z-index: 2000;
            pointer-events: none;
        }}
        .mdf2h-toast.show {{
            opacity: 1;
            transform: translateY(0);
        }}
        .mdf2h-toast.error {{
            background: rgba(160, 0, 0, 0.9);
        }}
        @media print {{
            .mdf2h-copy-btn,
            .mdf2h-toast {{
                display: none !important;
            }}
        }}

        /* ========== プレゼンテーションモード ========== */
        :root {{
            --mdf2h-presentation-margin: 48px;
            --mdf2h-presentation-h1h2-margin: 0px;
        }}
        body.mdf2h-presentation-mode {{
            overflow-y: scroll;
        }}
        body.mdf2h-presentation-mode .markdown-body {{
            max-width: 100%;
            margin: 0;
            padding: 8px 12px;
        }}
        /* H1/H2のマージン（設定で変更可能） */
        body.mdf2h-presentation-mode .markdown-body h1,
        body.mdf2h-presentation-mode .markdown-body h2 {{
            margin-left: var(--mdf2h-presentation-h1h2-margin);
            margin-right: var(--mdf2h-presentation-h1h2-margin);
        }}
        /* H1のサイズ・マージン・パディングをH2に合わせる（ページ切り替え時のXY座標を統一） */
        /* !importantはGitHub CSSの :first-child ルールを上書きするため必要 */
        body.mdf2h-presentation-mode .markdown-body h1 {{
            font-size: 1.5em !important;
            margin-top: 24px !important;
            margin-bottom: 16px !important;
            padding-bottom: 0.3em !important;
            border-bottom: 1px solid var(--color-border-muted, #d0d7de) !important;
        }}
        /* H1/H2配下のコンテンツは少し左右にマージンを追加（設定で変更可能） */
        body.mdf2h-presentation-mode .markdown-body h3,
        body.mdf2h-presentation-mode .markdown-body h4,
        body.mdf2h-presentation-mode .markdown-body h5,
        body.mdf2h-presentation-mode .markdown-body h6,
        body.mdf2h-presentation-mode .markdown-body p,
        body.mdf2h-presentation-mode .markdown-body ul,
        body.mdf2h-presentation-mode .markdown-body ol,
        body.mdf2h-presentation-mode .markdown-body blockquote,
        body.mdf2h-presentation-mode .markdown-body pre,
        body.mdf2h-presentation-mode .markdown-body table,
        body.mdf2h-presentation-mode .markdown-body dl {{
            margin-left: var(--mdf2h-presentation-margin);
            margin-right: var(--mdf2h-presentation-margin);
        }}
        body.mdf2h-presentation-mode .markdown-body table {{
            width: calc(100% - var(--mdf2h-presentation-margin) * 2);
            max-width: calc(100% - var(--mdf2h-presentation-margin) * 2);
            display: table;
        }}
        body.mdf2h-presentation-mode .markdown-body pre.mermaid,
        body.mdf2h-presentation-mode .markdown-body .mermaid {{
            max-width: calc(100% - var(--mdf2h-presentation-margin) * 2);
            width: calc(100% - var(--mdf2h-presentation-margin) * 2);
            box-sizing: border-box;
        }}
        body.mdf2h-presentation-mode .markdown-body pre.mermaid {{
            padding: 0;
        }}
        body.mdf2h-presentation-mode .markdown-body svg {{
            display: block;
            width: 100% !important;
            max-width: 100% !important;
            height: auto;
        }}
        .mdf2h-presentation-hidden {{
            display: none !important;
        }}
        /* コードブロックラッパーにマージン適用（Copyボタンも追従） */
        body.mdf2h-presentation-mode .markdown-body .mdf2h-codewrap {{
            margin-left: var(--mdf2h-presentation-margin);
            margin-right: var(--mdf2h-presentation-margin);
        }}
        body.mdf2h-presentation-mode .markdown-body .mdf2h-codewrap pre {{
            margin-left: 0;
            margin-right: 0;
        }}
        
        /* ========== インラインTOC（H1の下に表示） ========== */
        .mdf2h-inline-toc {{
            margin: 16px 0 24px 0;
            padding: 0;
            background-color: transparent;
        }}
        .mdf2h-inline-toc ul {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .mdf2h-inline-toc li {{
            margin: 6px 0;
            line-height: 1.6;
            display: flex;
            align-items: baseline;
        }}
        .mdf2h-inline-toc li::before {{
            content: "•";
            color: #57606a;
            margin-right: 8px;
            font-size: 1.25em;
        }}
        .mdf2h-inline-toc a {{
            color: #24292f;
            text-decoration: none;
            font-size: 1.25em;
        }}
        .mdf2h-inline-toc a:hover {{
            text-decoration: underline;
            color: #0969da;
        }}
        @media print {{
            .mdf2h-inline-toc {{
                display: none;
            }}
        }}
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true }});

        function decodeHashId(raw) {{
            try {{
                return decodeURIComponent(raw);
            }} catch (e) {{
                return raw;
            }}
        }}

        function scrollToHash() {{
            if (!window.location.hash) return;
            const raw = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : window.location.hash;
            const targetId = decodeHashId(raw);
            const target = document.getElementById(targetId);
            if (target) {{
                target.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }}

        // ========== 自動リロード（更新検知） ==========
        const AUTO_RELOAD_INTERVAL_MS = 2000;
        let autoReloadSig = null;
        let autoReloadTimer = null;

        async function fetchSignature() {{
            const path = window.location.pathname;
            const url = '/__sig__?path=' + encodeURIComponent(path);
            const response = await fetch(url, {{ cache: 'no-store' }});
            if (!response.ok) return null;
            return await response.json();
        }}

        async function initAutoReload() {{
            try {{
                const info = await fetchSignature();
                if (!info || !info.exists) return;
                autoReloadSig = info.sig;
                if (autoReloadTimer) clearInterval(autoReloadTimer);
                autoReloadTimer = setInterval(async () => {{
                    try {{
                        const now = await fetchSignature();
                        if (!now || !now.exists) return;
                        if (autoReloadSig !== null && now.sig !== autoReloadSig) {{
                            savePresentationState();
                            location.reload();
                        }}
                    }} catch (e) {{
                        // ignore
                    }}
                }}, AUTO_RELOAD_INTERVAL_MS);
            }} catch (e) {{
                // ignore
            }}
        }}

        // ページ読み込み後、複数のタイミングで試行
        window.addEventListener('load', () => {{
            scrollToHash();
            // Mermaid等の遅延レンダリングに対応
            setTimeout(scrollToHash, 100);
            setTimeout(scrollToHash, 500);
            setTimeout(scrollToHash, 1000);
            initAutoReload();
            restorePresentationState();
        }});
        window.addEventListener('hashchange', scrollToHash);
        
        // ========== インラインTOC（H1の下にH2一覧） ==========
        function insertTocUnderH1() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;
            
            // 既にTOCが挿入されていたらスキップ
            if (article.querySelector('.mdf2h-inline-toc')) return;
            
            // H1を探す
            const h1 = article.querySelector('h1');
            if (!h1) return;
            
            // H2を全て取得
            const h2s = article.querySelectorAll('h2');
            if (h2s.length === 0) return;
            
            // TOCを作成
            const nav = document.createElement('nav');
            nav.className = 'mdf2h-inline-toc';
            const ul = document.createElement('ul');
            
            h2s.forEach((h2, index) => {{
                // 「目次」という見出しはスキップ
                const text = h2.textContent.trim();
                if (text === '目次' || text === 'TOC' || text === 'Table of Contents') return;
                
                // IDがなければ生成
                if (!h2.id) {{
                    h2.id = 'toc-h2-' + index;
                }}
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#' + h2.id;
                a.textContent = text;
                li.appendChild(a);
                ul.appendChild(li);
            }});
            
            nav.appendChild(ul);
            
            // H1の直後に挿入
            h1.insertAdjacentElement('afterend', nav);
        }}
        
        // 印刷前に目次とcreditsを生成
        const headerMode = {header_mode};
        
        // ロゴ画像を挿入
        function insertLogo() {{
            if (!headerMode) return;
            const existingLogo = document.querySelector('.mdf2h-logo');
            if (existingLogo) return; // 既に存在する場合はスキップ
            
            const img = document.createElement('img');
            img.src = '/__logo__';
            img.className = 'mdf2h-logo';
            img.alt = 'Logo';
            img.onerror = () => {{ img.style.display = 'none'; }}; // 画像がない場合は非表示
            document.body.appendChild(img);
        }}

        // ========== コードブロックCopy機能 ==========
        let toastTimer = null;
        function showToast(message, ok = true) {{
            let toast = document.querySelector('.mdf2h-toast');
            if (!toast) {{
                toast = document.createElement('div');
                toast.className = 'mdf2h-toast';
                document.body.appendChild(toast);
            }}
            toast.textContent = message;
            toast.classList.remove('error');
            if (!ok) toast.classList.add('error');
            toast.classList.add('show');

            if (toastTimer) window.clearTimeout(toastTimer);
            toastTimer = window.setTimeout(() => {{
                toast.classList.remove('show');
            }}, 1400);
        }}

        async function copyTextToClipboard(text) {{
            // Clipboard API（https/localhost）を優先
            try {{
                if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {{
                    await navigator.clipboard.writeText(text);
                    return true;
                }}
            }} catch (e) {{
                // fallbackへ
            }}

            // execCommand fallback
            try {{
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.setAttribute('readonly', '');
                ta.style.position = 'fixed';
                ta.style.top = '-1000px';
                ta.style.left = '-1000px';
                document.body.appendChild(ta);
                ta.select();
                const ok = document.execCommand('copy');
                document.body.removeChild(ta);
                return !!ok;
            }} catch (e) {{
                return false;
            }}
        }}

        function initCodeCopyButtons() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;

            const pres = Array.from(article.querySelectorAll('pre'));
            pres.forEach((pre) => {{
                // Mermaidは除外
                if (pre.classList.contains('mermaid')) return;
                // 印刷用の要素内は除外
                if (pre.closest('.mdf2h-print-toc') || pre.closest('.mdf2h-print-credits')) return;
                // 既にラップ済みならスキップ
                if (pre.closest('.mdf2h-codewrap')) return;

                const code = pre.querySelector('code');
                const textSource = code || pre;
                const text = (textSource.textContent || '');
                if (!text.trim()) return;

                const wrapper = document.createElement('div');
                wrapper.className = 'mdf2h-codewrap';

                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'mdf2h-copy-btn';
                btn.title = 'Copy';
                // クリップボードアイコン (GitHub Octicons copy)
                const copyIcon = '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"></path><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"></path></svg>';
                // チェックアイコン (GitHub Octicons check)
                const checkIcon = '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>';
                btn.innerHTML = copyIcon;

                btn.addEventListener('click', async (ev) => {{
                    ev.preventDefault();
                    ev.stopPropagation();
                    const ok = await copyTextToClipboard(textSource.textContent || '');
                    if (ok) {{
                        btn.innerHTML = checkIcon;
                        btn.style.color = '#1a7f37';
                        showToast('Copied!', true);
                        window.setTimeout(() => {{ 
                            btn.innerHTML = copyIcon;
                            btn.style.color = '';
                        }}, 900);
                    }} else {{
                        showToast('Copy failed', false);
                    }}
                }});

                // DOM差し替え: pre を wrapper に移動してボタンを重ねる
                pre.parentNode.insertBefore(wrapper, pre);
                wrapper.appendChild(btn);
                wrapper.appendChild(pre);
            }});
        }}
        
        async function generatePrintContent() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;
            
            // 既存の印刷用要素を削除
            document.querySelectorAll('.mdf2h-print-toc, .mdf2h-print-credits').forEach(el => el.remove());
            
            // H1をタイトルとして取得（最初のH1）
            const h1 = article.querySelector('h1');
            const docTitle = h1 ? h1.textContent : document.title;
            
            // H2〜H4から階層的な目次を生成
            const headings = article.querySelectorAll('h2, h3, h4');
            if (headings.length > 0) {{
                const tocDiv = document.createElement('div');
                tocDiv.className = 'mdf2h-print-toc';
                tocDiv.innerHTML = '<h2>目次</h2>';
                // 印刷用目次のH2はフォーカス対象外にする
                tocDiv.querySelector('h2').setAttribute('tabindex', '-1');
                const ul = document.createElement('ul');
                
                headings.forEach((heading, index) => {{
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    const id = heading.id || 'heading-' + index;
                    if (!heading.id) heading.id = id;
                    a.href = '#' + id;
                    a.textContent = heading.textContent;
                    li.appendChild(a);
                    
                    // レベル別にクラスを設定
                    if (heading.tagName === 'H2') {{
                        li.className = 'toc-h2';
                    }} else if (heading.tagName === 'H3') {{
                        li.className = 'toc-h3';
                    }} else if (heading.tagName === 'H4') {{
                        li.className = 'toc-h4';
                    }}
                    
                    ul.appendChild(li);
                }});
                
                tocDiv.appendChild(ul);
                
                // H1の後に挿入（H1がなければ先頭に）
                if (h1 && h1.nextSibling) {{
                    article.insertBefore(tocDiv, h1.nextSibling);
                }} else {{
                    article.insertBefore(tocDiv, article.firstChild);
                }}
            }}
            
            // credits.md を読み込んで右上に表示
            if (headerMode) {{
                try {{
                    const response = await fetch('/__credits__');
                    if (response.ok) {{
                        const creditsText = await response.text();
                        const creditsDiv = document.createElement('div');
                        creditsDiv.className = 'mdf2h-print-credits';
                        creditsDiv.innerHTML = creditsText
                            .split('\\n')
                            .filter(line => line.trim() !== '')
                            .map(line => '<p>' + line + '</p>')
                            .join('');
                        article.insertBefore(creditsDiv, article.firstChild);
                    }}
                }} catch (e) {{
                    console.warn('Failed to load credits.md:', e);
                }}
            }}
        }}
        
        window.addEventListener('beforeprint', generatePrintContent);
        window.addEventListener('load', generatePrintContent);
        
        // ========== ナビゲーションショートカット ==========
        let navInfo = null;
        
        async function loadNavInfo() {{
            try {{
                const currentPath = window.location.pathname;
                const response = await fetch('/__nav__?path=' + encodeURIComponent(currentPath));
                if (response.ok) {{
                    navInfo = await response.json();
                }}
            }} catch (e) {{
                console.warn('Failed to load nav info:', e);
            }}
        }}
        
        function navigateToParent() {{
            if (navInfo && navInfo.parent) {{
                window.location.href = navInfo.parent;
            }}
        }}
        
        function navigateToPrev() {{
            if (navInfo && navInfo.prevPage) {{
                window.location.href = navInfo.prevPage;
            }}
        }}
        
        function navigateToNext() {{
            if (navInfo && navInfo.nextPage) {{
                window.location.href = navInfo.nextPage;
            }}
        }}
        
        // ========== 見出し折りたたみ機能 ==========
        let hoveredHeading = null;
        
        function initFoldableHeadings() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;
            
            // H1〜H4すべてを対象にする（印刷用目次内は除外）
            const headings = article.querySelectorAll('h1, h2, h3, h4');
            let count = 0;
            headings.forEach((heading) => {{
                // 印刷用目次内の見出しは除外
                if (heading.closest('.mdf2h-print-toc')) {{
                    heading.setAttribute('tabindex', '-1');
                    return;
                }}
                count++;
                // フォーカス可能にする
                heading.setAttribute('tabindex', '0');
                // ホバー検出
                heading.addEventListener('mouseenter', () => {{ hoveredHeading = heading; }});
                heading.addEventListener('mouseleave', () => {{ hoveredHeading = null; }});
                // クリックで展開/折りたたみ
                heading.addEventListener('click', () => {{
                    setActiveHeading(heading);
                    toggleHeading(heading);
                }});
            }});
        }}
        
        function toggleHeading(heading) {{
            const isCollapsed = heading.classList.toggle('collapsed');
            
            // 次の同レベル以上の見出しまでのコンテンツを折りたたみ
            const level = parseInt(heading.tagName.charAt(1));
            let sibling = heading.nextElementSibling;
            
            while (sibling) {{
                const tagName = sibling.tagName;
                if (/^H[1-6]$/.test(tagName)) {{
                    const siblingLevel = parseInt(tagName.charAt(1));
                    if (siblingLevel <= level) break;
                }}
                sibling.style.display = isCollapsed ? 'none' : '';
                sibling = sibling.nextElementSibling;
            }}
        }}

        function setActiveHeading(heading) {{
            if (!heading) return;
            heading.focus();
            const index = focusableElements.indexOf(heading);
            if (index >= 0) {{
                currentFocusIndex = index;
            }}
        }}
        
        function toggleAllH2() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;
            
            const h2s = article.querySelectorAll('h2');
            if (h2s.length === 0) return;
            
            // 最初のH2の状態で全体の展開/折りたたみを決定
            const shouldCollapse = !h2s[0].classList.contains('collapsed');
            
            h2s.forEach(h2 => {{
                const isCurrentlyCollapsed = h2.classList.contains('collapsed');
                if (isCurrentlyCollapsed !== shouldCollapse) {{
                    toggleHeading(h2);
                }}
            }});
        }}
        
        function toggleHoverHeading() {{
            // フォーカス中の見出しを優先、なければホバー中の見出しを操作
            const active = document.activeElement;
            if (active && active.matches && active.matches('.markdown-body h1[tabindex="0"], .markdown-body h2[tabindex="0"], .markdown-body h3[tabindex="0"], .markdown-body h4[tabindex="0"]')) {{
                toggleHeading(active);
                return true;
            }}
            if (hoveredHeading) {{
                setActiveHeading(hoveredHeading);
                toggleHeading(hoveredHeading);
                return true;
            }}
            if (currentFocusIndex >= 0 && focusableElements[currentFocusIndex]) {{
                toggleHeading(focusableElements[currentFocusIndex]);
                return true;
            }}
            return false;
        }}
        
        // ========== フォーカス移動機能 ==========
        let focusableElements = [];
        let currentFocusIndex = -1;
        
        function initFocusableElements() {{
            // H1〜H4すべてを対象にする（tabindex="0"が設定された要素のみ）
            focusableElements = Array.from(document.querySelectorAll('.markdown-body h1[tabindex="0"], .markdown-body h2[tabindex="0"], .markdown-body h3[tabindex="0"], .markdown-body h4[tabindex="0"]'));
            currentFocusIndex = -1;
        }}
        
        function focusNext() {{
            if (focusableElements.length === 0) return;
            currentFocusIndex = (currentFocusIndex + 1) % focusableElements.length;
            focusableElements[currentFocusIndex].focus();
            focusableElements[currentFocusIndex].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
        
        function focusPrev() {{
            if (focusableElements.length === 0) return;
            currentFocusIndex = currentFocusIndex <= 0 ? focusableElements.length - 1 : currentFocusIndex - 1;
            focusableElements[currentFocusIndex].focus();
            focusableElements[currentFocusIndex].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}

        // ========== 設定読み込み ==========
        const SETTINGS_KEY = 'markdownup_settings';
        
        function getSettings() {{
            try {{
                const saved = localStorage.getItem(SETTINGS_KEY);
                if (saved) {{
                    return JSON.parse(saved);
                }}
            }} catch (e) {{
                console.warn('Failed to load settings:', e);
            }}
            return {{ h1h2Margin: 'none', contentMargin: 'normal' }};
        }}
        
        function applyPresentationMarginSetting() {{
            const settings = getSettings();
            const marginMap = {{
                'large': '72px',
                'normal': '48px',
                'small': '24px',
                'none': '0px'
            }};
            const h1h2Margin = marginMap[settings.h1h2Margin] || '0px';
            const contentMargin = marginMap[settings.contentMargin] || '24px';
            document.documentElement.style.setProperty('--mdf2h-presentation-h1h2-margin', h1h2Margin);
            document.documentElement.style.setProperty('--mdf2h-presentation-margin', contentMargin);
        }}

        // ========== プレゼンテーションモード ==========
        let presentationMode = false;
        let presentationSections = [];
        let presentationIndex = 0;
        const PRESENTATION_STATE_KEY = 'mdf2h-presentation-state';

        function savePresentationState() {{
            if (presentationMode) {{
                sessionStorage.setItem(PRESENTATION_STATE_KEY, JSON.stringify({{
                    mode: true,
                    index: presentationIndex
                }}));
            }} else {{
                sessionStorage.removeItem(PRESENTATION_STATE_KEY);
            }}
        }}

        function restorePresentationState() {{
            const saved = sessionStorage.getItem(PRESENTATION_STATE_KEY);
            if (saved) {{
                try {{
                    const state = JSON.parse(saved);
                    if (state.mode) {{
                        presentationMode = true;
                        document.body.classList.add('mdf2h-presentation-mode');
                        applyPresentationMarginSetting();
                        presentationSections = buildPresentationSections();
                        presentationIndex = Math.min(state.index || 0, Math.max(0, presentationSections.length - 1));
                        applyPresentationVisibility();
                    }}
                }} catch (e) {{
                    // ignore
                }}
            }}
        }}

        function isPresentationBoundary(el) {{
            return el && (el.tagName === 'H1' || el.tagName === 'H2');
        }}

        function buildPresentationSections() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return [];
            const children = Array.from(article.children);
            const sections = [];
            let current = null;

            children.forEach((el) => {{
                if (el.classList.contains('mdf2h-print-toc') || el.classList.contains('mdf2h-print-credits')) {{
                    return;
                }}
                if (isPresentationBoundary(el)) {{
                    if (current && current.length > 0) {{
                        sections.push(current);
                    }}
                    current = [el];
                    return;
                }}
                if (!current) {{
                    current = [el];
                }} else {{
                    current.push(el);
                }}
            }});
            if (current && current.length > 0) {{
                sections.push(current);
            }}
            return sections.length > 0 ? sections : [children];
        }}

        function clearPresentationHidden() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;
            article.querySelectorAll('.mdf2h-presentation-hidden').forEach((el) => {{
                el.classList.remove('mdf2h-presentation-hidden');
            }});
        }}

        function applyPresentationVisibility() {{
            const sections = presentationSections;
            if (!sections || sections.length === 0) return;
            sections.forEach((section, index) => {{
                const hidden = index !== presentationIndex;
                section.forEach((el) => {{
                    if (hidden) {{
                        el.classList.add('mdf2h-presentation-hidden');
                    }} else {{
                        el.classList.remove('mdf2h-presentation-hidden');
                    }}
                }});
            }});
            const activeSection = sections[presentationIndex] || [];
            // プレゼンモードでは常にページトップから表示を開始
            // scrollIntoView(smooth)はDOMの変更タイミングとずれるため使用しない
            window.scrollTo(0, 0);
            const sectionHeights = activeSection.slice(0, 6).map((el) => {{
                const r = el.getBoundingClientRect();
                return {{ tag: el.tagName, height: Math.round(r.height) }};
            }});
            const article = document.querySelector('.markdown-body');
            const activeHeading = activeSection.find(el => el.tagName === 'H1' || el.tagName === 'H2');
            let articleRect = null;
            let articleStyle = null;
            let headingRect = null;
            let headingStyle = null;
            if (article) {{
                const rect = article.getBoundingClientRect();
                articleRect = {{ width: Math.round(rect.width), left: Math.round(rect.left), right: Math.round(rect.right) }};
                const style = window.getComputedStyle(article);
                articleStyle = {{
                    paddingLeft: style.paddingLeft,
                    paddingRight: style.paddingRight,
                    marginLeft: style.marginLeft,
                    marginRight: style.marginRight,
                    maxWidth: style.maxWidth,
                    width: style.width
                }};
            }}
            if (activeHeading) {{
                const rect = activeHeading.getBoundingClientRect();
                headingRect = {{
                    width: Math.round(rect.width),
                    left: Math.round(rect.left),
                    right: Math.round(rect.right),
                    top: Math.round(rect.top),
                    bottom: Math.round(rect.bottom)
                }};
                const style = window.getComputedStyle(activeHeading);
                headingStyle = {{
                    marginTop: style.marginTop,
                    marginBottom: style.marginBottom,
                    scrollMarginTop: style.scrollMarginTop
                }};
            }}
            const hiddenElements = Array.from(document.querySelectorAll('.mdf2h-presentation-hidden'));
            const hiddenSample = hiddenElements[0];
            const hiddenSampleStyle = hiddenSample ? window.getComputedStyle(hiddenSample).display : null;
            const bodyHasClass = document.body ? document.body.classList.contains('mdf2h-presentation-mode') : false;
            const visibleH2 = [];
            const h2s = Array.from(document.querySelectorAll('.markdown-body h2'));
            h2s.forEach((h2) => {{
                const display = window.getComputedStyle(h2).display;
                if (display !== 'none') {{
                    visibleH2.push((h2.textContent || '').trim());
                }}
            }});
            const activeTables = activeSection.filter(el => el.tagName === 'TABLE');
            if (activeTables.length > 0) {{
                const tableRects = activeTables.slice(0, 2).map(t => {{
                    const r = t.getBoundingClientRect();
                    const style = window.getComputedStyle(t);
                    return {{
                        width: Math.round(r.width),
                        left: Math.round(r.left),
                        right: Math.round(r.right),
                        styleWidth: style.width,
                        marginLeft: style.marginLeft,
                        marginRight: style.marginRight
                    }};
                }});
            }}
            if (docEl) {{
            }}

            let minLeft = null;
            let maxRight = null;
            let minLeftTag = null;
            let maxRightTag = null;
            activeSection.forEach((el) => {{
                const r = el.getBoundingClientRect();
                if (minLeft === null || r.left < minLeft) {{
                    minLeft = r.left;
                    minLeftTag = el.tagName;
                }}
                if (maxRight === null || r.right > maxRight) {{
                    maxRight = r.right;
                    maxRightTag = el.tagName;
                }}
            }});
            const specialNodes = [];
            activeSection.forEach((el) => {{
                if (el.matches && (el.matches('table, pre, code, svg, .mermaid'))) {{
                    specialNodes.push(el);
                }}
                el.querySelectorAll && el.querySelectorAll('table, pre, code, svg, .mermaid').forEach((node) => {{
                    specialNodes.push(node);
                }});
            }});
            if (specialNodes.length > 0) {{
                const sample = specialNodes.slice(0, 4).map((node) => {{
                    const r = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    return {{
                        tag: node.tagName,
                        left: Math.round(r.left),
                        right: Math.round(r.right),
                        width: Math.round(r.width),
                        styleWidth: style.width,
                        styleMarginLeft: style.marginLeft,
                        styleMarginRight: style.marginRight,
                        display: style.display,
                        attrWidth: node.getAttribute ? node.getAttribute('width') : null,
                        attrHeight: node.getAttribute ? node.getAttribute('height') : null,
                        viewBox: node.getAttribute ? node.getAttribute('viewBox') : null
                    }};
                }});
            }}

            const blockSample = [];
            activeSection.forEach((el) => {{
                if (!el.tagName) return;
                const tag = el.tagName;
                if (!['H1','H2','H3','P','UL','OL','TABLE','PRE','DIV','BLOCKQUOTE'].includes(tag)) return;
                if (blockSample.length >= 6) return;
                const r = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                blockSample.push({{
                    tag,
                    left: Math.round(r.left),
                    right: Math.round(r.right),
                    width: Math.round(r.width),
                    paddingLeft: style.paddingLeft,
                    marginLeft: style.marginLeft,
                    paddingRight: style.paddingRight,
                    marginRight: style.marginRight
                }});
            }});
            if (blockSample.length > 0) {{
            }}

            if (articleRect) {{
                let maxRatio = 0;
                let maxTag = null;
                activeSection.forEach((el) => {{
                    const r = el.getBoundingClientRect();
                    const ratio = r.width / articleRect.width;
                    if (ratio > maxRatio) {{
                        maxRatio = ratio;
                        maxTag = el.tagName;
                    }}
                }});
            }}
        }}

        function findSectionIndexForElement(el) {{
            if (!el || !presentationSections.length) return -1;
            // 直接セクションに含まれるか確認
            let idx = presentationSections.findIndex(section => section.includes(el));
            if (idx >= 0) return idx;
            // 親要素を辿ってセクションを探す
            let parent = el.parentElement;
            while (parent && parent !== document.body) {{
                idx = presentationSections.findIndex(section => section.includes(parent));
                if (idx >= 0) return idx;
                parent = parent.parentElement;
            }}
            return -1;
        }}
        
        // プレゼンモード中のアンカーリンク処理
        function handlePresentationLinkClick(e) {{
            if (!presentationMode) return;
            
            const link = e.target.closest('a[href^="#"]');
            if (!link) return;
            
            const targetId = link.getAttribute('href').slice(1);
            const targetEl = document.getElementById(targetId);
            if (!targetEl) return;
            
            // ターゲット要素が含まれるセクションを探す
            const sectionIndex = findSectionIndexForElement(targetEl);
            if (sectionIndex >= 0 && sectionIndex !== presentationIndex) {{
                e.preventDefault();
                presentationIndex = sectionIndex;
                applyPresentationVisibility();
                savePresentationState();
                // スクロールしてターゲットを表示
                setTimeout(() => {{
                    targetEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}, 100);
            }}
        }}

        function togglePresentationMode() {{
            presentationMode = !presentationMode;
            document.body.classList.toggle('mdf2h-presentation-mode', presentationMode);
            if (presentationMode) {{
                // 設定から余白を適用
                applyPresentationMarginSetting();
                presentationSections = buildPresentationSections();
                const active = document.activeElement;
                const targetIndex = findSectionIndexForElement(active);
                presentationIndex = targetIndex >= 0 ? targetIndex : 0;
                applyPresentationVisibility();
            }} else {{
                clearPresentationHidden();
            }}
            savePresentationState();
        }}

        function gotoPresentation(delta) {{
            if (!presentationMode || presentationSections.length === 0) return;
            const nextIndex = presentationIndex + delta;
            if (nextIndex < 0 || nextIndex >= presentationSections.length) return;
            presentationIndex = nextIndex;
            applyPresentationVisibility();
            savePresentationState();
        }}
        
        // ========== キーボードショートカット ==========
        document.addEventListener('keydown', (e) => {{
            // Ctrl+Alt+A: ルートへ移動
            if (e.ctrlKey && e.altKey && !e.shiftKey && (e.key === 'a' || e.key === 'A')) {{
                e.preventDefault();
                window.location.href = '/';
                return;
            }}
            
            // Ctrl+Shift+矢印: ナビゲーション（Windowsでは Ctrl+Alt+矢印 がシステムに取られるため代替）
            if (e.ctrlKey && e.shiftKey && !e.altKey) {{
                switch(e.key) {{
                    case 'ArrowUp':
                        e.preventDefault();
                        navigateToParent();
                        return;
                    case 'ArrowRight':
                        e.preventDefault();
                        navigateToNext();
                        return;
                    case 'ArrowLeft':
                        e.preventDefault();
                        navigateToPrev();
                        return;
                }}
            }}
            
            // Ctrl+Alt+矢印: ナビゲーション（macOS向け、Windowsでは動作しない場合あり）
            if (e.ctrlKey && e.altKey) {{
                switch(e.key) {{
                    case 'p':
                    case 'P':
                        e.preventDefault();
                        togglePresentationMode();
                        return;
                    case 'ArrowUp':
                        e.preventDefault();
                        navigateToParent();
                        return;
                    case 'ArrowRight':
                        e.preventDefault();
                        navigateToNext();
                        return;
                    case 'ArrowLeft':
                        e.preventDefault();
                        navigateToPrev();
                        return;
                    case 't':
                    case 'T':
                        e.preventDefault();
                        toggleAllH2();
                        return;
                }}
            }}
            
            // Enter: フォーカス/ホバー中の見出しを折りたたみ
            if (!e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey && e.key === 'Enter') {{
                if (toggleHoverHeading()) {{
                    e.preventDefault();
                    return;
                }}
            }}
            
            // Ctrl+Enter: フォーカス/ホバー中の見出しを折りたたみ
            if (e.ctrlKey && e.key === 'Enter') {{
                if (toggleHoverHeading()) {{
                    e.preventDefault();
                    return;
                }}
            }}
            
            // ↑↓キー（修飾キーなし）: プレゼンモードではスクロール、通常モードではフォーカス移動
            if (!e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey) {{
                if (presentationMode) {{
                    // プレゼンモード: ↑↓でスクロール、←→でページ移動
                    if (e.key === 'ArrowDown') {{
                        e.preventDefault();
                        window.scrollBy({{ top: 100, behavior: 'smooth' }});
                    }} else if (e.key === 'ArrowUp') {{
                        e.preventDefault();
                        window.scrollBy({{ top: -100, behavior: 'smooth' }});
                    }} else if (e.key === 'ArrowRight') {{
                        e.preventDefault();
                        gotoPresentation(1);
                    }} else if (e.key === 'ArrowLeft') {{
                        e.preventDefault();
                        gotoPresentation(-1);
                    }}
                }} else {{
                    // 通常モード: ↑↓でフォーカス移動
                    if (e.key === 'ArrowDown') {{
                        e.preventDefault();
                        focusNext();
                    }} else if (e.key === 'ArrowUp') {{
                        e.preventDefault();
                        focusPrev();
                    }}
                }}
            }}
        }});
        
        // ========== 設定ダイアログ ==========
        function saveSettings(settings) {{
            try {{
                localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
            }} catch (e) {{
                console.warn('Failed to save settings:', e);
            }}
        }}
        
        // 初期化
        window.addEventListener('load', () => {{
            loadNavInfo();
            initFoldableHeadings();
            initFocusableElements();
            insertLogo();
            initCodeCopyButtons();
            insertTocUnderH1();
        }});
        
        // プレゼンモード中のアンカーリンククリック処理
        document.addEventListener('click', handlePresentationLinkClick);
    </script>
</head>
<body>
    <article class="markdown-body">
        {content}
    </article>
</body>
</html>'''
    
    @staticmethod
    def simple_markdown_to_html(md_content):
        """Markdown→HTML変換"""
        def apply_strikethrough(text):
            return re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)

        lines = md_content.split('\n')
        html_lines = []
        in_code_block = False
        code_lang = ''

        for line in lines:
            # 先頭の空白を無視して判定（インデント付き ``` などにも対応）
            stripped = line.lstrip()
            # コードブロック
            if stripped.startswith('```'):
                if not in_code_block:
                    code_lang = stripped[3:].strip()
                    html_lines.append(f'<pre><code class="language-{code_lang}">')
                    in_code_block = True
                else:
                    html_lines.append('</code></pre>')
                    in_code_block = False
                continue
            
            if in_code_block:
                html_lines.append(line.replace('<', '&lt;').replace('>', '&gt;'))
                continue
            
            # 見出し
            if stripped.startswith('#### '):
                html_lines.append(f'<h4>{apply_strikethrough(stripped[5:])}</h4>')
            elif stripped.startswith('### '):
                html_lines.append(f'<h3>{apply_strikethrough(stripped[4:])}</h3>')
            elif stripped.startswith('## '):
                html_lines.append(f'<h2>{apply_strikethrough(stripped[3:])}</h2>')
            elif stripped.startswith('# '):
                html_lines.append(f'<h1>{apply_strikethrough(stripped[2:])}</h1>')
            # リスト
            elif stripped.startswith('- ') or stripped.startswith('* '):
                html_lines.append(f'<li>{apply_strikethrough(stripped[2:])}</li>')
            # 空行
            elif line.strip() == '':
                html_lines.append('<br>')
            # 通常のテキスト
            else:
                html_lines.append(f'<p>{apply_strikethrough(line)}</p>')
        
        return '\n'.join(html_lines)


def save_pid(port):
    """PIDファイルにプロセスIDを保存し、最新のポートを記録"""
    try:
        PID_INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
        # ポートごとのPIDファイル
        pid_file = PID_INSTANCES_DIR / f'port_{port}.pid'
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        # 最新のポート番号を記録
        with open(LATEST_PID_FILE, 'w', encoding='utf-8') as f:
            f.write(str(port))
    except Exception as e:
        print(f"[!] PIDファイルの保存に失敗しました: {e}")


def remove_pid(port):
    """指定されたポートのPIDファイルを削除"""
    try:
        pid_file = PID_INSTANCES_DIR / f'port_{port}.pid'
        if pid_file.exists():
            pid_file.unlink()
        
        # 全てのPIDファイルがなくなったら最新ポート記録も消す
        if not any(PID_INSTANCES_DIR.glob('port_*.pid')):
            if LATEST_PID_FILE.exists():
                LATEST_PID_FILE.unlink()
    except Exception as e:
        print(f"[!] PIDファイルの削除に失敗しました: {e}")


def read_pid(port=None):
    """
    PIDファイルからプロセスIDを読み込む。
    portがNoneの場合は最後に使用されたポートを使用する。
    """
    try:
        if port is None:
            if not LATEST_PID_FILE.exists():
                # latestがない場合は、唯一存在するPIDファイルを探す
                pids = list(PID_INSTANCES_DIR.glob('port_*.pid'))
                if len(pids) == 1:
                    port = int(pids[0].stem.split('_')[1])
                else:
                    return None, None
            else:
                with open(LATEST_PID_FILE, 'r', encoding='utf-8') as f:
                    port = int(f.read().strip())
        
        pid_file = PID_INSTANCES_DIR / f'port_{port}.pid'
        if not pid_file.exists():
            return None, port
            
        with open(pid_file, 'r', encoding='utf-8') as f:
            pid = int(f.read().strip())
            return pid, port
    except Exception as e:
        print(f"[ERROR] PIDファイルの読み取りに失敗しました: {e}")
    return None, None


def get_pid_using_port(port):
    """指定ポートをLISTENしているプロセスのPIDを取得（Windows/Linux対応）"""
    import subprocess
    try:
        if sys.platform == 'win32':
            # Windows: netstat -ano
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                # "TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    12345"
                # または "TCP    127.0.0.1:8000    ..."
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        return int(parts[-1])
        else:
            # Linux/macOS: lsof
            result = subprocess.run(
                ['lsof', '-i', f':{port}', '-t'],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                return int(result.stdout.strip().split('\n')[0])
    except Exception:
        pass
    return None


def stop_service():
    """起動中のすべてのサービスを停止"""
    import subprocess
    import time
    
    success_count = 0
    stopped_ports = set()
    
    # 1. PIDファイルからプロセスを停止
    if PID_INSTANCES_DIR.exists():
        pid_files = list(PID_INSTANCES_DIR.glob('port_*.pid'))
        for pid_file in pid_files:
            try:
                port = int(pid_file.stem.split('_')[1])
                with open(pid_file, 'r', encoding='utf-8') as f:
                    pid = int(f.read().strip())
                
                try:
                    if sys.platform == 'win32':
                        # Windows: taskkill /F /PID で強制終了（確認プロンプトなし）
                        subprocess.run(
                            ['taskkill', '/F', '/PID', str(pid)],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    else:
                        # Linux/macOS: signal.SIGTERM
                        os.kill(pid, signal.SIGTERM)
                    
                    print(f"[OK] サービスを停止しました (PID: {pid}, ポート: {port})")
                    success_count += 1
                    stopped_ports.add(port)
                except (ProcessLookupError, OSError):
                    print(f"[!] PID {pid} (ポート: {port}) は既に終了しています")
                    stopped_ports.add(port)
                
                pid_file.unlink()
            except Exception as e:
                print(f"[ERROR] PIDファイル {pid_file.name} の処理中にエラー: {e}")
                try:
                    pid_file.unlink()
                except:
                    pass
    
    if LATEST_PID_FILE.exists():
        LATEST_PID_FILE.unlink()
    
    # 2. 実際にポートを使用しているプロセスをスキャンして停止
    ports_to_check = [DEFAULT_PORT] + FALLBACK_PORTS
    for port in ports_to_check:
        if port in stopped_ports:
            continue
        
        pid = get_pid_using_port(port)
        if pid:
            try:
                if sys.platform == 'win32':
                    # Windows: taskkill /F /PID で強制終了
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(pid)],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # Linux/macOS: signal.SIGTERM
                    os.kill(pid, signal.SIGTERM)
                
                print(f"[OK] ポート {port} を使用中のサービスを停止しました (PID: {pid})")
                success_count += 1
            except (ProcessLookupError, OSError):
                pass
    
    if success_count > 0:
        print(f"\n[*] 合計 {success_count} 個のサービスを停止しました")
    else:
        print("[*] 実行中のサービスはありません")
    
    return 0


def start_service(args):
    """サービスをバックグラウンドで起動（-d/--directory でルートを指定可能）"""
    import subprocess
    import time

    # 子プロセスは --start を付けずに起動する（再帰起動防止）
    try:
        target_dir = resolve_target_directory(getattr(args, 'directory', '.'))
    except Exception:
        target_dir = Path(getattr(args, 'directory', '.'))

    if not target_dir.exists():
        print(f"[ERROR] ディレクトリが見つかりません: {getattr(args, 'directory', '.')}")
        return 1
    if not target_dir.is_dir():
        print(f"[ERROR] 指定されたパスはディレクトリではありません: {getattr(args, 'directory', '.')}")
        return 1

    script_path = Path(__file__).resolve()
    cmd = [
        sys.executable,
        str(script_path),
        '--_child',
        '--port', str(args.port),
        '--directory', str(target_dir),
    ]
    if getattr(args, 'header', False):
        cmd.append('--header')

    # デタッチ実行時はログに出力してトラブルシュートできるようにする
    logs_dir = PID_BASE_DIR / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"markdownup_{int(time.time())}.log"

    start_time_ns = time.time_ns()
    with open(log_path, 'ab') as log_fp:
        # Git Bash/Windows環境で stdout のデフォルトエンコーディングが cp1252 等になると、
        # 日本語の print() で子プロセスが UnicodeEncodeError で即死する場合がある。
        # 子プロセス側だけUTF-8を強制してログ出力が安全に行えるようにする。
        child_env = os.environ.copy()
        child_env['PYTHONUTF8'] = '1'
        child_env['PYTHONIOENCODING'] = 'utf-8'

        popen_kwargs = {
            'stdin': subprocess.DEVNULL,
            'stdout': log_fp,
            'stderr': log_fp,
            'env': child_env,
        }
        if sys.platform == 'win32':
            creationflags = 0
            creationflags |= getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
            creationflags |= getattr(subprocess, 'DETACHED_PROCESS', 0)
            creationflags |= getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            popen_kwargs['creationflags'] = creationflags
        else:
            popen_kwargs['start_new_session'] = True
            popen_kwargs['close_fds'] = True

        proc = subprocess.Popen(cmd, **popen_kwargs)

    print(f"[OK] バックグラウンドで起動しました (PID: {proc.pid})")
    print(f"   ログ: {log_path}")

    # 子プロセスが起動してポートを書き込むまで少し待って表示用のURLを推測する
    detected_port = None
    for _ in range(30):  # 最大3秒
        try:
            if LATEST_PID_FILE.exists():
                st = LATEST_PID_FILE.stat()
                if st.st_mtime_ns >= start_time_ns:
                    txt = LATEST_PID_FILE.read_text(encoding='utf-8').strip()
                    if txt.isdigit():
                        detected_port = int(txt)
                        break
        except Exception:
            pass
        time.sleep(0.1)

    if detected_port:
        print(f"   ローカル: http://localhost:{detected_port}")
    else:
        print(f"   ローカル: http://localhost:{args.port} (指定ポート、または代替ポート)")
    print("   停止するには: python markdownup.py --stop")
    return 0


def build_argument_parser():
    """argparse のパーサを構築（ヘルプ表示と実行時で共通化）"""
    parser = argparse.ArgumentParser(
        description='MarkdownファイルをHTML化するHTTPサーバー',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s                      # ヘルプを表示
  %(prog)s --header             # フォアグラウンド起動（カレントディレクトリを表示）
  %(prog)s --start              # サービスをバックグラウンドで起動（-d ./ と同じ）
  %(prog)s --start --port 8080  # バックグラウンド起動（ポート8080）
  %(prog)s --start -d /path/to/docs --header  # 指定ディレクトリで起動（ヘッダー有効）
  %(prog)s --stop               # サービスを停止

機能:
  MarkdownをHTMLに変換表示（Mermaid図表対応）
  
最適な表示を得るには:
  pip install markdown pygments
        """)

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=DEFAULT_PORT,
        help=f'ポート番号（--start と併用。デフォルト: {DEFAULT_PORT}）'
    )

    # 内部用: --start で起動した子プロセス識別（ヘルプには出さない）
    parser.add_argument(
        '--_child',
        action='store_true',
        help=argparse.SUPPRESS
    )

    parser.add_argument(
        '--directory', '-d',
        type=str,
        default='.',
        help='サーバーのルートディレクトリ（デフォルト: カレントディレクトリ）'
    )

    parser.add_argument(
        '--stop',
        action='store_true',
        help='実行中のすべてのサービスを停止'
    )

    parser.add_argument(
        '--start',
        action='store_true',
        help='バックグラウンドでサービスを起動（-d/--directory, --header を併用可）'
    )

    parser.add_argument(
        '--header',
        action='store_true',
        help='画面右上にロゴ（images/logo.png）を表示、印刷時にcredits.mdを表示'
    )

    return parser


def parse_arguments():
    """コマンドライン引数をパース"""
    parser = build_argument_parser()
    return parser.parse_args()


def find_available_port(preferred_port):
    """利用可能なポートを探す"""
    ports_to_try = [preferred_port] + FALLBACK_PORTS
    
    for port in ports_to_try:
        try:
            # ポートが使用可能か確認
            # Windowsの場合はIPv4で確認（localhostで確認）
            if sys.platform == 'win32':
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # WindowsではSO_REUSEADDRが他と挙動が異なるため、チェック時は使わない
                test_socket.bind(('localhost', port))
                test_socket.close()
            else:
                # Linux/macOSの場合はIPv6で確認
                socketserver.TCPServer.address_family = socket.AF_INET6
                test_socket = socketserver.TCPServer(("::", port), None, bind_and_activate=False)
                test_socket.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                test_socket.server_bind()
                test_socket.server_close()
            return port
        except OSError as e:
            # 10048: Address already in use
            # 10013: Permission denied (Windows reserved port or admin required)
            # 98: Address already in use (Linux)
            if e.errno in (98, 10048, 10013):
                if port == preferred_port:
                    reason = "使用中" if e.errno != 10013 else "システム予約済み/権限不足"
                    print(f"[!] ポート {port} は{reason}です。別のポートを探します...")
                continue
            else:
                raise
    
    return None


def get_working_directory():
    """シェルのカレントディレクトリを取得（MINGW64のUNCパス対応）"""
    # MINGW64/Git Bashでは PWD 環境変数にシェルのcwdが設定される
    pwd = os.environ.get('PWD', '')
    if pwd.startswith('//') or pwd.startswith('\\\\'):
        # UNCパス形式の場合はそのまま使用
        return Path(pwd)
    # 通常はPythonのcwdを使用
    return Path.cwd()


def resolve_target_directory(directory_arg: str) -> Path:
    """-d/--directory の値を実際のルートディレクトリへ解決（UNC配慮）"""
    if directory_arg == '.':
        target_dir = get_working_directory()
    elif Path(directory_arg).is_absolute():
        target_dir = Path(directory_arg)
    else:
        # 相対パスの場合はシェルのcwdを基準にする
        target_dir = get_working_directory() / directory_arg

    # UNCパス以外は resolve() で正規化
    if not str(target_dir).startswith('//') and not str(target_dir).startswith('\\\\'):
        target_dir = target_dir.resolve()

    return target_dir


def is_directory_only_invocation(argv):
    """-d/--directory だけが指定された起動かどうか（値のトークンは除外して判定）"""
    has_directory = False
    other_options = []

    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ('-d', '--directory'):
            has_directory = True
            i += 2  # 値もスキップ
            continue
        if tok.startswith('--directory='):
            has_directory = True
            i += 1
            continue
        if tok.startswith('-'):
            other_options.append(tok)
        i += 1

    return has_directory and len(other_options) == 0


def is_port_without_start_invocation(argv):
    """--start なしで --port/-p が指定された起動かどうか（値のトークンは除外して判定）"""
    has_start = False
    has_port = False
    has_child = False

    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == '--start':
            has_start = True
            i += 1
            continue
        if tok == '--_child':
            has_child = True
            i += 1
            continue
        if tok in ('-p', '--port'):
            has_port = True
            i += 2  # 値もスキップ
            continue
        if tok.startswith('--port='):
            has_port = True
            i += 1
            continue
        i += 1

    return has_port and not has_start and not has_child


def main():
    """メイン処理"""
    # 引数なしの場合はヘルプを表示
    # ただし argcomplete の補完実行（_ARGCOMPLETE=1）時はここで抜けると補完が動かないため除外
    if len(sys.argv) == 1 and os.environ.get("_ARGCOMPLETE") != "1":
        parser = build_argument_parser()
        parser.print_help()
        return

    # -d/--directory 単体での起動は廃止（ヘルプ表示に寄せる）
    # ただし argcomplete の補完実行時はここで抜けない
    if os.environ.get("_ARGCOMPLETE") != "1":
        if is_directory_only_invocation(sys.argv[1:]):
            parser = build_argument_parser()
            parser.print_help()
            return
        if is_port_without_start_invocation(sys.argv[1:]):
            parser = build_argument_parser()
            parser.print_help()
            return
    
    args = parse_arguments()
    
    # --stop オプションの処理
    if args.stop:
        return stop_service()

    # --start オプションの処理
    if args.start:
        return start_service(args)
    
    # ディレクトリの検証と移動
    # MINGW64/Git Bash環境でUNCパス（//server/share/...）をサポート
    target_dir = resolve_target_directory(args.directory)
    
    if not target_dir.exists():
        print(f"[ERROR] ディレクトリが見つかりません: {args.directory}")
        return 1
    if not target_dir.is_dir():
        print(f"[ERROR] 指定されたパスはディレクトリではありません: {args.directory}")
        return 1
    
    # 指定されたディレクトリに移動
    try:
        os.chdir(target_dir)
        print(f"[*] ルートディレクトリ: {target_dir}")
    except Exception as e:
        print(f"[ERROR] ディレクトリへの移動に失敗しました: {e}")
        return 1
    
    # ハンドラーの選択
    handler = PrettyMarkdownHTTPRequestHandler
    handler.header_mode = args.header
    handler.base_dir_name = target_dir.name  # ベースディレクトリ名を設定
    if args.header:
        print(f"[*] ヘッダーモード有効: credits.md を印刷時に表示します")
    if not MARKDOWN_AVAILABLE:
        print("[!] markdownパッケージがインストールされていません")
        print("   最適な表示のために以下をインストールしてください:")
        print("   pip install markdown pygments\n")
    
    # 利用可能なポートを探す
    port = find_available_port(args.port)
    
    if port is None:
        print("[ERROR] 利用可能なポートが見つかりませんでした")
        return 1
    
    # サーバー起動
    print("=" * 60)
    print(f"Markdownビューワーサーバー")
    print("=" * 60)
    
    try:
        # PIDを保存
        save_pid(port)
        
        # サーバー起動（プラットフォームに応じて対応）
        if sys.platform == 'win32':
            # WindowsではIPv4で起動（localhostでリッスン）
            socketserver.TCPServer.address_family = socket.AF_INET
            with socketserver.TCPServer(("localhost", port), handler) as httpd:
                if port != args.port:
                    print(f"[OK] ポート {port} でサーバーを起動しました（代替ポート）")
                else:
                    print(f"[OK] ポート {port} でサーバーを起動しました")
                
                print(f"   ローカル:     http://localhost:{port}")
                print(f"   ネットワーク: http://192.168.1.13:{port}")
                print(f"\n[!] ブラウザでアクセスしてMarkdownファイルを表示できます")
                print(f"   停止するには: python markdownup.py --stop")
                print("   または Ctrl+C を押してください\n")
                print("=" * 60 + "\n")
                
                httpd.serve_forever()
        else:
            # Linux/macOSではIPv6対応（IPv4もデュアルスタック）
            socketserver.TCPServer.address_family = socket.AF_INET6
            with socketserver.TCPServer(("::", port), handler, bind_and_activate=False) as httpd:
                # IPv6ソケットでIPv4も受け入れる設定（デュアルスタック）
                httpd.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                httpd.server_bind()
                httpd.server_activate()
                
                if port != args.port:
                    print(f"[OK] ポート {port} でサーバーを起動しました（代替ポート）")
                else:
                    print(f"[OK] ポート {port} でサーバーを起動しました")
                
                print(f"   ローカル:     http://localhost:{port}")
                print(f"   ネットワーク: http://pi.local:{port}")
                print(f"   IPv4:        http://192.168.1.13:{port}")
                print(f"\n[!] ブラウザでアクセスしてMarkdownファイルを表示できます")
                print(f"   (IPv4/IPv6 デュアルスタック対応)")
                print(f"   停止するには: python markdownup.py --stop")
                print("   または Ctrl+C を押してください\n")
                print("=" * 60 + "\n")
                
                httpd.serve_forever()
    except KeyboardInterrupt:
        # Ctrl+C による終了
        print("\n\n[*] サーバーを停止しています...")
        remove_pid(port)
        return 0
    except Exception as e:
        print(f"\n[ERROR] {e}")
        remove_pid(port)
        return 1
    finally:
        remove_pid(port)


if __name__ == "__main__":
    sys.exit(main() or 0)
