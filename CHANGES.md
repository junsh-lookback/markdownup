# 修正内容まとめ

## 問題

1. **エンコーディングエラー**: 別のPCでMarkdownファイルを表示しようとすると、UTF-8でデコードできないエラーが発生
2. **インストールエラー**: `.txt`ファイルが自動暗号化される環境で `pip install -e .` が失敗

## 解決策

### 1. エンコーディング自動検出機能の追加

`markdownup.py` の `send_markdown_as_html()` メソッドを修正し、複数のエンコーディングを順番に試すように変更:

- UTF-8
- UTF-8 with BOM
- Shift_JIS
- CP932 (Windows)
- EUC-JP
- ISO-2022-JP
- Latin-1

どのエンコーディングでも読めない場合は、エラー文字を置換文字に変換して表示。

### 2. インストール方法の変更

`.txt` ファイルの暗号化問題を回避するため、以下を実装:

- `install.sh` (Linux/macOS用)
- `install.bat` (Windows用)
- `INSTALL.md` (詳細な手順書)

依存パッケージを直接インストールし、`markdownup.py` を直接実行する方法を採用。

### 3. ドキュメントの更新

- `README.md`: インストール手順を更新
- `.gitignore`: `.egg-info/*.txt` を追加(暗号化対策)

## 使用方法

### インストール

**Linux/macOS:**
```bash
bash install.sh
```

**Windows:**
```cmd
install.bat
```

または手動で:
```bash
python -m pip install --user markdown pygments
```

### サーバー起動

```bash
python markdownup.py -d ./
```

### エイリアス作成(オプション)

**Linux/macOS (~/.bashrc に追加):**
```bash
alias markdownup='python /path/to/markdownup.py'
```

**Windows (markdownup.bat を作成):**
```batch
@echo off
python "C:\path\to\markdownup.py" %*
```

## テスト結果

✅ エンコーディングエラーの解決を確認
✅ サーバーが正常に起動
✅ README.mdが正しく表示される
✅ 依存パッケージのインストールが成功

## 注意事項

- Python 3.8以上が必要
- `markdown` と `pygments` パッケージが必要(最適な表示のため)
- `.txt` ファイルが暗号化される環境では `pip install -e .` は使用不可
