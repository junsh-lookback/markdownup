#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""
Markdownビューワーサーバー
UTF-8エンコーディングでMarkdownファイルを配信します

使用例:
    # サーバーを起動（HTMLに変換）
    python mdfile2html.py --port 8000
    
    # 特定のディレクトリをルートとして起動
    python mdfile2html.py --directory /path/to/docs --port 8000
    python mdfile2html.py -d ~/Documents/notes -p 8080
    
    # サービス停止
    python mdfile2html.py --stop
    
    # サービス再起動
    python mdfile2html.py --restart
    
    # 最適な表示を得るには
    pip install markdown pygments
    
    # タブ補完を有効にするには（bash / Git Bash）
    # ※ `python mdfile2html.py ...` 形式は argcomplete の仕様上うまく補完できないため
    #    `mdfile2html` コマンドとしてインストールして利用してください
    pip install argcomplete
    pip install -e .
    pyenv rehash  # pyenv-win を使っている場合
    export ARGCOMPLETE_USE_TEMPFILES=1  # Git Bash(Windows) の場合
    eval "$(register-python-argcomplete --no-defaults mdfile2html)"
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

# タブ補完のサポート（オプショナル）
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


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
    from markdown.extensions import fenced_code, tables, toc, codehilite
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# デフォルト設定
DEFAULT_PORT = 8000
FALLBACK_PORTS = [8001, 8080, 8888, 9000, 3000]
PID_BASE_DIR = Path.home() / '.mdfile2html'
PID_INSTANCES_DIR = PID_BASE_DIR / 'instances'
LATEST_PID_FILE = PID_BASE_DIR / 'latest_port'

