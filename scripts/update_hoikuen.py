#!/usr/bin/env python3
"""
さいたま市保育施設データの統合・ジオコーディングスクリプト

認可保育所、小規模保育、事業所内保育、家庭的保育、認定こども園、認可外保育施設の
データを統合し、hoikuen_geo.csv を出力する。
さらに schools.html と schools_all_geo.csv を更新する。
"""

import csv
import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path
from collections import Counter

# === 設定 ===
BASE_DIR = Path(__file__).parent.parent  # scripts/ の親ディレクトリ
OPENDATA_DIR = BASE_DIR / "opendata"

# 認可系5ファイル（同一フォーマット）
NINKA_FILES = {
    "111007_ninkahoikusho.csv": "認可保育所",
    "111007_shokibohoikujigyo.csv": "小規模保育",
    "111007_jigyoshonai.csv": "事業所内保育",
    "111007_kateiteki.csv": "家庭的保育",
    "111007_ninteikodomoen.csv": "認定こども園",
}

# 認可外ファイル
NINKAGAI_FILE = "111007_ninkagaihoikushisetsu.csv"

# さいたま市の区一覧
WARDS = ["西区", "北区", "大宮区", "見沼区", "中央区", "桜区", "浦和区", "南区", "緑区", "岩槻区"]

# 元の施設_種別から表示用種別へのマッピング
SHUBETSU_MAP = {
    "民間保育所": "認可保育所",
    "公立保育所": "認可保育所",
    "小規模保育事業所": "小規模保育",
    "事業所内保育事業": "事業所内保育",
    "家庭的保育事業所": "家庭的保育",
    "認定こども園": "認定こども園",
}

# 出力ファイル
OUTPUT_CSV = BASE_DIR / "csv" / "hoikuen_geo.csv"
SCHOOLS_HTML = BASE_DIR / "docs" / "schools.html"
SCHOOLS_CSV = BASE_DIR / "csv" / "schools_all_geo.csv"


def extract_ward(address: str) -> str:
    """住所から区名を抽出する"""
    for ward in WARDS:
        if ward in address:
            return ward
    return ""


def normalize_phone(phone: str) -> str:
    """電話番号を正規化する（048-付加など）"""
    phone = phone.strip()
    if not phone:
        return ""
    # 既に市外局番がある場合はそのまま
    if phone.startswith("048") or phone.startswith("070") or phone.startswith("080") or phone.startswith("090"):
        return phone
    # 3桁-4桁 形式なら 048- を付加
    if re.match(r"^\d{3}-\d{4}$", phone):
        return "048-" + phone
    return phone


def normalize_address(address: str) -> str:
    """住所を正規化する（埼玉県さいたま市プレフィックス付加）"""
    address = address.strip()
    if not address:
        return ""
    # 既にフルアドレスの場合
    if address.startswith("埼玉県"):
        return address
    if address.startswith("さいたま市"):
        return "埼玉県" + address
    # 区名で始まる場合（認可外のパターン）
    for ward in WARDS:
        if address.startswith(ward):
            return "埼玉県さいたま市" + address
    return address


def geocode(address: str) -> tuple:
    """国土地理院APIでジオコーディングする"""
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + urllib.parse.quote(address)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data and len(data) > 0:
            coords = data[0]["geometry"]["coordinates"]
            # APIは [lng, lat] で返す
            lng, lat = coords[0], coords[1]
            return (str(lat), str(lng))
    except Exception as e:
        print(f"  ジオコーディング失敗: {address} -> {e}")
    return ("", "")


def read_ninka_files() -> list:
    """認可系5ファイルを読み込んで統合する"""
    rows = []
    for filename, display_shubetsu in NINKA_FILES.items():
        filepath = OPENDATA_DIR / filename
        print(f"読み込み中: {filename}")
        with open(filepath, "r", encoding="cp932") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # 施設_種別をマッピング
                orig_shubetsu = row.get("施設_種別", "").strip()
                shubetsu = SHUBETSU_MAP.get(orig_shubetsu, display_shubetsu)

                address = row.get("施設_住所_表記", "").strip()
                full_address = normalize_address(address)
                ward = extract_ward(full_address)

                phone = normalize_phone(row.get("施設_電話番号(市外局番048)", ""))

                # 保育時間を組み立て
                start_time = row.get("施設_保育開始時間", "").strip()
                end_time = row.get("施設_保育終了時間", "").strip()
                hoiku_time = ""
                if start_time and end_time:
                    hoiku_time = f"{start_time}～{end_time}"

                entry = {
                    "緯度": row.get("緯度", "").strip(),
                    "経度": row.get("経度", "").strip(),
                    "名称": row.get("施設_名称", "").strip(),
                    "住所": full_address,
                    "区": ward,
                    "種別": shubetsu,
                    "電話番号": phone,
                    "定員": row.get("施設_利用定員", "").strip(),
                    "保育時間": hoiku_time,
                    "対象": row.get("サービス_対象［保育可能日齢］", "").strip(),
                }
                rows.append(entry)
                count += 1
            print(f"  -> {count} 件")
    return rows


