# インストール手順

## 方法1: pip install（推奨 - どこからでも実行可能）

プロジェクトのルートディレクトリで以下を実行します:

```bash
pip install --user .
```

インストール後は、どのディレクトリからでも `markdownup` コマンドが使えます:

```bash
# ヘルプを表示（引数なしで実行）
markdownup

# サービスをバックグラウンドで起動（カレントディレクトリ）
markdownup --start

# ディレクトリを指定して起動
markdownup --start -d /path/to/docs

# ポートを指定して起動
markdownup --start --port 8080

# ヘッダーモードを有効にして起動
markdownup --start --header

# サービスを停止
markdownup --stop
```

> **注意**: `pip install -e .`（editable インストール）は使用しないでください。
> 理由は本ページ末尾の「なぜ pip install -e . が使えないのか？」を参照してください。

### アンインストール

```bash
pip uninstall markdownup
```

## 方法2: 依存パッケージのみインストール（pip install が使えない環境向け）

方法1 が失敗する場合の代替手段です。

### Linux/macOS の場合

```bash
bash install.sh
```

または手動で:

```bash
# 依存パッケージをインストール
python -m pip install --user markdown pygments
```

### Windows の場合

```cmd
REM 依存パッケージをインストール
python -m pip install --user markdown pygments
```

### 方法2 での使用方法

プロジェクトのルートディレクトリから `python -m markdownup` で実行します:

```bash
# ヘルプを表示（引数なしで実行）
python -m markdownup

# サービスをバックグラウンドで起動
python -m markdownup --start

# ディレクトリを指定して起動
python -m markdownup --start -d /path/to/docs

# ポートを指定して起動
python -m markdownup --start --port 8080

# サービスを停止
python -m markdownup --stop
```

## トラブルシューティング

### markdown パッケージが見つからない

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

### モジュールが見つからないエラー（方法2 の場合）

`python -m markdownup` 実行時に `No module named markdownup` と表示される場合、
プロジェクトのルートディレクトリ（`markdownup/` フォルダが存在するディレクトリ）で
実行しているか確認してください:

```bash
cd /path/to/markdownup-project
python -m markdownup --start
```

## なぜ pip install -e . が使えないのか？

`pip install -e .`（editable インストール）では、setuptools が
**プロジェクトディレクトリ内**に `markdownup.egg-info/` を作成し、
その中に複数の `.txt` ファイルを生成します（`SOURCES.txt`, `requires.txt` 等）。

一部のPC環境では `.txt` ファイルが自動的に暗号化されるため、
これらのファイルが暗号化されるとインストールやアンインストール時にエラーが発生します。

本プロジェクトではビルドバックエンドに **hatchling** を採用しています。
hatchling は setuptools と異なり、ビルド時にプロジェクトディレクトリ内に
`.egg-info/`（`.txt` ファイル）を生成しないため、
`pip install --user .` で問題なくインストールできます。
