import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# --- 設定項目 ---
# 集計したいサイトの情報を一つのリストで管理
TARGET_SITES = [
    {
        'type': 'element', # 処理のタイプを指定
        'display_name': 'ノンハプバーもぐら',
        'name': 'mogura',
        'url': 'https://member.nonhapumogura.com/',
        'selector': '#count-num'
    },
    {
        'type': 'paging_bbs', # 処理のタイプを指定
        'display_name': '440',
        'name': '440',
        'base_url': 'https://rara.jp/bar440/',
        'page_url_prefix': 'https://rara.jp/bar440/link',
        'start_page': 1,
        'max_page': 10,
        'step': 1,
        'date_selector': 'div.user-text',
        'date_format': '%Y/%m/%d'
    },
    {
        'type': 'paging_bbs', 
        'display_name': 'カネロ',
        'name': 'canelo',
        'base_url': 'https://barcanelo.com/bbs/index.php?page=0',
        'page_url_prefix': 'https://barcanelo.com/bbs/index.php?page=',
        'start_page': 0,
        'max_page': 10,
        'step': 10,
        'date_selector': 'dl.contributor', 
        'date_format': '%Y/%m/%d'
    },
    {
        'type': 'paging_bbs', 
        'display_name': 'リトリートバー',
        'name': 'retreatbar',
        'base_url': 'https://retreatbar.jp/bbs/index.php?page=0',
        'page_url_prefix': 'https://retreatbar.jp/bbs/index.php?page=',
        'start_page': 0,
        'max_page': 10,
        'step': 10,
        'date_selector': 'dl.contributor', 
        'date_format': '%Y/%m/%d' 
    },
    {
        'type': 'paging_bbs', 
        'display_name': 'バーフェイス',
        'name': 'bar-face',
        'base_url': 'https://bar-face.jp/bbs/index.php?page=0',
        'page_url_prefix': 'https://bar-face.jp/bbs/index.php?page=',
        'start_page': 0,
        'max_page': 10,
        'step': 10,
        'date_selector': 'dl.contributor', 
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
        display_text = f"  -> Error fetching {site['url']}: {e}"

    return {'display_name': site['display_name'], 'count': display_text}

def get_today_post_count_from_paging_site(site):
    """ ページングされた掲示板を巡回し、今日の投稿数を集計する """
    # サイトの設定から日付フォーマットを取得
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
            
            is_today_post_found_on_page = False
            # 個別の整形処理
            posts = soup.select(site['date_selector'])
            for post in posts:
                if site['name'] == '440':
                    poster_name = post.select_one('.user-name').text.strip()
                    # お店の返信は含めない
                    if (poster_name != '440'):
                        post_datetime_str = post.select_one('.user-meta').text.strip()
                    else:
                        post_datetime_str = ''
                elif site['name'] == 'canelo' or site['name'] == 'retreatbar' or site['name'] == 'bar-face':
                    poster_sex = post.select_one('span.sex').text.strip()
                    # 女性または性別不明の投稿のみ
                    if '男性' not in poster_sex:
                        post_datetime_str = post.select_one('span.date').text.strip()
                    else:
                        post_datetime_str = ''
                # 今日の日付が含まれているか
                if today_str in post_datetime_str:
                    today_post_count += 1
                    is_today_post_found_on_page = True
            
            if not is_today_post_found_on_page and page_num > 1:
                print("    -> No more posts for today. Stopping.")
                break

        except requests.exceptions.RequestException as e:
            print(f"    -> Error: {e}")
            break
    
    display_text = f"{today_post_count}件"
    return {'display_name': site['display_name'], 'count': display_text}

if __name__ == '__main__':
    results = []

    # 共通のリストをループ処理
    for site in TARGET_SITES:
        if site['type'] == 'element':
            results.append(get_post_count_from_element(site))
        elif site['type'] == 'paging_bbs':
            results.append(get_today_post_count_from_paging_site(site))

    final_data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'post_data': results
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print("\n---")
    print("Scraping complete.")
    print("Results saved to data.json.")