# さいたま市 子育て・教育リソースまとめ

さいたま市の子育て・教育に関する施設情報を一覧・地図表示できるサイト。

---

## フォルダ構成

```
saitama_hattatsu_map/
│
├── docs/                        # HTMLページ（GitHub Pages公開用）
│   ├── portal.html              #   トップページ（全カテゴリへのリンク）
│   ├── index.html               #   1. 発達障害 医療機関（56件）
│   ├── juku.html                #   2. 補習塾・学習支援（17件）
│   ├── dayservice.html          #   3. 放課後デイ・児童発達支援（168件）
│   ├── clinics.html             #   4. 小児科・皮膚科・耳鼻科・眼科（361件）
│   ├── naraigoto.html           #   5. 習い事教室（129件）
│   ├── juku_shingaku.html       #   6. 進学塾・学習塾（183件）
│   ├── schools.html             #   7. 保育園・幼稚園・学校（890件）
│   └── houkago.html             #   8. 放課後児童クラブ・居場所（337件）
├── README.md
│
├── csv/                         # Google My Maps用CSV（全て緯度/経度付き、utf-8-sig）
│   ├── facilities.csv           #   1. 発達障害医療機関
│   ├── facilities_geo.csv       #   1. 同上（ジオコーディング済み）
│   ├── juku.csv                 #   2. 補習塾
│   ├── juku_geo.csv             #   2. 同上（ジオコーディング済み）
│   ├── dayservice.csv           #   3. 放課後デイ・児童発達支援
│   ├── dayservice_geo.csv       #   3. 同上（ジオコーディング済み）
│   ├── clinics_geo.csv          #   4. 全診療科まとめ（361件）
│   ├── clinics_小児科_geo.csv    #   4. 小児科のみ（70件）
│   ├── clinics_皮膚科_geo.csv    #   4. 皮膚科のみ（144件）
│   ├── clinics_耳鼻咽喉科_geo.csv #  4. 耳鼻咽喉科のみ（84件）
│   ├── clinics_眼科_geo.csv      #   4. 眼科のみ（103件）
│   ├── naraigoto_geo.csv        #   5. 全習い事まとめ（129件）
│   ├── naraigoto_*_geo.csv      #   5. ジャンル別（10種）
│   ├── juku_shingaku_geo.csv    #   6. 全進学塾まとめ（183件）
│   ├── juku_*_geo.csv           #   6. カテゴリ別
│   ├── hoikuen_geo.csv          #   7. 保育施設のみ（572件）
│   ├── schools_all_geo.csv      #   7. 全施設まとめ（890件）
│   ├── schools_*_geo.csv        #   7. 種別ごと
│   └── houkago_geo.csv          #   8. 放課後児童クラブ・居場所（337件）
│
├── scripts/                     # データ処理スクリプト
│   ├── update_clinics.py        #   医療機関データ更新
│   ├── update_hoikuen.py        #   保育施設データ更新
│   ├── create_houkago.py        #   放課後クラブ作成
│   ├── extract_clinics.py       #   厚労省データからの抽出（旧版、参考用）
│   └── geocode_all.py           #   国土地理院APIジオコーディング（汎用）
│
├── opendata/                    # さいたま市オープンデータ（展開済み）
│   ├── 111007_hospital_20260131.csv       # 医療機関一覧（utf-8-sig、1817件）
│   ├── 111007_hospital_2025051231.csv     # 医療機関一覧（過去版）
│   ├── 111007_ninkahoikusho.csv           # 認可保育所（cp932、275件）
│   ├── 111007_shokibohoikujigyo.csv       # 小規模保育事業（cp932、160件）
│   ├── 111007_jigyoshonai.csv             # 事業所内保育事業（cp932、15件）
│   ├── 111007_kateiteki.csv               # 家庭的保育事業（cp932、3件）
│   ├── 111007_ninteikodomoen.csv           # 認定こども園（cp932、21件）
│   ├── 111007_ninkagaihoikushisetsu.csv   # 認可外保育施設（cp932、別フォーマット）
│   ├── 111007_hokagojidoclub250401.csv    # 放課後児童クラブ（cp932、324件）
│   ├── 111007_ibasho250401.csv            # 放課後子ども居場所（cp932、13件）
│   └── 02-1/02-2_clinic_*.csv             # 厚労省データ（旧版、参考用）
│
├── archive/                     # ZIPアーカイブ・旧Excelファイル
│   ├── 【さいたま市】*.zip
│   ├── clinic_*.zip
│   ├── saitama_*.xlsx
│   ├── hattatu_jigyousyo.xlsx
│   └── clinic_data/
│
└── intermediate/                # 中間生成ファイル
    ├── *_gmap.csv               # ジオコーディング前CSV
    ├── *_data.json              # 中間JSON
    └── school_east.csv          # 文科省学校コード
```

---

## データ更新手順

### 前提
- Python 3 が利用可能であること
- インターネット接続（ジオコーディング用）

### 1. さいたま市オープンデータの取得

以下のサイトからZIPファイルをダウンロードし、プロジェクトフォルダに配置:
- https://opendata.city.saitama.lg.jp/

対象データセット:
| データ | ファイル名パターン | エンコーディング |
|---|---|---|
| 医療機関一覧 | `111007_hospital_YYYYMMDD.csv` | utf-8-sig |
| 認可保育所 | `111007_ninkahoikusho.csv` | cp932 |
| 小規模保育事業 | `111007_shokibohoikujigyo.csv` | cp932 |
| 事業所内保育事業 | `111007_jigyoshonai.csv` | cp932 |
| 家庭的保育事業 | `111007_kateiteki.csv` | cp932 |
| 認定こども園 | `111007_ninteikodomoen.csv` | cp932 |
| 認可外保育施設 | `111007_ninkagaihoikushisetsu.csv` | cp932（別フォーマット） |
| 放課後児童クラブ | `111007_hokagojidoclub*.csv` | cp932 |
| 放課後子ども居場所 | `111007_ibasho*.csv` | cp932 |