# HTML テンプレート
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
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
        }}
        @media (max-width: 767px) {{
            .markdown-body {{
                padding: 15px;
            }}
        }}
        body {{
            background-color: #ffffff;
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
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
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

        // ページ読み込み後、複数のタイミングで試行
        window.addEventListener('load', () => {{
            scrollToHash();
            // Mermaid等の遅延レンダリングに対応
            setTimeout(scrollToHash, 100);
            setTimeout(scrollToHash, 500);
            setTimeout(scrollToHash, 1000);
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
            // Ctrl+Alt+↑: 親ディレクトリへ移動
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
        
        // 初期化
        window.addEventListener('load', () => {{
            loadNavInfo();
            initFocusableElements();
        }});
    </script>
</head>
<body>
    <article class="markdown-body">
        {content}
    </article>
</body>
</html>"""


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
        
        html = HTML_TEMPLATE.format(
            title=f'Index of {display_path}',
            content=content
        )
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_no_cache_headers()
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_markdown_as_html(self, file_path):
        """MarkdownファイルをHTMLに変換して送信"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
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
            
            if MARKDOWN_AVAILABLE:
                # markdown パッケージを使用
                html_content = markdown.markdown(
                    md_content,
                    extensions=[
                        'fenced_code',
                        'tables',
                        'toc',
                        'codehilite',
                        'nl2br',
                        'sane_lists',
                        'attr_list'  # アンカーリンク対応
                    ],
                    extension_configs={
                        # tocが付与する見出しID（アンカー）をGitHub風に寄せる
                        'toc': {
                            'slugify': githubish_slugify,
                            'separator': '-',
                        }
                    }
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
<html lang="ja">
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
        }}
        @media (max-width: 767px) {{
            .markdown-body {{
                padding: 15px;
            }}
        }}
        body {{
            background-color: #ffffff;
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
        
        /* 見出しフォーカス時のハイライト */
        .markdown-body h2:focus,
        .markdown-body h3:focus,
        .markdown-body h4:focus {{
            color: #0969da;
            outline: none;
        }}
        
        /* ロゴ表示（画面右上、印刷時は非表示） */
        .mdf2h-logo {{
            position: fixed;
            top: 5px;
            right: 5px;
            max-height: 30px;
            max-width: 80px;
            opacity: 0.7;
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
        
        /* 印刷用スタイル */
        @media print {{
            /* ページ設定 */
            @page {{
                size: A4;
                margin: 20mm 15mm 25mm 15mm;
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
        }}
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
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

        // ページ読み込み後、複数のタイミングで試行
        window.addEventListener('load', () => {{
            scrollToHash();
            // Mermaid等の遅延レンダリングに対応
            setTimeout(scrollToHash, 100);
            setTimeout(scrollToHash, 500);
            setTimeout(scrollToHash, 1000);
        }});
        window.addEventListener('hashchange', scrollToHash);
        
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
            
            const headings = article.querySelectorAll('h2, h3, h4');
            headings.forEach((heading) => {{
                // フォーカス可能にする
                heading.setAttribute('tabindex', '0');
                // ホバー検出
                heading.addEventListener('mouseenter', () => {{ hoveredHeading = heading; }});
                heading.addEventListener('mouseleave', () => {{ hoveredHeading = null; }});
                // クリックで展開/折りたたみ
                heading.addEventListener('click', () => {{ toggleHeading(heading); }});
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
            // Ctrl+Enter: フォーカス中の見出しを優先、なければホバー中の見出しを操作
            if (currentFocusIndex >= 0 && focusableElements[currentFocusIndex]) {{
                toggleHeading(focusableElements[currentFocusIndex]);
            }} else if (hoveredHeading) {{
                toggleHeading(hoveredHeading);
            }}
        }}
        
        // ========== フォーカス移動機能 ==========
        let focusableElements = [];
        let currentFocusIndex = -1;
        
        function initFocusableElements() {{
            // 見出し（H2, H3, H4）のみを対象にする
            focusableElements = Array.from(document.querySelectorAll('.markdown-body h2, .markdown-body h3, .markdown-body h4'));
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
            // Ctrl+Alt+矢印: ナビゲーション
            if (e.ctrlKey && e.altKey) {{
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
                    case 'r':
                    case 'R':
                        e.preventDefault();
                        toggleAllH2();
                        return;
                }}
            }}
            
            // Ctrl+Enter: ホバー中の見出しを折りたたみ
            if (e.ctrlKey && e.key === 'Enter') {{
                e.preventDefault();
                toggleHoverHeading();
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
        
        // 初期化
        window.addEventListener('load', () => {{
            loadNavInfo();
            initFoldableHeadings();
            initFocusableElements();
            insertLogo();
        }});
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
                html_lines.append(f'<h4>{stripped[5:]}</h4>')
            elif stripped.startswith('### '):
                html_lines.append(f'<h3>{stripped[4:]}</h3>')
            elif stripped.startswith('## '):
                html_lines.append(f'<h2>{stripped[3:]}</h2>')
            elif stripped.startswith('# '):
                html_lines.append(f'<h1>{stripped[2:]}</h1>')
            # リスト
            elif stripped.startswith('- ') or stripped.startswith('* '):
                html_lines.append(f'<li>{stripped[2:]}</li>')
            # 空行
            elif line.strip() == '':
                html_lines.append('<br>')
            # 通常のテキスト
            else:
                html_lines.append(f'<p>{line}</p>')
        
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


def restart_service(args):
    """サービスを再起動"""
    pid, saved_port = read_pid(args.port if args.port != DEFAULT_PORT else None)
    
    if pid is None:
        print("[!] 実行中のサービスが見つかりません")
        print("   新しくサービスを起動します...\n")
        return None  # 新規起動へ
    
    print(f"[*] サービスを再起動します (PID: {pid}, ポート: {saved_port})")
    
    # まず停止
    try:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[OK] 既存のサービスを停止しました")
        except (ProcessLookupError, OSError):
            print(f"[!] 既存のプロセスは既に終了しています")
        remove_pid(saved_port)
        
        # 少し待機
        import time
        time.sleep(1)
        
        # ポート指定がない場合は保存されていたポートを使用
        if args.port == DEFAULT_PORT and saved_port is not None:
            args.port = saved_port
        
        return args  # 起動処理へ
        
    except ProcessLookupError:
        print(f"[!] PID {pid} のプロセスが見つかりません")
        print("   PIDファイルをクリアして新しくサービスを起動します...\n")
        remove_pid()
        return None  # 新規起動へ
    except Exception as e:
        print(f"[ERROR] サービスの停止に失敗しました: {e}")
        return 1


def parse_arguments():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description='Markdownファイルを正しい文字エンコーディングで配信するHTTPサーバー',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s                      # ヘルプを表示
  %(prog)s --port 8080          # サーバーを起動（ポート8080）
  %(prog)s -d /path/to/docs     # 指定ディレクトリをルートとして起動
  %(prog)s --stop               # サービスを停止
  %(prog)s --restart            # サービスを再起動

機能:
  MarkdownをHTMLに変換して美しく表示（Mermaid図表対応）
  
最適な表示を得るには:
  pip install markdown pygments

タブ補完を有効にするには:
  pip install -e .
  pyenv rehash  # pyenv-win を使っている場合
  export ARGCOMPLETE_USE_TEMPFILES=1  # Git Bash(Windows) の場合
  eval "$(register-python-argcomplete --no-defaults mdfile2html)"
        """)
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=DEFAULT_PORT,
        help=f'ポート番号（デフォルト: {DEFAULT_PORT}）'
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
        '--restart',
        action='store_true',
        help='実行中のサービスを再起動'
    )
    
    parser.add_argument(
        '--header',
        action='store_true',
        help='画面右上にロゴ（images/logo.png）を表示、印刷時にcredits.mdを表示'
    )
    
    # タブ補完を有効化
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)
    
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


def signal_handler(sig, frame):
    """シグナルハンドラー（Ctrl+C処理）"""
    print("\n\n[*] サーバーを停止しています...")
    # ポート番号を取得するために、httpd オブジェクトが必要だが
    # ここでは PID ファイルを特定できないため、終了時に cleanup される
    os._exit(0)


def main():
    """メイン処理"""
    # 引数なしの場合はヘルプを表示
    # ただし argcomplete の補完実行（_ARGCOMPLETE=1）時はここで抜けると補完が動かないため除外
    if len(sys.argv) == 1 and os.environ.get("_ARGCOMPLETE") != "1":
        parser = argparse.ArgumentParser(
            description='Markdownファイルを正しい文字エンコーディングで配信するHTTPサーバー',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  %(prog)s                      # ヘルプを表示
  %(prog)s --port 8080          # サーバーを起動（ポート8080）
  %(prog)s -d /path/to/docs     # 指定ディレクトリをルートとして起動
  %(prog)s --stop               # すべてのサービスを停止
  %(prog)s --restart            # サービスを再起動

機能:
  MarkdownをHTMLに変換（Mermaid図表対応）
  
最適な表示を得るには:
  pip install markdown pygments

タブ補完を有効にするには:
  pip install -e .
  pyenv rehash  # pyenv-win を使っている場合
  export ARGCOMPLETE_USE_TEMPFILES=1  # Git Bash(Windows) の場合
  eval "$(register-python-argcomplete --no-defaults mdfile2html)"

Git Bashで「Tab1回で候補一覧を表示」したい場合（シェル全体に影響）:
  bind 'set show-all-if-ambiguous on'
  # または ~/.inputrc に: set show-all-if-ambiguous on
        """)
        parser.print_help()
        return
    
    args = parse_arguments()
    
    # Ctrl+Cのシグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, signal_handler)
    
    # --stop オプションの処理
    if args.stop:
        return stop_service()
    
    # --restart オプションの処理
    if args.restart:
        result = restart_service(args)
        if result == 1:
            return 1  # エラー
        # result が None または args の場合は起動処理を続行
    
    # ディレクトリの検証と移動
    target_dir = Path(args.directory).resolve()
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
                print(f"   停止するには: python mdfile2html.py --stop")
                print(f"   再起動するには: python mdfile2html.py --restart")
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
                print(f"   停止するには: python mdfile2html.py --stop")
                print(f"   再起動するには: python mdfile2html.py --restart")
                print("   または Ctrl+C を押してください\n")
                print("=" * 60 + "\n")
                
                httpd.serve_forever()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        remove_pid(port)
        return 1
    finally:
        remove_pid(port)


if __name__ == "__main__":
    sys.exit(main() or 0)
