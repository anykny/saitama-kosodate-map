#!/usr/bin/env python3
"""さいたま市オープンデータ（医療機関一覧CSV）から
小児科・皮膚科・耳鼻咽喉科・眼科を抽出してCSV生成 + clinics.html更新"""

import csv
import re
import json
import unicodedata
import urllib.request
import urllib.parse
import time
from collections import Counter

# === 設定 ===
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, 'opendata/111007_hospital_20260131.csv')
OUTPUT_CSV = os.path.join(BASE_DIR, 'csv/clinics_geo.csv')
HTML_FILE = os.path.join(BASE_DIR, 'docs/clinics.html')

# 対象診療科の省略形マッピング
# データでは「小」=小児科、「皮」=皮膚科、「眼」=眼科、「耳」=耳鼻咽喉科 等の省略形
# 「美皮」=美容皮膚科は除外対象

# 施設名で除外するキーワード
EXCLUDE_KEYWORDS = ['美容', 'AGA', 'aga', 'メンズ脱毛', '脱毛', '聖心']


def normalize(text):
    """テキストをNFKC正規化"""
    return unicodedata.normalize('NFKC', text)


def classify_specialities(shinryoukamoku):
    """診療科目文字列から対象カテゴリを判定。
    省略形（全角スペース区切り）を解析する。
    美容系は除外。"""
    kamoku_norm = normalize(shinryoukamoku)
    # 全角スペースで分割
    items = [s.strip() for s in kamoku_norm.split('\u3000') if s.strip()]

    categories = set()
    for item in items:
        # 美容皮膚科は除外
        if '美' in item:
            continue

        # 小児科判定: 「小」で始まり、歯科系・外科系でないもの
        # 「小」「小アレ」「小皮」「小耳」「小眼」「小循内」「小泌内」「小糖内」
        # 除外: 「小歯」「小外」「小児整」「小児矯正歯科」
        if item.startswith('小'):
            if item in ('小歯', '小外', '小児整', '小児矯正歯科'):
                pass  # 歯科・外科系は対象外
            else:
                categories.add('小児科')

        # 皮膚科判定: 「皮」を含む（「美皮」は上で除外済み）
        # 「皮」「皮膚」「皮泌」「アレ皮」「小皮」「頭部皮」等
        # 「男性皮膚科」も含む
        if '皮' in item or '皮膚' in item:
            if '美' not in item:
                categories.add('皮膚科')

        # 耳鼻咽喉科判定: 「耳」を含む
        # 「耳」「耳、アレ」「小耳」等
        if '耳' in item:
            categories.add('耳鼻咽喉科')

        # 眼科判定: 「眼」を含む
        # 「眼」「小眼」「神眼」等
        if '眼' in item:
            categories.add('眼科')

    return sorted(categories)


def geocode_gsi(address):
    """国土地理院APIでジオコーディング"""
    try:
        url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(address)
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data:
            coords = data[0]['geometry']['coordinates']
            return str(coords[1]), str(coords[0])  # 緯度, 経度
    except Exception as e:
        print(f"  ジオコーディングエラー: {e}")
    return None, None


