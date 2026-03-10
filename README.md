# さいたま市 子育て・教育リソースまとめ

さいたま市の子育て・教育に関する施設情報を一覧・地図表示できるサイト。
GitHub Pagesで公開し、Notionに埋め込んで利用する。

- **公開URL**: https://anykny.github.io/saitama-kosodate-map/portal.html
- **リポジトリ**: https://github.com/anykny/saitama-kosodate-map
- 全ページに `noindex, nofollow` を設定済み（検索エンジンに表示されない）

---

## フォルダ構成

```
saitama_hattatsu_map/
│
├── docs/                        # HTMLページ（GitHub Pages公開用、/docs で配信）
│   ├── portal.html              #   トップページ（全カテゴリへのリンク）
│   ├── index.html               #   1. 発達障害 医療機関（56件）
│   ├── juku.html                #   2. 補習塾・学習支援（17件）
│   ├── dayservice.html          #   3. 放課後デイ・児童発達支援（168件）
│   ├── clinics.html             #   4. 小児科・皮膚科・耳鼻科・眼科（361件）
│   ├── naraigoto.html           #   5. 習い事教室（129件）
│   ├── juku_shingaku.html       #   6. 進学塾・学習塾（183件）
│   ├── schools.html             #   7. 保育園・幼稚園・学校（890件）
│   └── houkago.html             #   8. 放課後児童クラブ・居場所（337件）
│
├── csv/                         # Google My Maps用CSV（全て緯度/経度付き、utf-8-sig）
│   ├── clinics_geo.csv          #   4. 全診療科まとめ + 診療科別CSV
│   ├── hoikuen_geo.csv          #   7. 保育施設のみ（572件）
│   ├── schools_all_geo.csv      #   7. 保育+学校の統合（890件）
│   ├── houkago_geo.csv          #   8. 放課後児童クラブ・居場所（337件）
│   ├── facilities.csv / _geo    #   1. 発達障害医療機関
│   ├── juku.csv / _geo          #   2. 補習塾
│   ├── dayservice.csv / _geo    #   3. 放課後デイ
│   ├── naraigoto_geo.csv        #   5. 習い事 + ジャンル別CSV
│   └── juku_shingaku_geo.csv    #   6. 進学塾 + カテゴリ別CSV
│
├── scripts/                     # データ処理スクリプト
│   ├── update_clinics.py        #   医療機関データ更新
│   ├── update_hoikuen.py        #   保育施設データ更新
│   ├── create_houkago.py        #   放課後クラブ作成
│   ├── extract_clinics.py       #   厚労省データからの抽出（旧版、参考用）
│   └── geocode_all.py           #   国土地理院APIジオコーディング（汎用）
│
├── opendata/                    # さいたま市オープンデータ（展開済み、.gitignore対象）
│   ├── 111007_hospital_*.csv    #   医療機関一覧（utf-8-sig）
│   ├── 111007_ninkahoikusho.csv #   認可保育所（cp932）
│   ├── 111007_shokibohoikujigyo.csv  # 小規模保育事業（cp932）
│   ├── 111007_jigyoshonai.csv   #   事業所内保育事業（cp932）
│   ├── 111007_kateiteki.csv     #   家庭的保育事業（cp932）
│   ├── 111007_ninteikodomoen.csv #  認定こども園（cp932）
│   ├── 111007_ninkagaihoikushisetsu.csv  # 認可外保育施設（cp932、別フォーマット）
│   ├── 111007_hokagojidoclub*.csv  # 放課後児童クラブ（cp932）
│   └── 111007_ibasho*.csv      #   放課後子ども居場所（cp932）
│
├── archive/                     # ZIPアーカイブ・旧Excel（.gitignore対象）
├── intermediate/                # 中間生成ファイル（.gitignore対象）
├── .gitignore
└── README.md
```

---

## データ更新手順（一連の作業の再現方法）

### 前提
- Python 3
- インターネット接続（ジオコーディング・GitHub Pages公開用）
- `gh` CLI（`brew install gh && gh auth login`）

### 1. さいたま市オープンデータの取得

https://opendata.city.saitama.lg.jp/ から以下のZIPをダウンロードし、プロジェクトフォルダに配置:

| データ | ファイル名パターン | エンコーディング |
|---|---|---|
| 医療機関一覧 | `111007_hospital_YYYYMMDD.csv` | utf-8-sig |
| 認可保育所 | `111007_ninkahoikusho.csv` | cp932 |
| 小規模保育事業 | `111007_shokibohoikujigyo.csv` | cp932 |
| 事業所内保育事業 | `111007_jigyoshonai.csv` | cp932 |
| 家庭的保育事業 | `111007_kateiteki.csv` | cp932 |
| 認定こども園 | `111007_ninteikodomoen.csv` | cp932 |
| 認可外保育施設 | `111007_ninkagaihoikushisetsu.csv` | cp932（2行ヘッダー、別フォーマット） |
| 放課後児童クラブ | `111007_hokagojidoclub*.csv` | cp932（ヘッダーにタブ混在） |
| 放課後子ども居場所 | `111007_ibasho*.csv` | cp932（ヘッダーにタブ混在） |

