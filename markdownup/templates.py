# -*- coding: utf-8 -*-
"""HTMLテンプレート定義"""

# HTML テンプレート（ディレクトリ一覧表示用）
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


def get_print_html_template():
    """Markdown表示用HTMLテンプレートを返す（Ctrl+P印刷対応）"""
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
        /* 直接の子要素のみ対象（ネストされたul/ol等に二重適用しない） */
        body.mdf2h-presentation-mode .markdown-body > h3,
        body.mdf2h-presentation-mode .markdown-body > h4,
        body.mdf2h-presentation-mode .markdown-body > h5,
        body.mdf2h-presentation-mode .markdown-body > h6,
        body.mdf2h-presentation-mode .markdown-body > p,
        body.mdf2h-presentation-mode .markdown-body > ul,
        body.mdf2h-presentation-mode .markdown-body > ol,
        body.mdf2h-presentation-mode .markdown-body > blockquote,
        body.mdf2h-presentation-mode .markdown-body > pre,
        body.mdf2h-presentation-mode .markdown-body > table,
        body.mdf2h-presentation-mode .markdown-body > dl,
        body.mdf2h-presentation-mode .markdown-body > nav {{
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
        
        /* ========== 画像を含むリストアイテムのマーカー非表示 ========== */
        .markdown-body li.mdf2h-img-item {{
            list-style: none;
        }}
        
        /* ========== 画像サイズ切替（クリック対応） ========== */
        .markdown-body img.mdf2h-img-clickable {{
            cursor: pointer;
            transition: width 0.2s ease;
        }}
        .markdown-body img.mdf2h-img-medium {{
            width: 90%;
        }}
        .markdown-body img.mdf2h-img-small {{
            width: 80%;
        }}
        @media print {{
            .markdown-body img.mdf2h-img-medium,
            .markdown-body img.mdf2h-img-small {{
                width: auto;
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

        // ========== 画像を含むリストアイテムのマーカー非表示 ==========
        function initImageListItems() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;
            
            const listItems = article.querySelectorAll('li');
            listItems.forEach((li) => {{
                // li の直接の子ノードを走査し、画像のみかどうかを判定
                const children = Array.from(li.childNodes);
                let hasImg = false;
                let hasText = false;
                
                children.forEach((node) => {{
                    if (node.nodeType === Node.TEXT_NODE) {{
                        if (node.textContent.trim() !== '') {{
                            hasText = true;
                        }}
                    }} else if (node.nodeType === Node.ELEMENT_NODE) {{
                        if (node.tagName === 'IMG') {{
                            hasImg = true;
                        }} else if (node.tagName === 'P') {{
                            // <p> 内に <img> のみが含まれているかチェック
                            const pChildren = Array.from(node.childNodes);
                            let pHasImg = false;
                            let pHasText = false;
                            pChildren.forEach((pNode) => {{
                                if (pNode.nodeType === Node.TEXT_NODE) {{
                                    if (pNode.textContent.trim() !== '') {{
                                        pHasText = true;
                                    }}
                                }} else if (pNode.nodeType === Node.ELEMENT_NODE) {{
                                    if (pNode.tagName === 'IMG') {{
                                        pHasImg = true;
                                    }} else {{
                                        pHasText = true;
                                    }}
                                }}
                            }});
                            if (pHasImg && !pHasText) {{
                                hasImg = true;
                            }} else {{
                                hasText = true;
                            }}
                        }} else {{
                            hasText = true;
                        }}
                    }}
                }});
                
                if (hasImg && !hasText) {{
                    li.classList.add('mdf2h-img-item');
                }}
            }});
        }}
        
        // ========== 画像クリックで3段階サイズ切替 ==========
        function initImageSizeToggle() {{
            const article = document.querySelector('.markdown-body');
            if (!article) return;
            
            const images = article.querySelectorAll('img');
            images.forEach((img) => {{
                // ロゴ画像は除外
                if (img.classList.contains('mdf2h-logo')) return;
                // Mermaid内の画像は除外
                if (img.closest('.mermaid') || img.closest('pre.mermaid')) return;
                
                img.classList.add('mdf2h-img-clickable');
                
                img.addEventListener('click', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                    
                    if (img.classList.contains('mdf2h-img-small')) {{
                        // 小 -> 大（デフォルト）
                        img.classList.remove('mdf2h-img-small');
                    }} else if (img.classList.contains('mdf2h-img-medium')) {{
                        // 中 -> 小
                        img.classList.remove('mdf2h-img-medium');
                        img.classList.add('mdf2h-img-small');
                    }} else {{
                        // 大（デフォルト） -> 中
                        img.classList.add('mdf2h-img-medium');
                    }}
                }});
            }});
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
            initImageListItems();
            initImageSizeToggle();
            // DOM変更がすべて完了した後にプレゼン状態を復元
            restorePresentationState();
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