def read_ninkagai_file() -> list:
    """認可外保育施設ファイルを読み込む（ヘッダ2行、ジオコーディング必要）"""
    filepath = OPENDATA_DIR / NINKAGAI_FILE
    print(f"読み込み中: {NINKAGAI_FILE}")

    with open(filepath, "r", encoding="cp932") as f:
        # 1行目はメタデータ、スキップ
        f.readline()
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"  -> {len(raw_rows)} 件（ジオコーディング開始）")

    rows = []
    for i, row in enumerate(raw_rows):
        name = row.get("名称", "").strip()
        # 改行を含む名称をクリーンアップ
        name = re.sub(r"\s+", " ", name)
        if not name:
            continue

        address_raw = row.get("所在地", "").strip()
        # 改行を含む住所をクリーンアップ
        address_raw = re.sub(r"\s+", " ", address_raw)
        # 住所が区名で始まらない場合、所在区列から区名を付加する
        shozaiku = row.get("所在区", "").strip()
        has_ward = any(address_raw.startswith(w) for w in WARDS)
        if not has_ward and shozaiku and shozaiku in WARDS:
            address_raw = shozaiku + address_raw
        full_address = normalize_address(address_raw)
        ward = extract_ward(full_address)

        phone = normalize_phone(row.get("電話番号", ""))

        teiin = row.get("定員", "").strip()

        # ジオコーディング
        lat, lng = geocode(full_address)
        if lat:
            print(f"  [{i+1}/{len(raw_rows)}] {name}: OK ({lat}, {lng})")
        else:
            print(f"  [{i+1}/{len(raw_rows)}] {name}: ジオコーディング失敗")

        # APIレート制限対策
        time.sleep(0.3)

        entry = {
            "緯度": lat,
            "経度": lng,
            "名称": name,
            "住所": full_address,
            "区": ward,
            "種別": "認可外保育",
            "電話番号": phone,
            "定員": teiin,
            "保育時間": "",
            "対象": "",
        }
        rows.append(entry)

    return rows


def write_hoikuen_csv(rows: list):
    """hoikuen_geo.csv を出力する"""
    fieldnames = ["緯度", "経度", "名称", "住所", "区", "種別", "電話番号", "定員", "保育時間", "対象"]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n出力完了: {OUTPUT_CSV} ({len(rows)} 件)")


def print_summary(rows: list):
    """種別・区ごとの集計を表示する"""
    print("\n=== 種別ごとの件数 ===")
    shubetsu_count = Counter(r["種別"] for r in rows)
    for k, v in shubetsu_count.most_common():
        print(f"  {k}: {v}")

    print("\n=== 区ごとの件数 ===")
    ward_count = Counter(r["区"] for r in rows)
    for ward in WARDS:
        print(f"  {ward}: {ward_count.get(ward, 0)}")
    if "" in ward_count:
        print(f"  (不明): {ward_count['']}")

    print(f"\n合計: {len(rows)} 件")


def determine_settku(shubetsu: str, name: str) -> str:
    """種別と名称から設置区分を推定する"""
    # 認可保育所の公立/私立判定はソースデータの施設_種別による
    # ここでは保育施設は基本的に私立とする（公立は別途判定）
    return "私立"


