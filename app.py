from flask import Flask, jsonify, render_template
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from math import gcd
import json # jsonモジュールはデータ構造の確認のために残す

app = Flask(__name__)

# --- 設定項目（BASE_URLは設定されていなかったため、プレースホルダーURLを使用）---
# 🌐 WebサービスのルートURLに合わせて静的ファイルのパスを設定
BASE_URL_PLACEHOLDER = "/static"

TARGET_SITES = [
    {
        'type': 'element',
        'display_name': 'ノンハプバーもぐら',
        'name': 'mogura',
        'url': 'https://member.nonhapumogura.com/',
        'selector': '#count-num',
        'image_url': BASE_URL_PLACEHOLDER + '/images/mogura.png'
    },
    {
        'type': 'paging_bbs',
        'display_name': '440',
        'name': '440',
        'base_url': 'https://rara.jp/bar440/',
        'page_url_prefix': 'https://rara.jp/bar440/link',
        'start_page': 1,
        'max_page': 10,
        'step': 1,
        'date_selector': 'i.fa-solid.fa-clock',
        'date_format': '%Y/%m/%d',
        'image_url': BASE_URL_PLACEHOLDER + '/images/440.png'
    },
    {
        'type': 'paging_bbs_gender',
        'display_name': 'カネロ',
        'name': 'canelo',
        'base_url': 'https://barcanelo.com/bbs/index.php?page=0',
        'page_url_prefix': 'https://barcanelo.com/bbs/index.php?page=',
        'start_page': 0,
        'max_page': 10,
        'step': 10,
        'date_selector': 'span.date',
        'gender_selector': 'span.sex',
        'date_format': '%Y/%m/%d',
        'image_url': BASE_URL_PLACEHOLDER + '/images/canelo.png'
    },
    {
        'type': 'paging_bbs_gender',
        'display_name': 'リトリートバー',
        'name': 'retreatbar',
        'base_url': 'https://retreatbar.jp/bbs/index.php?page=0',
        'page_url_prefix': 'https://retreatbar.jp/bbs/index.php?page=',
        'start_page': 0,
        'max_page': 10,
        'step': 10,
        'date_selector': 'span.date',
        'gender_selector': 'span.sex',
        'date_format': '%Y/%m/%d',
        'image_url': BASE_URL_PLACEHOLDER + '/images/retreatbar.png'
    },
    {
        'type': 'paging_bbs_gender',
        'display_name': 'バーフェイス',
        'name': 'bar-face',
        'base_url': 'https://bar-face.jp/bbs/index.php?page=0',
        'page_url_prefix': 'https://bar-face.jp/bbs/index.php?page=',
        'start_page': 0,
        'max_page': 10,
        'step': 10,
        'date_selector': 'span.date',
        'gender_selector': 'span.sex',
        'date_format': '%Y/%m/%d',
        'image_url': BASE_URL_PLACEHOLDER + '/images/bar-face.png'
    },
]
# -----------------

# 状態管理のための辞書（ファイルI/Oの代わりに使用）
# 最後のスクレイピング結果と実行時刻を保存
SCRAPED_DATA_CACHE = {
    'last_updated': None,
    'data': None
}

# --- スクレピング関数の定義 ---

