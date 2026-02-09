# -*- coding: utf-8 -*-
"""PID管理およびサービス起動/停止"""

import sys
import os
import signal
from pathlib import Path

from .constants import (
    DEFAULT_PORT, FALLBACK_PORTS,
    PID_BASE_DIR, PID_INSTANCES_DIR, LATEST_PID_FILE
)
from .utils import resolve_target_directory


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
            # Windows日本語環境ではコマンド出力がCP932のため、encoding='oem'で読む
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                encoding='oem',
                errors='replace',
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
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
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
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
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

    # パッケージとして起動: python -m markdownup
    cmd = [
        sys.executable,
        '-m', 'markdownup',
        '--_child',
        '--port', str(args.port),
        '--directory', str(target_dir),
    ]
    if getattr(args, 'header', False):
        cmd.append('--header')

    # #region agent log
    print(f"[DEBUG-E2] start_service: cmd={cmd}")
    print(f"[DEBUG-E2] start_service: args.header={getattr(args, 'header', False)}, target_dir={target_dir}")
    # #endregion

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
    print("   停止するには: markdownup --stop")
    return 0
