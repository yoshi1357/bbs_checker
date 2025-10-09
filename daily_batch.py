"""
毎日19時に実行されるバッチ処理
各店舗の書き込み数を取得してDBに保存
"""
import db_manager
from config import TARGET_SITES
from scraper_utils import (
    get_jst_now,
    get_post_count_from_element,
    get_today_post_count_from_paging_site,
    get_today_post_count_with_gender
)


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