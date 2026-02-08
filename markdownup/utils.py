# -*- coding: utf-8 -*-
"""ユーティリティ関数群"""

import re
import sys
import os
import socket
import socketserver
from pathlib import Path

from .constants import DEFAULT_PORT, FALLBACK_PORTS


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