### 2. ZIPの展開

```bash
cd /Users/mezawahidetoshi/Desktop/saitama_hattatsu_map

# 新しくダウンロードしたZIPをopendata/に展開
for z in 【さいたま市】*.zip; do
  unzip -o "$z" -d opendata/
done
# 展開後、ZIPはarchive/に移動
mv 【さいたま市】*.zip archive/
```

### 3. 医療機関データの更新（カテゴリ4）

```bash
# scripts/update_clinics.py 内の INPUT_FILE を最新のファイル名に変更してから実行
python3 scripts/update_clinics.py
```

**処理内容:**
- `opendata/111007_hospital_YYYYMMDD.csv`（全1817件）から小児科/皮膚科/耳鼻咽喉科/眼科を抽出
- 診療科目は省略形（小/皮/耳/眼 等）で全角スペース区切り。美容系（美皮等）は除外
- 施設名で美容/AGA/脱毛/聖心を含むものを除外
- 座標欠損分は国土地理院APIでジオコーディング
- `docs/clinics.html` のDATA部分を自動更新

**出力:**
- `csv/clinics_geo.csv`（全件）
- `csv/clinics_小児科_geo.csv` 等（診療科別）
- `docs/clinics.html`（HTMLの埋め込みデータ更新）

### 4. 保育施設データの更新（カテゴリ7の保育部分）

```bash
python3 scripts/update_hoikuen.py
```

**処理内容:**
- 認可系5ファイル（同一12カラムフォーマット、cp932）を統合
- 認可外保育施設（別フォーマット、1行目メタデータ+2行目ヘッダー）を国土地理院APIでジオコーディング
- 住所に「埼玉県さいたま市」プレフィックス付与、電話番号に「048-」付与
- `docs/schools.html` の保育施設部分のみ差し替え（学校データは保持）
- 種別フィルタに小規模保育/事業所内保育/家庭的保育/認可外保育を追加

**出力:**
- `csv/hoikuen_geo.csv`（保育施設のみ）
- `csv/schools_all_geo.csv`（保育+学校の統合）
- `docs/schools.html`（HTMLの埋め込みデータ更新）

### 5. 放課後児童クラブの更新（カテゴリ8）

```bash
python3 scripts/create_houkago.py
```

**処理内容:**
- 放課後児童クラブCSV（ヘッダーのタブ文字をクリーニング）と居場所CSVを統合
- 住所に「埼玉県さいたま市」プレフィックス付与
- 電話番号に「048-」付与（080/090/070携帯は除外）
- `docs/houkago.html` を生成、`docs/portal.html` にカード追加（未存在時のみ）

**出力:**
- `csv/houkago_geo.csv`
- `docs/houkago.html`

### 6. portal.html の統計値更新

各スクリプトの出力結果（件数）を確認し、`docs/portal.html` のカード内の数値を手動で更新する。

### 7. GitHub Pagesに公開

```bash
git add docs/ csv/ scripts/ README.md
git commit -m "データ更新 YYYY-MM"
git push origin main
```

- プッシュ後、数十秒で https://anykny.github.io/saitama-kosodate-map/ に反映される
- デプロイ確認: `gh api repos/anykny/saitama-kosodate-map/pages/builds --jq '.[0].status'`

### 8. Notionへの埋め込み

1. Notionページで `/embed` ブロックを追加
2. URLを貼り付け:
   - ポータル: `https://anykny.github.io/saitama-kosodate-map/portal.html`
   - 各カテゴリ: `https://anykny.github.io/saitama-kosodate-map/clinics.html` 等

---

## その他のデータ（手動対応が必要）

以下のカテゴリはオープンデータではなく手動収集のため、内容変更時は直接CSV/HTMLを編集:

| カテゴリ | HTMLファイル | CSVファイル | データソース |
|---|---|---|---|
| 1. 発達障害医療機関 | docs/index.html | csv/facilities.csv | 埼玉県公式リスト |
| 2. 補習塾・学習支援 | docs/juku.html | csv/juku.csv | 各塾公式サイト |
| 3. 放課後デイ | docs/dayservice.html | csv/dayservice.csv | さいたま市事業所リスト |
| 5. 習い事 | docs/naraigoto.html | csv/naraigoto.csv | コドモブースター等 |
| 6. 進学塾 | docs/juku_shingaku.html | csv/juku_shingaku.csv | 各塾公式サイト |

---

## 一括更新コマンド