### 2. ZIPの展開

```bash
cd /Users/mezawahidetoshi/Desktop/saitama_hattatsu_map

# ZIPを opendata/ に展開
for z in 【さいたま市】*.zip; do
  unzip -o "$z" -d opendata/
done
```

### 3. 医療機関データの更新

```bash
# scripts/update_clinics.py 内の INPUT_FILE を最新のファイル名に変更してから実行
python3 scripts/update_clinics.py
```

**出力:**
- `csv/clinics_geo.csv` （全件）
- `csv/clinics_小児科_geo.csv` 等（診療科別）
- `clinics.html` （HTMLページの埋め込みデータも更新される）

**手動確認:**
- `portal.html` のカード4の統計値を出力結果に合わせて更新

### 4. 保育施設データの更新

```bash
python3 scripts/update_hoikuen.py
```

**出力:**
- `csv/hoikuen_geo.csv` （保育施設のみ）
- `csv/schools_all_geo.csv` （保育+学校の統合）
- `schools.html` （HTMLページの埋め込みデータも更新される）

**注意:**
- 認可外保育施設は緯度/経度がないため国土地理院APIでジオコーディングする（約0.5秒/件）
- schools.html の学校データ（小中高等）はそのまま保持される

**手動確認:**
- `portal.html` のカード7の統計値を出力結果に合わせて更新

### 5. 放課後児童クラブの更新

```bash
python3 scripts/create_houkago.py
```

**出力:**
- `csv/houkago_geo.csv`
- `houkago.html`

**手動確認:**
- `portal.html` のカード8の統計値を出力結果に合わせて更新

### 6. その他のデータ（手動対応が必要）

以下のカテゴリはオープンデータではなく手動収集のため、内容変更時は直接CSV/HTMLを編集:

| カテゴリ | HTMLファイル | CSVファイル | データソース |
|---|---|---|---|
| 1. 発達障害医療機関 | index.html | facilities.csv | 埼玉県公式リスト |
| 2. 補習塾・学習支援 | juku.html | juku.csv | 各塾公式サイト |
| 3. 放課後デイ | dayservice.html | dayservice.csv | さいたま市事業所リスト |
| 5. 習い事 | naraigoto.html | naraigoto.csv | コドモブースター等 |
| 6. 進学塾 | juku_shingaku.html | juku_shingaku.csv | 各塾公式サイト |

---

## 技術メモ

### ジオコーディング
- **国土地理院 API**: `https://msearch.gsi.go.jp/address-search/AddressSearch?q=住所`
- レスポンス: GeoJSON形式、`geometry.coordinates` = `[経度, 緯度]`（注意: 経度が先）
- レート制限: 0.5秒間隔で呼び出し
- フォールバック: 建物名除去 → 番地レベルまで切り詰め の順で再試行

### HTMLページの構造
- データは `const DATA = [...]` としてJSONで埋め込み
- JavaScript でフィルタリング（テキスト検索・カテゴリ・区）
- Google Maps リンク: `https://www.google.com/maps/search/?api=1&query=緯度,経度`

### CSVファイルの仕様
- エンコーディング: utf-8-sig（BOM付きUTF-8、Excelで文字化けしない）
- 先頭2列は常に `緯度, 経度`（Google My Mapsインポート用）
- Google My Maps でインポート時に「緯度」「経度」列を位置情報として選択

### さいたま市オープンデータのエンコーディング
- 医療機関（111007_hospital_*.csv）: **utf-8-sig**
- その他（保育所・放課後クラブ等）: **cp932**
- 認可外保育施設: cp932 + 2行ヘッダー（1行目はメタデータ、2行目が実際のヘッダー）
- 放課後児童クラブ: cp932 + ヘッダーにタブ文字混在（要クリーニング）

### 住所の正規化
- さいたま市オープンデータの住所は「西区西大宮1-47-1」のような短縮形
- 「埼玉県さいたま市」を先頭に付与してからジオコーディング/表示
- 区の抽出: `re.search(r'さいたま市(.{1,3}区)', addr)` または住所先頭から

---

## 一括更新コマンド

全データを一括更新する場合:

```bash
cd /Users/mezawahidetoshi/Desktop/saitama_hattatsu_map

# 1. ZIPを展開
for z in archive/【さいたま市】*.zip; do unzip -o "$z" -d opendata/; done

# 2. 各スクリプト実行
python3 scripts/update_clinics.py
python3 scripts/update_hoikuen.py
python3 scripts/create_houkago.py

# 3. portal.html の統計値を手動で確認・更新
```

---

## 現在のデータ件数（2026年3月時点）

| # | カテゴリ | 件数 | データソース |
|---|---|---|---|
| 1 | 発達障害 医療機関 | 56 | 埼玉県公式リスト |
| 2 | 補習塾・学習支援 | 17 | 手動収集 |
| 3 | 放課後デイ・児童発達支援 | 168 | さいたま市事業所リスト |
| 4 | 小児科・皮膚科・耳鼻科・眼科 | 361 | さいたま市オープンデータ（2026/1） |
| 5 | 習い事教室 | 129 | 手動収集 |
| 6 | 進学塾・学習塾 | 183 | 手動収集 |
| 7 | 保育園・幼稚園・学校 | 890 | さいたま市オープンデータ + 文科省学校コード |
| 8 | 放課後児童クラブ | 337 | さいたま市オープンデータ（2025/4） |
| | **合計** | **2,141** | |