def get_post_count_from_element(site):
    """ 単一の要素から直接書き込み数を取得する """
    print(f"Checking '{site['display_name']}'...")
    headers = {'User-Agent': 'MyScraper/1.0'}
    
    try:
        response = requests.get(site['url'], headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        count_element = soup.select_one(site['selector'])
        
        display_text = count_element.text.strip() if count_element else '取得失敗'
            
    except requests.exceptions.RequestException as e:
        print(f"  -> Error fetching {site['url']}: {e}")
        display_text = 'エラー'
    except Exception as e:
        print(f"  -> Unexpected error: {e}")
        display_text = '処理エラー'

    return {
        'display_name': site['display_name'],
        'count': display_text,
        'url': site['url'],
        'type': 'simple',
        'image_url': site['image_url']
    }

def get_today_post_count_from_paging_site(site):
    """ ページングされた掲示板を巡回し、今日の投稿数を集計する """
    today_str = datetime.now().strftime(site['date_format'])
    today_post_count = 0
    headers = {'User-Agent': 'MyPagingScraper/1.0'}

    print(f"Checking '{site['display_name']}' (Date: {today_str})...")

    try:
        for page_num in range(site['start_page'], site['max_page'] + 1, site['step']):
            target_url = site['base_url'] if page_num == site['start_page'] else f"{site['page_url_prefix']}{page_num}"
            print(f"  -> page {page_num} ({target_url})")

            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            post_times = soup.select(site['date_selector'])
            
            if not post_times:
                print("    -> No date info found. Stopping.")
                break

            is_today_post_found_on_page = False
            for time_element in post_times:
                post_datetime_str = ''
                if site['name'] == '440':
                    next_node = time_element.next_sibling
                    if next_node and next_node.string:
                        post_datetime_str = next_node.string.strip()
                else:
                    post_datetime_str = time_element.text.strip()
                
                if today_str in post_datetime_str:
                    today_post_count += 1
                    is_today_post_found_on_page = True
            
            if not is_today_post_found_on_page and page_num > site['start_page']:
                print("    -> No more posts for today. Stopping.")
                break
    except requests.exceptions.RequestException as e:
        print(f"    -> Error: {e}")
    except Exception as e:
        print(f"    -> Unexpected error: {e}")
    
    display_text = f"{today_post_count}件"
    return {
        'display_name': site['display_name'],
        'count': display_text,
        'url': site['base_url'],
        'type': 'simple',
        'image_url' : site['image_url']
    }

def get_today_post_count_with_gender(site):
    """ 性別ごとに今日の投稿数を集計する """
    today_str = datetime.now().strftime(site['date_format'])
    gender_count = {'男性': 0, '女性': 0, '不明': 0}
    headers = {'User-Agent': 'MyPagingScraper/1.0'}

    print(f"Checking '{site['display_name']}' with gender (Date: {today_str})...")

    try:
        for page_num in range(site['start_page'], site['max_page'] + 1, site['step']):
            target_url = site['base_url'] if page_num == site['start_page'] else f"{site['page_url_prefix']}{page_num}"
            print(f"  -> page {page_num} ({target_url})")

            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            posts = soup.select('dl.contributor')
            
            if not posts:
                print("    -> No posts found. Stopping.")
                break

            is_today_post_found_on_page = False
            
            for post in posts:
                date_element = post.select_one(site['date_selector'])
                if not date_element:
                    continue
                    
                post_date_str = date_element.text.strip()
                
                if today_str in post_date_str:
                    is_today_post_found_on_page = True
                    
                    gender_element = post.select_one(site['gender_selector'])
                    if gender_element:
                        gender_text = gender_element.text.strip()
                        
                        if '男' in gender_text or 'male' in gender_text.lower():
                            gender_count['男性'] += 1
                        elif '女' in gender_text or 'female' in gender_text.lower():
                            gender_count['女性'] += 1
                        else:
                            gender_count['不明'] += 1
                    else:
                        gender_count['不明'] += 1
                
                # 古い日付に達したら停止
                try:
                    if datetime.strptime(post_date_str, site['date_format']) < datetime.strptime(today_str, site['date_format']):
                         # 同じページ内に今日の日付の投稿が残っている可能性を考慮し、ページ全体でループを抜ける
                        break
                except ValueError:
                    # 日付パースエラーはスキップ
                    continue
            
            if not is_today_post_found_on_page and page_num > site['start_page']:
                print("    -> No more posts for today. Stopping.")
                break
    except requests.exceptions.RequestException as e:
        print(f"    -> Error: {e}")
    except Exception as e:
        print(f"    -> Unexpected error: {e}")

    total = sum(gender_count.values())
    
    # 男女比を計算（最小の自然数比）
    ratio = "計算不可"
    if gender_count['男性'] > 0 and gender_count['女性'] > 0:
        common_divisor = gcd(gender_count['男性'], gender_count['女性'])
        male_ratio = gender_count['男性'] // common_divisor
        female_ratio = gender_count['女性'] // common_divisor
        ratio = f"{male_ratio}:{female_ratio}"
    elif gender_count['男性'] > 0:
        ratio = "男性のみ"
    elif gender_count['女性'] > 0:
        ratio = "女性のみ"
    
    print(f"  -> Total: {total}, Male: {gender_count['男性']}, Female: {gender_count['女性']}, Unknown: {gender_count['不明']}, Ratio: {ratio}")
    
    return {
        'display_name': site['display_name'],
        'count': f"{total}件",
        'url': site['base_url'],
        'type': 'gender',
        'image_url' : site['image_url'],
        'gender_detail': {
            'male': gender_count['男性'],
            'female': gender_count['女性'],
            'unknown': gender_count['不明'],
            'ratio': ratio
        }
    }


def scrape_data(force_run=False):
    """ データをスクレイピングし、結果の辞書を返すメイン関数（キャッシュ機能付き） """
    
    global SCRAPED_DATA_CACHE
    cache = SCRAPED_DATA_CACHE
    
    # キャッシュの有効期限をチェック (1時間 = 3600秒)
    is_cache_stale = (cache['last_updated'] is None or 
                      (datetime.now() - cache['last_updated']).total_seconds() > 3600)
    
    if not force_run and not is_cache_stale:
        print("Returning data from cache.")
        return cache['data']

    print("Executing full scrape...")
    results = []

    for site in TARGET_SITES:
        try:
            if site['type'] == 'element':
                results.append(get_post_count_from_element(site))
            elif site['type'] == 'paging_bbs':
                results.append(get_today_post_count_from_paging_site(site))
            elif site['type'] == 'paging_bbs_gender':
                results.append(get_today_post_count_with_gender(site))
        except Exception as e:
            print(f"An unexpected error occurred for {site['display_name']}: {e}")
            results.append({
                'display_name': site['display_name'],
                'count': '処理エラー',
                'url': site.get('url') or site.get('base_url', 'N/A'),
                'type': site['type'],
                'image_url': site['image_url']
            })

    final_data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'post_data': results
    }
    
    # キャッシュを更新
    SCRAPED_DATA_CACHE['last_updated'] = datetime.now()
    SCRAPED_DATA_CACHE['data'] = final_data
    
    return final_data

