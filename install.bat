@echo off
REM markdownup インストールスクリプト (Windows)
REM .txt拡張子を避けるため、依存パッケージを直接インストールし、
REM スクリプトを直接使用する方法を採用します

echo ==========================================
echo markdownup セットアップ
echo ==========================================

REM 依存パッケージをインストール
echo [1/2] 依存パッケージをインストール中...
python -m pip install --user markdown pygments

if errorlevel 1 (
    echo [エラー] 依存パッケージのインストールに失敗しました
    exit /b 1
)

echo [2/2] セットアップ完了
echo.
echo ==========================================
echo 使用方法:
echo ==========================================
echo   python markdownup.py --help
echo   python markdownup.py -d ./
echo.
echo バッチファイルを作成して簡単に起動できるようにするには:
echo   echo @echo off ^> markdownup.bat
echo   echo python "%CD%\markdownup.py" %%* ^>^> markdownup.bat
echo.
echo その後、markdownup.bat をパスの通った場所に置いてください
echo ==========================================
pause