def main():
    # === 1. CSVデータ読み込みと抽出 ===
    print("=== さいたま市オープンデータ読み込み ===")
    print(f"  入力ファイル: {INPUT_FILE}")

    results = []
    total_rows = 0

    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1

            # 診療科目から対象カテゴリを判定
            kamoku = row.get('診療科目', '')
            categories = classify_specialities(kamoku)
            if not categories:
                continue

            # 施設名を正規化
            name = normalize(row.get('名称', ''))

            # 施設名で美容系・AGA系を除外
            name_lower = name.lower()
            if any(kw.lower() in name_lower for kw in EXCLUDE_KEYWORDS):
                continue

            # 住所を取得
            addr = normalize(row.get('所在地＿連結表記', ''))

            # さいたま市フィルタ（念のため確認）
            if 'さいたま市' not in addr:
                continue

            # 区を抽出
            m = re.search(r'さいたま市(.{1,3}区)', addr)
            ward = m.group(1) if m else ''

            # 埼玉県プレフィックス追加
            if addr.startswith('さいたま市'):
                addr = '埼玉県' + addr

            # 緯度経度
            lat = row.get('緯度', '').strip()
            lng = row.get('経度', '').strip()

            # 電話番号
            tel = normalize(row.get('電話番号', '').strip())

            # 診療時間
            time_detail = normalize(row.get('診療時間詳細（午前・午後など）', '').strip())
            start_time = row.get('診療開始時間', '').strip()
            end_time = row.get('診療終了時間', '').strip()
            if time_detail and time_detail != '00:00~00:00':
                shinryou_time = time_detail
            elif start_time and end_time and start_time != '00:00':
                shinryou_time = f'{start_time}~{end_time}'
            else:
                shinryou_time = ''

            # 休診日等
            rest = normalize(row.get('休診日等', '').strip())

            # URL（このデータにはURL列がない）
            url = ''

            results.append({
                '緯度': lat,
                '経度': lng,
                '名称': name,
                '住所': addr,
                '区': ward,
                '診療科': '・'.join(categories),
                '電話番号': tel,
                '診療時間': shinryou_time,
                '休診日等': rest,
                'URL': url,
            })

    print(f"  全{total_rows}行中、対象施設: {len(results)}件\n")

    # === 2. カテゴリ別・区別カウント ===
    cat_counts = Counter()
    for r in results:
        for c in r['診療科'].split('・'):
            cat_counts[c] += 1

    print("=== 診療科別件数 ===")
    for cat in ['小児科', '皮膚科', '耳鼻咽喉科', '眼科']:
        print(f"  {cat}: {cat_counts.get(cat, 0)}件")

    ward_counts = Counter(r['区'] for r in results)
    print("\n=== 区別件数 ===")
    ward_order = ['西区', '北区', '大宮区', '見沼区', '中央区', '桜区', '浦和区', '南区', '緑区', '岩槻区']
    for ward in ward_order:
        print(f"  {ward}: {ward_counts.get(ward, 0)}件")

    # === 3. 座標欠損のジオコーディング ===
    zero_coords = [r for r in results if not r['緯度'] or r['緯度'] in ('0', '0.0', '')]
    if zero_coords:
        print(f"\n=== 座標欠損 {len(zero_coords)}件をジオコーディング ===")
        for r in zero_coords:
            lat, lng = geocode_gsi(r['住所'])
            if lat:
                r['緯度'] = lat
                r['経度'] = lng
                print(f"  OK: {r['名称']}")
            else:
                print(f"  FAIL: {r['名称']}")
            time.sleep(0.5)
    else:
        print("\n全施設の緯度経度が取得済みです。")

    # === 4. CSV出力 ===
    fieldnames = ['緯度', '経度', '名称', '住所', '区', '診療科', '電話番号', '診療時間', '休診日等', 'URL']

    # メインCSV
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"\n=== 出力完了: {OUTPUT_CSV} ({len(results)}件) ===")

    # 診療科別CSV
    for cat in ['小児科', '皮膚科', '耳鼻咽喉科', '眼科']:
        cat_file = os.path.join(BASE_DIR, f'csv/clinics_{cat}_geo.csv')
        cat_rows = [r for r in results if cat in r['診療科']]
        with open(cat_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in cat_rows:
                writer.writerow(r)
        print(f"  {cat}: {cat_file} ({len(cat_rows)}件)")

    # === 5. 緯度経度の最終チェック ===
    missing = [r['名称'] for r in results if not r['緯度'] or r['緯度'] in ('0', '0.0')]
    if missing:
        print(f"\n警告: 緯度経度が欠損している施設が{len(missing)}件あります:")
        for n in missing[:10]:
            print(f"  {n}")
    else:
        print("\n全施設の緯度経度が取得済みです。")

    # === 6. clinics.html更新 ===
    print("\n=== clinics.html更新 ===")
    update_html(results)


def update_html(results):
    """clinics.htmlのJSON DATA部分を更新"""
    # HTMLファイルを読み込み
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    # JSONデータ部分を置換
    # 既存の「const DATA = [...];\n」部分を新しいデータに差し替え
    json_data = json.dumps(results, ensure_ascii=False)
    new_data_line = f'const DATA = {json_data};'

    # 正規表現で既存のDATA定義を置換
    html_new = re.sub(
        r'const DATA = \[.*?\];',
        new_data_line,
        html,
        flags=re.DOTALL
    )

    # 出典の日付を更新
    html_new = html_new.replace(
        '厚生労働省 医療情報ネット オープンデータ（2025年12月1日時点）',
        'さいたま市オープンデータ（2026年1月31日時点）'
    )

    # <p>タグ内のデータソース説明も更新
    html_new = re.sub(
        r'(<p>)厚生労働省 医療情報ネット オープンデータ（2025年12月1日時点）(</p>)',
        r'\g<1>さいたま市オープンデータ（2026年1月31日時点）\g<2>',
        html_new
    )

    # カードのHTMLテンプレート部分に電話番号と診療時間を追加
    # 既存のmeta部分を拡張
    # 元: '<div class="meta">' + addr + rest + '</div>'
    # 新: '<div class="meta">' + addr + tel + time + rest + '</div>'
    old_meta = """let rest = d['休診日'] ? '<br>休診: ' + d['休診日'] : '';

    return '<div class="card ' + mainCat + '">' +
      '<h3>' + d['名称'] + '</h3>' +
      '<div class="tags">' + tags + '</div>' +
      '<div class="meta">' + addr + rest + '</div>' +
      '<div class="links">' + links + '</div>' +
      '</div>';"""

    new_meta = """let rest = d['休診日等'] ? '<br>休診: ' + d['休診日等'] : '';
    let tel = d['電話番号'] ? '<br>TEL: ' + d['電話番号'] : '';
    let hours = d['診療時間'] ? '<br>診療時間: ' + d['診療時間'] : '';

    return '<div class="card ' + mainCat + '">' +
      '<h3>' + d['名称'] + '</h3>' +
      '<div class="tags">' + tags + '</div>' +
      '<div class="meta">' + addr + tel + hours + rest + '</div>' +
      '<div class="links">' + links + '</div>' +
      '</div>';"""

    html_new = html_new.replace(old_meta, new_meta)

    # 休診日キー名の修正（JSON側が「休診日等」になったため、フィルタ部分も対応）
    # 旧データは「休診日」だが新データは「休診日等」

    # フッターの出典も更新
    html_new = html_new.replace(
        '※ 休診日情報は届出ベースのため、実際と異なる場合があります。受診前に各医療機関にご確認ください。',
        '※ 情報は届出ベースのため、実際と異なる場合があります。受診前に各医療機関にご確認ください。'
    )

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_new)

    print(f"  {HTML_FILE} を更新しました（{len(results)}件のデータを埋め込み）")


if __name__ == '__main__':
    main()
