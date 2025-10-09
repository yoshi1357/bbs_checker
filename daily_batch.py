"""
毎日19時に実行されるバッチ処理
各店舗の書き込み数を取得してDBに保存
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from math import gcd
import db_manager

# 日本時間（JST）のタイムゾーン定義
JST = timezone(timedelta(hours=9))

TARGET_SITES = [
    {
        'type': 'element',
        'display_name': 'ノンハプバーもぐら',
        'name': 'mogura',
        'url': 'https://member.nonhapumogura.com/',
        'selector': '#count-num'
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
        'date_format': '%Y/%m/%d'
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
        'date_format': '%Y/%m/%d'
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
        'date_format': '%Y/%m/%d'
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
        'date_format': '%Y/%m/%d'
    },
]

def get_jst_now():
    """現在の日本時間を取得"""
    return datetime.now(JST)

def get_post_count_from_element(site):
    """単一の要素から直接書き込み数を取得"""
    print(f"Checking '{site['display_name']}'...")
    headers = {'User-Agent': 'MyScraper/1.0'}
    
    try:
        response = requests.get(site['url'], headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        count_element = soup.select_one(site['selector'])
        
        if count_element:
            count_text = count_element.text.strip()
            # 数字のみ抽出
            count = int(''.join(filter(str.isdigit, count_text)))
        else:
            count = 0
            
    except Exception as e:
        print(f"  -> Error: {e}")
        count = 0

    return {
        'site_name': site['display_name'],
        'total_count': count,
        'male_count': 0,
        'female_count': 0,
        'unknown_count': 0
    }

def get_today_post_count_from_paging_site(site, target_date_str):
    """ページングされた掲示板を巡回し、指定日の投稿数を集計"""
    today_post_count = 0
    headers = {'User-Agent': 'MyPagingScraper/1.0'}

    print(f"Checking '{site['display_name']}' (Date: {target_date_str})...")

    try:
        for page_num in range(site['start_page'], site['max_page'] + 1, site['step']):
            target_url = site['base_url'] if page_num == site['start_page'] else f"{site['page_url_prefix']}{page_num}"
            print(f"  -> page {page_num}")

            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            post_times = soup.select(site['date_selector'])
            
            if not post_times:
                break

            is_target_post_found = False
            for time_element in post_times:
                post_datetime_str = ''
                if site['name'] == '440':
                    next_node = time_element.next_sibling
                    if next_node and next_node.string:
                        post_datetime_str = next_node.string.strip()
                else:
                    post_datetime_str = time_element.text.strip()
                
                if target_date_str in post_datetime_str:
                    today_post_count += 1
                    is_target_post_found = True
            
            if not is_target_post_found and page_num > site['start_page']:
                break
    except Exception as e:
        print(f"    -> Error: {e}")
    
    return {
        'site_name': site['display_name'],
        'total_count': today_post_count,
        'male_count': 0,
        'female_count': 0,
        'unknown_count': 0
    }

def get_today_post_count_with_gender(site, target_date_str):
    """性別ごとに指定日の投稿数を集計"""
    gender_count = {'男性': 0, '女性': 0, '不明': 0}
    headers = {'User-Agent': 'MyPagingScraper/1.0'}

    print(f"Checking '{site['display_name']}' with gender (Date: {target_date_str})...")

    try:
        for page_num in range(site['start_page'], site['max_page'] + 1, site['step']):
            target_url = site['base_url'] if page_num == site['start_page'] else f"{site['page_url_prefix']}{page_num}"
            print(f"  -> page {page_num}")

            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            posts = soup.select('dl.contributor')
            
            if not posts:
                break

            is_target_post_found = False
            
            for post in posts:
                date_element = post.select_one(site['date_selector'])
                if not date_element:
                    continue
                    
                post_date_str = date_element.text.strip()
                
                if target_date_str in post_date_str:
                    is_target_post_found = True
                    
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
            
            if not is_target_post_found and page_num > site['start_page']:
                break
    except Exception as e:
        print(f"    -> Error: {e}")

    total = sum(gender_count.values())
    
    return {
        'site_name': site['display_name'],
        'total_count': total,
        'male_count': gender_count['男性'],
        'female_count': gender_count['女性'],
        'unknown_count': gender_count['不明']
    }

def run_daily_batch():
    """毎日のバッチ処理を実行"""
    print(f"\n{'='*50}")
    print(f"Daily Batch Started at {get_jst_now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    # データベース初期化
    db_manager.init_db()
    
    # 今日の日付（JST）
    today = get_jst_now().strftime('%Y-%m-%d')
    today_formatted = get_jst_now().strftime('%Y/%m/%d')
    
    results = []
    
    for site in TARGET_SITES:
        try:
            if site['type'] == 'element':
                data = get_post_count_from_element(site)
            elif site['type'] == 'paging_bbs':
                data = get_today_post_count_from_paging_site(site, today_formatted)
            elif site['type'] == 'paging_bbs_gender':
                data = get_today_post_count_with_gender(site, today_formatted)
            
            # DBに保存
            db_manager.save_daily_data(
                site_name=data['site_name'],
                record_date=today,
                total_count=data['total_count'],
                male_count=data['male_count'],
                female_count=data['female_count'],
                unknown_count=data['unknown_count']
            )
            
            results.append(data)
            print(f"✓ {data['site_name']}: {data['total_count']}件")
            
        except Exception as e:
            print(f"✗ Error processing {site['display_name']}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Daily Batch Completed")
    print(f"{'='*50}\n")
    
    return results

if __name__ == '__main__':
    run_daily_batch()