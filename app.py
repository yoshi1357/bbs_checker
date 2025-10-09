from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import db_manager
from daily_batch import run_daily_batch
from config import TARGET_SITES, JST, BATCH_HOUR, BATCH_MINUTE, CACHE_EXPIRATION
from scraper_utils import (
    get_jst_now,
    get_post_count_from_element,
    get_today_post_count_from_paging_site,
    get_today_post_count_with_gender
)

app = Flask(__name__)

# データベース初期化
db_manager.init_db()

# スケジューラー設定
scheduler = BackgroundScheduler(timezone='Asia/Tokyo')

def scheduled_batch_job():
    """スケジューラーから呼ばれるジョブ"""
    print("Scheduled batch job triggered")
    run_daily_batch()

# 毎日指定時刻に実行
scheduler.add_job(
    func=scheduled_batch_job,
    trigger='cron',
    hour=BATCH_HOUR,
    minute=BATCH_MINUTE,
    id='daily_batch_job',
    name='Daily post count batch',
    replace_existing=True
)

scheduler.start()

# アプリケーション終了時にスケジューラーを停止
atexit.register(lambda: scheduler.shutdown())

# 状態管理のための辞書
SCRAPED_DATA_CACHE = {
    'last_updated': None,
    'data': None
}

def scrape_data(force_run=False):
    """ データをスクレイピングし、結果の辞書を返すメイン関数（キャッシュ機能付き） """
    
    global SCRAPED_DATA_CACHE
    cache = SCRAPED_DATA_CACHE
    
    # キャッシュの有効期限をチェック
    now_jst = get_jst_now()
    is_cache_stale = (cache['last_updated'] is None or 
                      (now_jst - cache['last_updated']).total_seconds() > CACHE_EXPIRATION)
    
    if not force_run and not is_cache_stale:
        print("Returning data from cache.")
        return cache['data']

    print("Executing full scrape...")
    results = []

    for site in TARGET_SITES:
        try:
            if site['type'] == 'element':
                result = get_post_count_from_element(site)
            elif site['type'] == 'paging_bbs':
                result = get_today_post_count_from_paging_site(site)
            elif site['type'] == 'paging_bbs_gender':
                result = get_today_post_count_with_gender(site)
            
            results.append(result)
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
        'last_updated': now_jst.strftime('%Y-%m-%d %H:%M:%S'),
        'post_data': results
    }
    
    # キャッシュを更新
    SCRAPED_DATA_CACHE['last_updated'] = now_jst
    SCRAPED_DATA_CACHE['data'] = final_data
    
    return final_data

def calculate_comparison(current_count, past_count):
    """前回との比較を計算"""
    if past_count is None or past_count == 0:
        return {
            'diff': None,
            'diff_text': '---',
            'rate': None,
            'rate_text': '---'
        }
    
    diff = current_count - past_count
    rate = ((current_count - past_count) / past_count) * 100
    
    diff_text = f"+{diff}" if diff > 0 else str(diff)
    rate_text = f"+{rate:.1f}%" if rate > 0 else f"{rate:.1f}%"
    
    return {
        'diff': diff,
        'diff_text': diff_text,
        'rate': rate,
        'rate_text': rate_text
    }

# --- Flask ルート定義 ---

@app.route('/')
def index():
    """トップページ（index.html）を表示する"""
    return render_template('index.html')

@app.route('/api/posts')
def get_posts():
    """キャッシュされた、または新規にスクレイピングしたデータを返すAPI"""
    try:
        data = scrape_data(force_run=False)
        return jsonify(data)
    except Exception as e:
        print(f"API Error in get_posts: {e}")
        return jsonify({'error': f'データの取得中にエラーが発生しました: {e}'}), 500

@app.route('/api/refresh')
def force_refresh():
    """強制的にスクレイピングを実行し、最新のデータを返すAPI"""
    try:
        data = scrape_data(force_run=True)
        return jsonify(data)
    except Exception as e:
        print(f"API Error in force_refresh: {e}")
        return jsonify({'error': f'強制更新中にエラーが発生しました: {e}'}), 500

@app.route('/api/comparison')
def get_comparison():
    """前日・前週同曜日との比較データを返すAPI"""
    try:
        today = get_jst_now().strftime('%Y-%m-%d')
        comparisons = db_manager.get_all_sites_comparison(today)
        
        # 現在のデータも含めて返す
        result = {}
        for site_name, comp_data in comparisons.items():
            # 今日のデータを取得
            today_data = db_manager.get_data_by_date(site_name, today)
            
            if today_data:
                # 前日との比較
                yesterday_comp = calculate_comparison(
                    today_data['total_count'],
                    comp_data['yesterday']['total_count'] if comp_data['yesterday'] else None
                )
                
                # 前週同曜日との比較
                last_week_comp = calculate_comparison(
                    today_data['total_count'],
                    comp_data['last_week']['total_count'] if comp_data['last_week'] else None
                )
                
                result[site_name] = {
                    'today': today_data,
                    'yesterday': comp_data['yesterday'],
                    'last_week': comp_data['last_week'],
                    'yesterday_comparison': yesterday_comp,
                    'last_week_comparison': last_week_comp
                }
        
        return jsonify(result)
    except Exception as e:
        print(f"API Error in get_comparison: {e}")
        return jsonify({'error': f'比較データの取得中にエラーが発生しました: {e}'}), 500

@app.route('/api/history/<site_name>')
def get_history(site_name):
    """特定サイトの履歴データを返すAPI"""
    try:
        days = request.args.get('days', 7, type=int)
        history = db_manager.get_recent_history(site_name, days)
        return jsonify(history)
    except Exception as e:
        print(f"API Error in get_history: {e}")
        return jsonify({'error': f'履歴データの取得中にエラーが発生しました: {e}'}), 500

@app.route('/api/batch/run')
def manual_batch_run():
    """手動でバッチを実行するAPI（テスト用）"""
    try:
        results = run_daily_batch()
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        print(f"Batch Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print(f"Scheduler started. Next batch run at {BATCH_HOUR}:00 JST")
    print(f"Jobs: {scheduler.get_jobs()}")
    app.run(debug=True, host='0.0.0.0')