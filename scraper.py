import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from math import gcd

# --- 設定項目 ---
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
# -----------------

def get_post_count_from_element(site):
    """ 単一の要素から直接書き込み数を取得する """
    print(f"Checking '{site['display_name']}'...")
    headers = {'User-Agent': 'MyScraper/1.0'}
    
    try:
        response = requests.get(site['url'], headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        count_element = soup.select_one(site['selector'])
        
        if count_element:
            display_text = count_element.text.strip()
        else:
            display_text = '取得失敗'
            
    except requests.exceptions.RequestException as e:
        print(f"  -> Error fetching {site['url']}: {e}")
        display_text = 'エラー'

    return {
        'display_name': site['display_name'],
        'count': display_text,
        'url': site['url'],
        'type': 'simple'
    }

def get_today_post_count_from_paging_site(site):
    """ ページングされた掲示板を巡回し、今日の投稿数を集計する """
    today_str = datetime.now().strftime(site['date_format'])
    today_post_count = 0
    headers = {'User-Agent': 'MyPagingScraper/1.0'}

    print(f"Checking '{site['display_name']}' (Date: {today_str})...")

    for page_num in range(site['start_page'], site['max_page'] + 1, site['step']):
        if page_num == site['start_page']:
            target_url = site['base_url']
        else:
            target_url = f"{site['page_url_prefix']}{page_num}"

        print(f"  -> page {page_num} ({target_url})")

        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            post_times = soup.select(site['date_selector'])
            
            if not post_times:
                print("    -> No date info found. Stopping.")
                break

            is_today_post_found_on_page = False
            for time_element in post_times:
                if site['name'] == '440':
                    post_datetime_str = time_element.next_element.text.strip()
                
                if today_str in post_datetime_str:
                    today_post_count += 1
                    is_today_post_found_on_page = True
            
            if not is_today_post_found_on_page and page_num > site['start_page']:
                print("    -> No more posts for today. Stopping.")
                break

        except requests.exceptions.RequestException as e:
            print(f"    -> Error: {e}")
            break
    
    display_text = f"{today_post_count}件"
    return {
        'display_name': site['display_name'],
        'count': display_text,
        'url': site['base_url'],
        'type': 'simple'
    }

def get_today_post_count_with_gender(site):
    """ 性別ごとに今日の投稿数を集計する """
    today_str = datetime.now().strftime(site['date_format'])
    gender_count = {'男性': 0, '女性': 0, '不明': 0}
    headers = {'User-Agent': 'MyPagingScraper/1.0'}

    print(f"Checking '{site['display_name']}' with gender (Date: {today_str})...")

    for page_num in range(site['start_page'], site['max_page'] + 1, site['step']):
        if page_num == site['start_page']:
            target_url = site['base_url']
        else:
            target_url = f"{site['page_url_prefix']}{page_num}"

        print(f"  -> page {page_num} ({target_url})")

        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 投稿を取得（各投稿は.messageクラスなど、サイト構造に応じて調整）
            posts = soup.select('dl.contributor')
            
            if not posts:
                print("    -> No posts found. Stopping.")
                break

            is_today_post_found_on_page = False
            
            for post in posts:
                # 日付を取得
                date_element = post.select_one(site['date_selector'])
                if not date_element:
                    continue
                    
                post_date_str = date_element.text.strip()
                
                # 今日の投稿かチェック
                if today_str in post_date_str:
                    is_today_post_found_on_page = True
                    
                    # 性別を取得
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
            
            if not is_today_post_found_on_page and page_num > site['start_page']:
                print("    -> No more posts for today. Stopping.")
                break

        except requests.exceptions.RequestException as e:
            print(f"    -> Error: {e}")
            break
    
    total = sum(gender_count.values())
    
    # 男女比を計算（最小の自然数比）
    if gender_count['男性'] > 0 and gender_count['女性'] > 0:
        male_count = gender_count['男性']
        female_count = gender_count['女性']
        
        # 最大公約数で割って最小の比率にする
        common_divisor = gcd(male_count, female_count)
        male_ratio = male_count // common_divisor
        female_ratio = female_count // common_divisor
        
        ratio = f"{male_ratio}:{female_ratio}"
    elif gender_count['男性'] > 0:
        ratio = "男性のみ"
    elif gender_count['女性'] > 0:
        ratio = "女性のみ"
    else:
        ratio = "計算不可"
    
    print(f"  -> Total: {total}, Male: {gender_count['男性']}, Female: {gender_count['女性']}, Unknown: {gender_count['不明']}, Ratio: {ratio}")
    
    return {
        'display_name': site['display_name'],
        'count': f"{total}件",
        'url': site['base_url'],
        'type': 'gender',
        'gender_detail': {
            'male': gender_count['男性'],
            'female': gender_count['女性'],
            'unknown': gender_count['不明'],
            'ratio': ratio
        }
    }

if __name__ == '__main__':
    results = []

    for site in TARGET_SITES:
        if site['type'] == 'element':
            results.append(get_post_count_from_element(site))
        elif site['type'] == 'paging_bbs':
            results.append(get_today_post_count_from_paging_site(site))
        elif site['type'] == 'paging_bbs_gender':
            results.append(get_today_post_count_with_gender(site))

    final_data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'post_data': results
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print("\n---")
    print("Scraping complete.")
    print("Results saved to data.json.")