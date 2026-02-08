# -*- coding: utf-8 -*-
"""コマンドライン引数解析とメイン関数"""

import argparse
import sys
import os
import socket
import socketserver
from pathlib import Path

from .constants import DEFAULT_PORT, MARKDOWN_AVAILABLE
from .handler import PrettyMarkdownHTTPRequestHandler
from .service import save_pid, remove_pid, stop_service, start_service
from .utils import (
    find_available_port, resolve_target_directory,
    is_directory_only_invocation, is_port_without_start_invocation
)


def build_argument_parser():
    """argparse のパーサを構築（ヘルプ表示と実行時で共通化）"""
    parser = argparse.ArgumentParser(
        description='MarkdownファイルをHTML化するHTTPサーバー',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s                      # ヘルプを表示
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
                print(f"   停止するには: markdownup --stop")
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
                print(f"   停止するには: markdownup --stop")
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
