"""
スクレイピング処理の共通関数
app.pyとdaily_batch.pyの両方で使用
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from math import gcd
from config import JST

def get_jst_now():
    """現在の日本時間を取得"""
    return datetime.now(JST)

def get_jst_today_str(date_format='%Y/%m/%d'):
    """今日の日付を日本時間で取得"""
    return get_jst_now().strftime(date_format)

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
            try:
                count = int(''.join(filter(str.isdigit, count_text)))
            except ValueError:
                count = 0
                display_text = count_text
        else:
            count = 0
            display_text = '取得失敗'
            
    except requests.exceptions.RequestException as e:
        print(f"  -> Error fetching {site['url']}: {e}")
        count = 0
        display_text = 'エラー'
    except Exception as e:
        print(f"  -> Unexpected error: {e}")
        count = 0
        display_text = '処理エラー'

    return {
        'display_name': site['display_name'],
        'count': display_text if 'display_text' in locals() else f"{count}件",
        'url': site['url'],
        'type': 'simple',
        'image_url': site['image_url'],
        'total_count': count,
        'male_count': 0,
        'female_count': 0,
        'unknown_count': 0
    }

def get_today_post_count_from_paging_site(site):
    """ ページングされた掲示板を巡回し、今日の投稿数を集計する """
    today_str = get_jst_today_str(site['date_format'])
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
            
            posts = soup.select('table.layer_pop')
            
            if not posts:
                print("    -> No date info found. Stopping.")
                break

            is_today_post_found_on_page = False
            for post in posts:
                if site['name'] == '440':
                    post_user_name = post.select_one('div.user-name').text.strip()
                    post_datetime_str = post.select_one(site['date_selector']).text.strip()
                    if '440' in post_user_name:
                        # お店の書き込みは除く
                        continue

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
    
    return {
        'display_name': site['display_name'],
        'count': f"{today_post_count}件",
        'url': site['base_url'],
        'type': 'simple',
        'image_url': site['image_url'],
        'total_count': today_post_count,
        'male_count': 0,
        'female_count': 0,
        'unknown_count': 0
    }

def get_today_post_count_with_gender(site, target_date_str=None):
    """性別ごとに指定日の投稿数を集計"""
    if target_date_str is None:
        target_date_str = get_jst_today_str(site['date_format'])
    
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
                print("    -> No posts found. Stopping.")
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
                
                # 古い日付に達したら停止
                try:
                    if datetime.strptime(post_date_str, site['date_format']) < datetime.strptime(target_date_str, site['date_format']):
                        break
                except ValueError:
                    continue
            
            if not is_target_post_found and page_num > site['start_page']:
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
        'image_url': site['image_url'],
        'total_count': total,
        'male_count': gender_count['男性'],
        'female_count': gender_count['女性'],
        'unknown_count': gender_count['不明'],
        'gender_detail': {
            'male': gender_count['男性'],
            'female': gender_count['女性'],
            'unknown': gender_count['不明'],
            'ratio': ratio
        }
    }