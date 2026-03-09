#!/usr/bin/env python3
"""厚生労働省 医療情報ネットのオープンデータから
さいたま市の小児科・皮膚科・耳鼻科・眼科を抽出してCSV生成"""
import csv
import re
import unicodedata

FACILITY_FILE = 'clinic_data/02-1_clinic_facility_info_20251201.csv'
SPECIALITY_FILE = 'clinic_data/02-2_clinic_speciality_hours_20251201.csv'

# 対象診療科の判定関数
def classify_speciality(name):
    """診療科目名からカテゴリを判定。美容系は除外"""
    name_norm = unicodedata.normalize('NFKC', name)
    categories = []

    # 美容系・コンタクト・AGA等を除外
    if '美容' in name_norm or 'コンタクト' in name_norm:
        return []
    if 'AGA' in name_norm or 'aga' in name_norm:
        return []

    if '小児科' in name_norm or '小児' in name_norm:
        categories.append('小児科')
    if '皮膚科' in name_norm and '美容' not in name_norm:
        categories.append('皮膚科')
    if '耳鼻' in name_norm:
        categories.append('耳鼻咽喉科')
    if '眼科' in name_norm and '美容' not in name_norm:
        categories.append('眼科')

    return categories

# 1. 診療科目データから対象施設IDを収集
print("=== 診療科目データ読み込み ===")
clinic_specialities = {}  # ID -> set of categories
clinic_hours = {}  # ID -> {category: hours_info}

with open(SPECIALITY_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cats = classify_speciality(row['診療科目名'])
        if not cats:
            continue

        cid = row['ID']
        if cid not in clinic_specialities:
            clinic_specialities[cid] = set()
        clinic_specialities[cid].update(cats)

        # 診療時間を収集（最初の1つだけ）
        if cid not in clinic_hours:
            clinic_hours[cid] = {}
        for cat in cats:
            if cat not in clinic_hours[cid]:
                # 曜日ごとの診療時間を簡易的にまとめる
                days = []
                for d in ['月', '火', '水', '木', '金', '土', '日']:
                    start = row.get(f'{d}_診療開始時間', '')
                    end = row.get(f'{d}_診療終了時間', '')
                    if start and end:
                        days.append(f'{d}{start}-{end}')
                clinic_hours[cid][cat] = ' / '.join(days) if days else ''

print(f"  対象診療科を持つ施設ID数: {len(clinic_specialities)}")

# 2. 施設データからさいたま市の施設を抽出
print("\n=== 施設データ読み込み（さいたま市フィルタ） ===")
results = []

with open(FACILITY_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cid = row['ID']
        addr = row['所在地']

        # さいたま市フィルタ
        if 'さいたま市' not in addr:
            continue

        # 対象診療科を持っているか
        if cid not in clinic_specialities:
            continue

        cats = sorted(clinic_specialities[cid])
        lat = row.get('所在地座標（緯度）', '')
        lng = row.get('所在地座標（経度）', '')

        # 区を抽出（「西区」「北区」等の2〜3文字+区）
        m = re.search(r'さいたま市(.{1,3}区)', addr)
        ward = m.group(1) if m else ''

        # 休診日
        rest_days = []
        for d in ['月', '火', '水', '木', '金', '土', '日']:
            if row.get(f'毎週決まった曜日に休診（{d}）', '') == '1':
                rest_days.append(d)
        rest_str = '・'.join(rest_days) + '曜休診' if rest_days else ''

        # 住所に埼玉県を追加
        if addr.startswith('さいたま市'):
            addr = '埼玉県' + addr

        name = unicodedata.normalize('NFKC', row['正式名称'])

        # 施設名で美容系・AGA系を除外
        name_lower = name.lower()
        if any(kw in name_lower for kw in ['美容', 'aga', 'メンズ脱毛', '脱毛', '聖心']):
            continue

        results.append({
            '緯度': lat,
            '経度': lng,
            '名称': name,
            '住所': addr,
            '区': ward,
            '診療科': '・'.join(cats),
            '休診日': rest_str,
            'URL': row.get('案内用ホームページアドレス', ''),
        })

print(f"  さいたま市の対象施設数: {len(results)}")

# カテゴリ別カウント
from collections import Counter
cat_counts = Counter()
for r in results:
    for c in r['診療科'].split('・'):
        cat_counts[c] += 1
for cat, cnt in sorted(cat_counts.items()):
    print(f"    {cat}: {cnt}件")

# 区別カウント
ward_counts = Counter(r['区'] for r in results)
for ward, cnt in sorted(ward_counts.items()):
    print(f"    {ward}: {cnt}件")

# 2.5 座標0.0の施設を国土地理院APIでジオコーディング
import urllib.request
import urllib.parse
import json
import time

def geocode_gsi(address):
    try:
        url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(address)
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data:
            coords = data[0]['geometry']['coordinates']
            return str(coords[1]), str(coords[0])
    except:
        pass
    return None, None

zero_count = sum(1 for r in results if r['緯度'] in ('0.0', '', '0', 0))
if zero_count > 0:
    print(f"\n=== 座標0.0の{zero_count}件をジオコーディング ===")
    for r in results:
        if r['緯度'] in ('0.0', '', '0', 0):
            lat, lng = geocode_gsi(r['住所'])
            if lat:
                r['緯度'] = lat
                r['経度'] = lng
                print(f"  OK {r['名称']}")
            else:
                print(f"  FAIL {r['名称']}")
            time.sleep(0.5)

# 3. CSV出力
output_file = 'clinics_geo.csv'
fieldnames = ['緯度', '経度', '名称', '住所', '区', '診療科', '休診日', 'URL']

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r)

print(f"\n=== 出力完了: {output_file} ({len(results)}件) ===")

# 4. 診療科別CSVも生成
for cat in ['小児科', '皮膚科', '耳鼻咽喉科', '眼科']:
    cat_file = f'clinics_{cat}_geo.csv'
    cat_rows = [r for r in results if cat in r['診療科']]
    with open(cat_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in cat_rows:
            writer.writerow(r)
    print(f"  {cat}: {cat_file} ({len(cat_rows)}件)")

# 5. 緯度経度の欠損チェック
missing_coords = [r['名称'] for r in results if not r['緯度'] or r['緯度'] in ('0.0', '0')]
if missing_coords:
    print(f"\n警告: 緯度経度が欠損している施設が{len(missing_coords)}件あります:")
    for n in missing_coords[:10]:
        print(f"  {n}")
else:
    print("\n全施設の緯度経度が取得済みです。")
