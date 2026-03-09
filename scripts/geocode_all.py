#!/usr/bin/env python3
"""国土地理院APIで全CSVの住所をジオコーディングし、緯度・経度付きCSVを生成"""
import csv
import json
import time
import re
import urllib.request
import urllib.parse

def geocode_gsi(address):
    """国土地理院APIでジオコーディング"""
    try:
        url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(address)
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data:
            coords = data[0]['geometry']['coordinates']
            return coords[1], coords[0]  # lat, lng
    except Exception as e:
        pass

    # 建物名を除去して再試行
    simplified = re.sub(r'\s+.*$', '', address)
    if simplified != address:
        try:
            time.sleep(0.3)
            url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(simplified)
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read())
            if data:
                coords = data[0]['geometry']['coordinates']
                return coords[1], coords[0]
        except:
            pass

    # 番地レベルまで切り詰め
    m = re.search(r'(.*?\d+-\d+(-\d+)?)', address)
    if m:
        short = m.group(1)
        if short != address and short != simplified:
            try:
                time.sleep(0.3)
                url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(short)
                resp = urllib.request.urlopen(url, timeout=10)
                data = json.loads(resp.read())
                if data:
                    coords = data[0]['geometry']['coordinates']
                    return coords[1], coords[0]
            except:
                pass

    return None, None

def process_csv(input_file, output_file, addr_col):
    """CSVを読み込み、緯度・経度を追加"""
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if addr_col not in fieldnames:
        print(f"  警告: '{addr_col}'列が見つかりません。列: {fieldnames}")
        return

    out_fields = ['緯度', '経度'] + fieldnames
    success = 0
    fail = 0
    fail_list = []

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()

        for i, row in enumerate(rows):
            addr = row[addr_col]
            lat, lng = geocode_gsi(addr)

            if lat:
                success += 1
                status = "OK"
            else:
                fail += 1
                status = "FAIL"
                fail_list.append(row.get('名称', addr[:30]))

            row['緯度'] = lat if lat else ''
            row['経度'] = lng if lng else ''
            writer.writerow(row)

            name = row.get('名称', addr[:20])
            print(f"  [{i+1}/{len(rows)}] {status} {name}")

            # レート制限（控えめに0.5秒間隔）
            time.sleep(0.5)

    print(f"\n  結果: {success}件成功, {fail}件失敗 → {output_file}")
    if fail_list:
        print(f"  失敗リスト: {', '.join(fail_list[:10])}{'...' if len(fail_list)>10 else ''}")
    return success, fail

# --- メイン ---
files = [
    ('dayservice_gmap.csv', 'dayservice_geo.csv', '住所'),
    ('facilities_gmap.csv', 'facilities_geo.csv', '住所'),
    ('juku_gmap.csv', 'juku_geo.csv', '住所'),
]

for inp, out, col in files:
    print(f"\n=== {inp} ===")
    process_csv(inp, out, col)

print("\n全ファイル完了。*_geo.csv をGoogle My Mapsにインポートしてください。")
print("インポート時に「緯度」「経度」列を位置情報として選択してください。")
