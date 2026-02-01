# インストール手順

## 問題: .txt ファイルが暗号化される環境向けの対応

一部のPC環境では、`.txt` 拡張子のファイルが自動的に暗号化されるため、
標準的な `pip install -e .` によるインストールができない場合があります。

この問題を回避するため、以下の方法でセットアップを行います。

## セットアップ方法

### Linux/macOS の場合

```bash
bash install.sh
```

または手動で:

```bash
# 1. 依存パッケージをインストール
python -m pip install --user markdown pygments

# 2. エイリアスを設定(オプション)
echo "alias markdownup='python $(pwd)/markdownup.py'" >> ~/.bashrc
source ~/.bashrc
```

### Windows の場合

```cmd
install.bat
```

または手動で:

```cmd
REM 1. 依存パッケージをインストール
python -m pip install --user markdown pygments

REM 2. バッチファイルを作成(オプション)
echo @echo off > markdownup.bat
echo python "%CD%\markdownup.py" %%* >> markdownup.bat
```

## 使用方法

セットアップ後、以下のように直接実行します:

```bash
# ヘルプを表示
python markdownup.py --help

# サーバーを起動
python markdownup.py -d ./

# ポート指定
python markdownup.py -d ./ --port 8080
```

## エイリアス/ショートカットの作成(オプション)

### Linux/macOS

```bash
# エイリアスを追加
echo "alias markdownup='python /path/to/markdownup.py'" >> ~/.bashrc
source ~/.bashrc

# または、シンボリックリンクを作成
ln -s /path/to/markdownup.py ~/.local/bin/markdownup
chmod +x ~/.local/bin/markdownup
```

### Windows

プロジェクトディレクトリに `markdownup.bat` を作成:

```batch
@echo off
python "C:\path\to\markdownup.py" %*
```

このファイルをパスの通った場所(例: `C:\Windows\` や `%USERPROFILE%\bin`)にコピーすれば、
どこからでも `markdownup` コマンドとして使用できます。

## トラブルシューティング

### markdownパッケージが見つからない

```bash
python -m pip install --user markdown pygments
```

### 権限エラーが出る場合

```bash
# --user オプションを使用
python -m pip install --user markdown pygments
```

### Python が見つからない場合

Python 3.8以上がインストールされているか確認してください:

```bash
python --version
```

または

```bash
python3 --version
```

## なぜ pip install -e . が使えないのか?

通常の `pip install -e .` によるeditableインストールでは、setuptools が
`markdownup.egg-info/` ディレクトリ内に複数の `.txt` ファイルを生成します:

- `SOURCES.txt`
- `dependency_links.txt`
- `entry_points.txt`
- `requires.txt`
- `top_level.txt`

これらのファイルが暗号化されてしまうと、次回のインストールやアンインストール時に
エラーが発生します。

そのため、このプロジェクトでは依存パッケージを直接インストールし、
`markdownup.py` を直接実行する方法を推奨しています。