# --- Flask ルート定義 ---

@app.route('/')
def index():
    """トップページ（index.html）を表示する"""
    # テンプレートファイルが必要です
    return render_template('index.html')

@app.route('/api/posts')
def get_posts():
    """キャッシュされた、または新規にスクレイピングしたデータを返すAPI"""
    try:
        # キャッシュが有効ならそれを使用、そうでなければスクレイピング実行 (force_run=False)
        data = scrape_data(force_run=False)
        return jsonify(data)
    except Exception as e:
        print(f"API Error in get_posts: {e}")
        return jsonify({'error': f'データの取得中にエラーが発生しました: {e}'}), 500

@app.route('/api/refresh')
def force_refresh():
    """強制的にスクレイピングを実行し、最新のデータを返すAPI"""
    try:
        # 強制的にスクレイピングを実行 (force_run=True)
        data = scrape_data(force_run=True)
        return jsonify(data)
    except Exception as e:
        print(f"API Error in force_refresh: {e}")
        return jsonify({'error': f'強制更新中にエラーが発生しました: {e}'}), 500

if __name__ == '__main__':
    # 開発環境で実行する場合の注意: 
    # Flaskのデフォルトのreloaderはプロセスを再起動するため、SCRAPED_DATA_CACHEもリセットされます。
    app.run(debug=True, host='0.0.0.0')
