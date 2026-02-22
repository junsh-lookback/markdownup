# -*- coding: utf-8 -*-
"""HTTPリクエストハンドラー"""

import html
import http.server
import json
import re
import urllib.parse
from pathlib import Path

from .constants import MARKDOWN_AVAILABLE
from .templates import HTML_TEMPLATE, SETTINGS_SECTION_HTML, get_print_html_template
from .utils import githubish_slugify

# Markdownライブラリ（利用可能な場合のみ）
if MARKDOWN_AVAILABLE:
    import markdown
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.toc import TocExtension
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.nl2br import Nl2BrExtension
    from markdown.extensions.sane_lists import SaneListExtension
    from markdown.extensions.attr_list import AttrListExtension


class PrettyMarkdownHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """MarkdownをHTMLに変換して表示するハンドラー"""
    
    # クラス変数: --header オプションが有効かどうか
    header_mode = False
    # スクリプトのディレクトリパス
    script_dir = Path(__file__).parent.parent
    # 起動時に指定されたベースディレクトリ名
    base_dir_name = ''
    
    def do_GET(self):
        """GETリクエスト処理"""
        # パスをデコードして正規化
        parsed = urllib.parse.urlparse(self.path)
        path_str = urllib.parse.unquote(parsed.path).strip('/')
        query_params = urllib.parse.parse_qs(parsed.query)
        local_path = Path('.') / path_str
        
        # 0. __credits__ エンドポイント（~/.markdownup/credits.md を返す）
        if path_str == '__credits__' and self.header_mode:
            self.send_credits_md()
            return
        
        # 0.1. __logo__ エンドポイント（~/.markdownup/images/logo.png を返す）
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
    
    def do_POST(self):
        """POSTリクエスト処理（編集内容の保存）"""
        parsed = urllib.parse.urlparse(self.path)
        path_str = urllib.parse.unquote(parsed.path).strip('/')
        
        # __save__ エンドポイント
        if path_str == '__save__':
            self.handle_save_request()
            return
        
        self.send_error(404, 'Not found')
    
    def handle_save_request(self):
        """編集内容をファイルに保存"""
        try:
            # Content-Lengthヘッダーからデータサイズを取得
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, 'No content')
                return
            
            # JSONデータを読み取り
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # パスとコンテンツを取得（URLエンコードされた日本語パスをデコード）
            file_path = urllib.parse.unquote(data.get('path', ''))
            content = data.get('content', '')
            
            if not file_path or not file_path.endswith('.md'):
                self.send_error(400, 'Invalid path')
                return
            
            # セキュリティチェック: パストラバーサル防止
            local_path = Path('.') / file_path.strip('/')
            try:
                local_path.resolve().relative_to(Path('.').resolve())
            except ValueError:
                self.send_error(403, 'Access denied')
                return
            
            # ファイルに書き込み
            local_path.write_text(content, encoding='utf-8')
            
            # 成功レスポンス
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({'success': True})
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f'Save error: {e}')
    
    def send_credits_md(self):
        """~/.markdownup/credits.md をMarkdownとして返す"""
        credits_path = Path.home() / '.markdownup' / 'credits.md'
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
            self.send_error(404, '~/.markdownup/credits.md not found')
    
    def send_logo_image(self):
        """~/.markdownup/images/logo.png を返す"""
        logo_path = Path.home() / '.markdownup' / 'images' / 'logo.png'
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
            self.send_error(404, '~/.markdownup/images/logo.png not found')
    
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
                # ディレクトリ一覧に影響するもの（直下のディレクトリ + .md ファイル）でシグネチャ生成
                items = list(target_resolved.iterdir())
                dirs = [d for d in items if d.is_dir()]
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
        
        # フォルダとファイルを分離、更新日時の新しい順にソート
        dirs = [d for d in items if d.is_dir()]
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
        
        html_output = HTML_TEMPLATE.format(
            title=f'Index of {display_path}',
            content=content,
            settings_section=settings_section
        )
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_no_cache_headers()
        self.end_headers()
        self.wfile.write(html_output.encode('utf-8'))
    
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
            # HTMLエスケープにより <br/> 等のHTMLタグがブラウザに解釈されるのを防ぐ
            # mermaid.jsはtextContentで読み取るため、エスケープされた文字は自動的に復元される
            for i, block in enumerate(mermaid_blocks):
                html_content = html_content.replace(
                    f'<!--MERMAID_PLACEHOLDER_{i}-->',
                    f'<pre class="mermaid">{html.escape(block)}</pre>'
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
            
            html_output = self.get_html_template().format(
                title=file_path.name,
                content=html_content,
                header_mode='true' if self.header_mode else 'false'
            )
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_no_cache_headers()
            self.end_headers()
            self.wfile.write(html_output.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f'Error: {str(e)}')

    def send_no_cache_headers(self):
        """キャッシュされないようHTTPヘッダーを追加"""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
    
    def get_html_template(self):
        """HTMLテンプレートを返す（Ctrl+P印刷対応）"""
        return get_print_html_template()
    
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
