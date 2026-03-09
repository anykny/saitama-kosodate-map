"""
放課後児童クラブ・放課後子ども居場所データの処理スクリプト

1. opendata/111007_hokagojidoclub250401.csv（放課後児童クラブ）
2. opendata/111007_ibasho250401.csv（放課後子ども居場所）
を読み込み、統合CSV・HTML一覧ページを作成し、portal.htmlを更新する
"""

import csv
import json
import re
from pathlib import Path
from collections import Counter

# === 定数 ===
BASE_DIR = Path(__file__).parent.parent  # scripts/ の親ディレクトリ
CLUB_CSV = BASE_DIR / "opendata" / "111007_hokagojidoclub250401.csv"
IBASHO_CSV = BASE_DIR / "opendata" / "111007_ibasho250401.csv"
OUTPUT_CSV = BASE_DIR / "csv" / "houkago_geo.csv"
OUTPUT_HTML = BASE_DIR / "docs" / "houkago.html"
PORTAL_HTML = BASE_DIR / "docs" / "portal.html"

# さいたま市の区一覧
WARDS = ["西区", "北区", "大宮区", "見沼区", "中央区", "桜区", "浦和区", "南区", "緑区", "岩槻区"]


def parse_club_csv(filepath):
    """放課後児童クラブCSVを読み込む"""
    with open(filepath, encoding="cp932") as f:
        content = f.read()

    lines = content.strip().split("\n")
    # ヘッダーのタブ・スペース・引用符を除去
    # ヘッダー: '"名称\t",種別 ,ＴＥＬ ,住所 ,緯度, 経度'
    records = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 6:
            continue
        name = parts[0].strip()
        shubetsu = parts[1].strip()
        tel = parts[2].strip()
        address = parts[3].strip()
        lat = parts[4].strip()
        lng = parts[5].strip()
        records.append({
            "名称": name,
            "種別": shubetsu,
            "電話番号": tel,
            "住所": address,
            "緯度": lat,
            "経度": lng,
        })
    return records


def parse_ibasho_csv(filepath):
    """放課後子ども居場所CSVを読み込む"""
    with open(filepath, encoding="cp932") as f:
        content = f.read()

    lines = content.strip().split("\n")
    # ヘッダー: '"名称\t",ＴＥＬ ,住所 ,緯度, 経度'
    records = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 5:
            continue
        name = parts[0].strip()
        tel = parts[1].strip()
        address = parts[2].strip()
        lat = parts[3].strip()
        lng = parts[4].strip()
        records.append({
            "名称": name,
            "種別": "放課後子ども居場所",
            "電話番号": tel,
            "住所": address,
            "緯度": lat,
            "経度": lng,
        })
    return records


def fix_phone(tel):
    """電話番号に048-プレフィックスを付与（携帯番号は除く）"""
    tel = tel.strip()
    if not tel:
        return ""
    # 080/090/070で始まる携帯番号はそのまま
    if re.match(r"^0[789]0", tel):
        return tel
    # すでに048-で始まる場合はそのまま
    if tel.startswith("048"):
        return tel
    # 短縮形に048-を付与
    return "048-" + tel


def fix_address(address):
    """住所に埼玉県さいたま市プレフィックスを付与"""
    address = address.strip()
    if address.startswith("埼玉県"):
        return address
    # すでに区名で始まる場合（例: 西区西大宮1-47-1）
    for ward in WARDS:
        if address.startswith(ward):
            return "埼玉県さいたま市" + address
    # その他の場合もプレフィックスを付与
    return "埼玉県さいたま市" + address


def extract_ward(address):
    """住所から区名を抽出"""
    m = re.search(r"さいたま市(.{1,3}区)", address)
    if m:
        return m.group(1)
    # プレフィックス付与前の住所から直接検出
    for ward in WARDS:
        if ward in address:
            return ward
    return ""