```bash
cd /Users/mezawahidetoshi/Desktop/saitama_hattatsu_map

# 1. ZIPを展開
for z in 【さいたま市】*.zip; do unzip -o "$z" -d opendata/; done
mv 【さいたま市】*.zip archive/

# 2. 各スクリプト実行（医療機関のINPUT_FILEは事前に確認）
python3 scripts/update_clinics.py
python3 scripts/update_hoikuen.py
python3 scripts/create_houkago.py

# 3. portal.htmlの統計値を手動で確認・更新

# 4. GitHubに反映
git add docs/ csv/ scripts/ README.md
git commit -m "データ更新 $(date +%Y-%m)"
git push origin main
```

---

## 技術メモ

### ジオコーディング
- **国土地理院 API**: `https://msearch.gsi.go.jp/address-search/AddressSearch?q=住所`
- レスポンス: GeoJSON形式、`geometry.coordinates` = `[経度, 緯度]`（注意: 経度が先）
- レート制限: 0.3〜0.5秒間隔で呼び出し
- フォールバック: 建物名除去 → 番地レベルまで切り詰め の順で再試行

### HTMLページの構造
- データは `const DATA = [...]` としてJSONで埋め込み
- JavaScript でフィルタリング（テキスト検索・カテゴリ・区）
- Google Maps リンク: `https://www.google.com/maps/search/?api=1&query=緯度,経度`
- 全ページに `<meta name="robots" content="noindex, nofollow">` を設定
- CSVリンクは `../csv/xxx.csv` で参照（docs/ から csv/ への相対パス）

### CSVファイルの仕様
- エンコーディング: utf-8-sig（BOM付きUTF-8、Excelで文字化けしない）
- 先頭2列は常に `緯度, 経度`（Google My Mapsインポート用）
- Google My Maps でインポート時に「緯度」「経度」列を位置情報として選択

### さいたま市オープンデータのエンコーディング
- 医療機関（111007_hospital_*.csv）: **utf-8-sig**
- その他（保育所・放課後クラブ等）: **cp932**
- 認可外保育施設: cp932 + 2行ヘッダー（1行目はメタデータ、2行目が実際のヘッダー）
- 放課後児童クラブ/居場所: cp932 + ヘッダーにタブ文字混在（要クリーニング）

### 住所の正規化
- さいたま市オープンデータの住所は「西区西大宮1-47-1」のような短縮形
- 「埼玉県さいたま市」を先頭に付与してからジオコーディング/表示
- 区の抽出: `re.search(r'さいたま市(.{1,3}区)', addr)` または住所先頭から

### GitHub Pages設定
- リポジトリ: `anykny/saitama-kosodate-map`（public）
- Source: `main` ブランチ / `/docs` フォルダ
- 設定コマンド: `gh api repos/anykny/saitama-kosodate-map/pages -X POST -f "build_type=legacy" -f "source[branch]=main" -f "source[path]=/docs"`

---

## 現在のデータ件数（2026年3月時点）

| # | カテゴリ | 件数 | データソース | 更新方法 |
|---|---|---|---|---|
| 1 | 発達障害 医療機関 | 56 | 埼玉県公式リスト | 手動 |
| 2 | 補習塾・学習支援 | 17 | 手動収集 | 手動 |
| 3 | 放課後デイ・児童発達支援 | 168 | さいたま市事業所リスト | 手動 |
| 4 | 小児科・皮膚科・耳鼻科・眼科 | 361 | さいたま市オープンデータ（2026/1） | `update_clinics.py` |
| 5 | 習い事教室 | 129 | 手動収集 | 手動 |
| 6 | 進学塾・学習塾 | 183 | 手動収集 | 手動 |
| 7 | 保育園・幼稚園・学校 | 890 | さいたま市オープンデータ + 文科省学校コード | `update_hoikuen.py` |
| 8 | 放課後児童クラブ | 337 | さいたま市オープンデータ（2025/4） | `create_houkago.py` |
| | **合計** | **2,141** | | |

## 公開ページURL一覧

| ページ | URL |
|---|---|
| ポータル | https://anykny.github.io/saitama-kosodate-map/portal.html |
| 発達障害医療機関 | https://anykny.github.io/saitama-kosodate-map/index.html |
| 補習塾 | https://anykny.github.io/saitama-kosodate-map/juku.html |
| 放課後デイ | https://anykny.github.io/saitama-kosodate-map/dayservice.html |
| 小児科等 | https://anykny.github.io/saitama-kosodate-map/clinics.html |
| 習い事 | https://anykny.github.io/saitama-kosodate-map/naraigoto.html |
| 進学塾 | https://anykny.github.io/saitama-kosodate-map/juku_shingaku.html |
| 保育園・学校 | https://anykny.github.io/saitama-kosodate-map/schools.html |
| 放課後クラブ | https://anykny.github.io/saitama-kosodate-map/houkago.html |