def update_schools_html(nursery_rows: list):
    """schools.html の保育施設データを更新する"""
    print("\nschools.html を更新中...")

    with open(SCHOOLS_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    # 既存のDATAを解析
    m = re.search(r"const\s+DATA\s*=\s*(\[.*?\]);", content, re.DOTALL)
    if not m:
        print("エラー: schools.html にDATAが見つかりません")
        return

    existing_data = json.loads(m.group(1))
    print(f"  既存データ: {len(existing_data)} 件")

    # 保育施設系の種別（除外対象）
    nursery_types = {"認可保育所", "認可保育園", "小規模保育", "事業所内保育", "家庭的保育", "認可外保育", "認定こども園"}

    # 既存データから保育施設以外を保持
    non_nursery = [d for d in existing_data if d["種別"] not in nursery_types]
    print(f"  保育施設以外: {len(non_nursery)} 件")

    # 新しい保育施設データをschools.htmlフォーマットに変換
    new_nursery = []
    for r in nursery_rows:
        if not r["緯度"] or not r["経度"]:
            continue  # 座標なしはスキップ

        # 設置区分の推定
        settku = "私立"

        entry = {
            "緯度": r["緯度"],
            "経度": r["経度"],
            "名称": r["名称"],
            "住所": r["住所"],
            "区": r["区"],
            "種別": r["種別"],
            "設置区分": settku,
            "特別支援": "",
            "定員": r["定員"],
            "電話番号": r["電話番号"],
        }
        new_nursery.append(entry)

    print(f"  新しい保育施設: {len(new_nursery)} 件")

    # 統合
    all_data = non_nursery + new_nursery
    print(f"  統合後: {len(all_data)} 件")

    # DATAのJSONを生成
    data_json = json.dumps(all_data, ensure_ascii=False, separators=(",", ": "))

    # 種別フィルタのオプションを更新
    new_filter_options = """<select id="filterType">
      <option value="">全種別</option>
      <option value="認可保育所">認可保育所</option>
      <option value="小規模保育">小規模保育</option>
      <option value="事業所内保育">事業所内保育</option>
      <option value="家庭的保育">家庭的保育</option>
      <option value="認可外保育">認可外保育</option>
      <option value="認定こども園">認定こども園</option>
      <option value="幼稚園">幼稚園</option>
      <option value="小学校">小学校</option>
      <option value="中学校">中学校</option>
      <option value="高等学校">高等学校</option>
      <option value="中等教育学校">中等教育学校</option>
      <option value="特別支援学校">特別支援学校</option>
    </select>"""

    # schools.html を更新
    # DATAを置換
    content = re.sub(
        r"const\s+DATA\s*=\s*\[.*?\];",
        "const DATA = " + data_json + ";",
        content,
        flags=re.DOTALL,
    )

    # 種別フィルタを置換
    content = re.sub(
        r'<select id="filterType">.*?</select>',
        new_filter_options,
        content,
        flags=re.DOTALL,
    )

    # CSSに新しい種別のカードスタイルを追加
    # 既存のスタイルの後に追加
    new_css_rules = """    .card.小規模保育{border-left-color:#e91e63}
    .card.事業所内保育{border-left-color:#e91e63}
    .card.家庭的保育{border-left-color:#e91e63}
    .card.認可外保育{border-left-color:#ff5722}"""

    # 認可保育所のスタイルの後に追加
    if ".card.小規模保育" not in content:
        content = content.replace(
            "    .card.認可保育所{border-left-color:#e91e63}",
            "    .card.認可保育所{border-left-color:#e91e63}\n" + new_css_rules,
        )

    # ヒーローの説明文を更新
    content = content.replace(
        "認可保育所・幼稚園・こども園・小学校・中学校・高校・特別支援学校",
        "認可保育所・小規模保育・事業所内保育・家庭的保育・認可外保育・幼稚園・こども園・小学校・中学校・高校・特別支援学校",
    )

    # 保育時間・対象の情報もメタに含めるようrender関数を更新
    # 既存のmeta行を拡張
    old_meta_line = "if(d['電話番号'])meta+=' | TEL: '+d['電話番号'];"
    new_meta_line = (
        "if(d['電話番号'])meta+=' | TEL: '+d['電話番号'];\n"
        "    if(d['保育時間'])meta+=' | '+d['保育時間'];\n"
        "    if(d['対象'])meta+=' | '+d['対象'];"
    )
    if "d['保育時間']" not in content:
        content = content.replace(old_meta_line, new_meta_line)

    with open(SCHOOLS_HTML, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  schools.html 更新完了")
    return all_data


def update_schools_csv(all_data: list):
    """schools_all_geo.csv を更新する"""
    print("\nschools_all_geo.csv を更新中...")

    fieldnames = ["緯度", "経度", "名称", "住所", "区", "種別", "設置区分", "特別支援", "定員", "電話番号"]

    # 保育時間・対象がある場合はフィールド追加
    has_extra = any("保育時間" in d for d in all_data)
    if has_extra:
        fieldnames.extend(["保育時間", "対象"])

    # all_dataに保育時間・対象がないエントリにも空値を追加
    for d in all_data:
        if "保育時間" not in d:
            d["保育時間"] = ""
        if "対象" not in d:
            d["対象"] = ""

    with open(SCHOOLS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_data)

    print(f"  schools_all_geo.csv 更新完了 ({len(all_data)} 件)")


def main():
    print("=" * 60)
    print("さいたま市保育施設データ統合スクリプト")
    print("=" * 60)

    # 認可系ファイルの読み込み
    ninka_rows = read_ninka_files()

    # 認可外ファイルの読み込み（ジオコーディング含む）
    ninkagai_rows = read_ninkagai_file()

    # 統合
    all_nursery = ninka_rows + ninkagai_rows

    # hoikuen_geo.csv 出力
    write_hoikuen_csv(all_nursery)

    # 集計表示
    print_summary(all_nursery)

    # schools.html 更新
    all_data = update_schools_html(all_nursery)

    # schools_all_geo.csv 更新
    if all_data:
        update_schools_csv(all_data)

    print("\n全処理完了")


if __name__ == "__main__":
    main()