def main():
    # === CSV読み込み ===
    print("=== 放課後児童クラブ・居場所データ処理 ===\n")

    club_records = parse_club_csv(CLUB_CSV)
    print(f"放課後児童クラブ: {len(club_records)} 件読み込み")

    ibasho_records = parse_ibasho_csv(IBASHO_CSV)
    print(f"放課後子ども居場所: {len(ibasho_records)} 件読み込み")

    # === データ統合・加工 ===
    all_records = club_records + ibasho_records

    for rec in all_records:
        # 住所修正
        rec["住所"] = fix_address(rec["住所"])
        # 区の抽出
        rec["区"] = extract_ward(rec["住所"])
        # 電話番号修正
        rec["電話番号"] = fix_phone(rec["電話番号"])

    print(f"\n合計: {len(all_records)} 件\n")

    # === 種別ごとの集計 ===
    print("--- 種別ごとの件数 ---")
    shubetsu_count = Counter(rec["種別"] for rec in all_records)
    for s, c in shubetsu_count.most_common():
        print(f"  {s}: {c} 件")

    # === 区ごとの集計 ===
    print("\n--- 区ごとの件数 ---")
    ward_count = Counter(rec["区"] for rec in all_records)
    for ward in WARDS:
        if ward in ward_count:
            print(f"  {ward}: {ward_count[ward]} 件")

    # === CSV出力 ===
    columns = ["緯度", "経度", "名称", "住所", "区", "種別", "電話番号"]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_records)
    print(f"\n出力: {OUTPUT_CSV}")

    # === HTML作成 ===
    # JSON用データ作成
    json_data = []
    for rec in all_records:
        json_data.append({
            "緯度": rec["緯度"],
            "経度": rec["経度"],
            "名称": rec["名称"],
            "住所": rec["住所"],
            "区": rec["区"],
            "種別": rec["種別"],
            "電話番号": rec["電話番号"],
        })

    # 種別リスト（ドロップダウン用）
    shubetsu_list = sorted(shubetsu_count.keys())

    json_str = json.dumps(json_data, ensure_ascii=False)

    # 種別ドロップダウンオプション
    shubetsu_options = "\n".join(
        f'      <option value="{s}">{s}</option>' for s in shubetsu_list
    )

    # 区ドロップダウンオプション
    ward_options = "".join(
        f'<option value="{w}">{w}</option>' for w in WARDS
    )

    # 統計情報
    club_total = sum(c for s, c in shubetsu_count.items() if "児童クラブ" in s)
    ibasho_total = shubetsu_count.get("放課後子ども居場所", 0)
    kousetu = shubetsu_count.get("(公設)放課後児童クラブ", 0)
    minsetu = shubetsu_count.get("(民設）放課後児童クラブ", 0)

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>さいたま市 放課後児童クラブ・居場所事業一覧</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:"Hiragino Kaku Gothic ProN","Meiryo",sans-serif;background:#f5f5f5;color:#333}}
    .hero{{background:linear-gradient(135deg,#d35400,#e67e22);color:#fff;padding:40px 24px 20px;text-align:center;position:relative}}
    .hero h1{{font-size:1.4rem;margin-bottom:8px}}
    .hero p{{font-size:.85rem;opacity:.85}}
    .hero .back{{position:absolute;left:16px;top:16px;color:#fff;text-decoration:none;font-size:.85rem;opacity:.8}}
    .toolbar{{background:#fff;padding:12px 16px;border-bottom:1px solid #ddd;position:sticky;top:0;z-index:10}}
    .toolbar .row{{display:flex;gap:8px;flex-wrap:wrap;max-width:900px;margin:0 auto;align-items:center}}
    .toolbar input{{flex:1;min-width:140px;padding:8px 12px;border:1px solid #ccc;border-radius:6px;font-size:.88rem}}
    .toolbar select{{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:.85rem;background:#fff}}
    .container{{max-width:900px;margin:16px auto;padding:0 16px}}
    .count{{font-size:.82rem;color:#777;margin-bottom:12px}}
    .card{{background:#fff;border-radius:10px;box-shadow:0 1px 6px rgba(0,0,0,.08);padding:16px;margin-bottom:12px;border-left:5px solid #e67e22}}
    .card h3{{font-size:1rem;margin-bottom:4px;color:#d35400}}
    .card .meta{{font-size:.82rem;color:#666;line-height:1.5}}
    .card .tags{{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}}
    .tag{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.75rem;font-weight:bold;color:#fff}}
    .tag.kousetu{{background:#2980b9}}
    .tag.minsetu{{background:#e67e22}}
    .tag.ibasho{{background:#27ae60}}
    .card .links{{margin-top:8px;display:flex;gap:8px;flex-wrap:wrap}}
    .card .links a{{font-size:.82rem;padding:4px 12px;border-radius:5px;text-decoration:none;color:#fff}}
    .map-link{{background:#1a5276}}
    footer{{text-align:center;padding:24px;font-size:.78rem;color:#999}}
  </style>
</head>
<body>
<div class="hero">
  <a class="back" href="portal.html">← ポータルに戻る</a>
  <h1>さいたま市 放課後児童クラブ・居場所事業</h1>
  <p>放課後児童クラブ（公設・民設）・放課後子ども居場所事業の一覧</p>
</div>
<div class="toolbar">
  <div class="row">
    <input type="text" id="search" placeholder="名称・住所で検索...">
    <select id="filterShubetsu">
      <option value="">全種別</option>
{shubetsu_options}
    </select>
    <select id="filterWard">
      <option value="">全区</option>
      {ward_options}
    </select>
  </div>
</div>
<div class="container">
  <div class="count" id="count"></div>
  <div id="list"></div>
</div>
<footer>
  出典: さいたま市オープンデータ 放課後児童クラブ一覧・放課後子ども居場所一覧（令和7年4月1日時点）<br>
  ※ 情報は変更の可能性があります。各施設にご確認ください。
</footer>
<script>
const DATA = {json_str};
const listEl=document.getElementById('list'),countEl=document.getElementById('count');
const searchEl=document.getElementById('search'),shubetsuEl=document.getElementById('filterShubetsu');
const wardEl=document.getElementById('filterWard');
// タグのCSSクラスを種別から決定
function tagClass(s){{
  if(s.includes('公設'))return 'kousetu';
  if(s.includes('民設'))return 'minsetu';
  return 'ibasho';
}}
function render(){{
  const q=searchEl.value.toLowerCase(),s=shubetsuEl.value,w=wardEl.value;
  const f=DATA.filter(d=>{{
    if(q&&!(d['名称'].toLowerCase().includes(q)||d['住所'].toLowerCase().includes(q)))return false;
    if(s&&d['種別']!==s)return false;
    if(w&&d['区']!==w)return false;
    return true;
  }});
  countEl.textContent=f.length+' 件表示 / 全 '+DATA.length+' 件';
  listEl.innerHTML=f.map(d=>{{
    const mapUrl='https://www.google.com/maps/search/?api=1&query='+d['緯度']+','+d['経度'];
    let meta=d['住所'];
    if(d['電話番号'])meta+='<br>TEL: '+d['電話番号'];
    meta+='<br>種別: '+d['種別'];
    return '<div class="card"><h3>'+d['名称']+'</h3>'+
      '<div class="tags"><span class="tag '+tagClass(d['種別'])+'">'+d['種別']+'</span></div>'+
      '<div class="meta">'+meta+'</div>'+
      '<div class="links"><a class="map-link" href="'+mapUrl+'" target="_blank">Google Maps</a></div></div>';
  }}).join('');
}}
searchEl.addEventListener('input',render);shubetsuEl.addEventListener('change',render);
wardEl.addEventListener('change',render);
render();
</script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"出力: {OUTPUT_HTML}")

    # === portal.html更新 ===
    update_portal(len(all_records), club_total, ibasho_total, kousetu, minsetu)


def update_portal(total, club_total, ibasho_total, kousetu, minsetu):
    """portal.htmlに放課後児童クラブカードを追加"""
    with open(PORTAL_HTML, "r", encoding="utf-8") as f:
        portal = f.read()

    # 既にhoukago カードがある場合はスキップ
    if "card houkago" in portal:
        print("portal.html: 放課後児童クラブカードは既に存在します（スキップ）")
        return

    # CSSに.card.houkago追加
    portal = portal.replace(
        ".card.schools{border-left-color:#2c3e50}",
        ".card.schools{border-left-color:#2c3e50}\n    .card.houkago{border-left-color:#d35400}"
    )

    # 新しいカードのHTML
    new_card = f"""
  <div class="card houkago">
    <h2>8. 放課後児童クラブ・居場所事業</h2>
    <div class="desc">
      さいたま市オープンデータ（令和7年4月1日時点）の放課後児童クラブ・放課後子ども居場所事業全件。
      種別・区で絞り込み可能。Google Maps リンク付き。
    </div>
    <div class="stats">
      <div class="stat"><div class="num">{total}</div><div class="label">全施設</div></div>
      <div class="stat"><div class="num">{minsetu}</div><div class="label">民設クラブ</div></div>
      <div class="stat"><div class="num">{kousetu}</div><div class="label">公設クラブ</div></div>
      <div class="stat"><div class="num">{ibasho_total}</div><div class="label">子ども居場所</div></div>
    </div>
    <a class="link" href="houkago.html">一覧を見る</a>
    <a class="csv" href="houkago_geo.csv" download>CSV (My Maps用)</a>
  </div>"""

    # schoolsカードの閉じタグの後に挿入
    # </div> の後、</div>\n<footer> の前に挿入
    portal = portal.replace(
        """    <a class="csv" href="schools_all_geo.csv" download>CSV (My Maps用)</a>
  </div>
</div>""",
        f"""    <a class="csv" href="schools_all_geo.csv" download>CSV (My Maps用)</a>
  </div>
{new_card}
</div>"""
    )

    # 出典にさいたま市オープンデータを追加
    if "さいたま市オープンデータ" not in portal:
        portal = portal.replace(
            "埼玉県認可保育所一覧",
            "埼玉県認可保育所一覧 / さいたま市オープンデータ"
        )

    with open(PORTAL_HTML, "w", encoding="utf-8") as f:
        f.write(portal)
    print(f"更新: {PORTAL_HTML}")


if __name__ == "__main__":
    main()
