from flask import Flask, jsonify, render_template
import json
import subprocess
import os
from datetime import datetime

app = Flask(__name__)

def run_scraper():
    """scraper.pyを実行してdata.jsonを更新する"""
    try:
        print("Running scraper.py...")
        result = subprocess.run(
            ['python', 'scraper.py'],
            capture_output=True,
            text=True,
            timeout=120  # 2分でタイムアウト
        )
        
        if result.returncode == 0:
            print("Scraper completed successfully")
            return True
        else:
            print(f"Scraper failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Scraper timed out")
        return False
    except Exception as e:
        print(f"Error running scraper: {e}")
        return False

@app.route('/')
def index():
    """トップページ（index.html）を表示する"""
    return render_template('index.html')

@app.route('/api/posts')
def get_posts():
    """data.json の内容を返すAPI（アクセス時にスクレイピング実行）"""
    
    # data.jsonが存在しない、または古い場合はスクレイピング実行
    should_scrape = False
    
    if not os.path.exists('data.json'):
        should_scrape = True
        print("data.json not found. Running scraper...")
    else:
        # data.jsonの更新時刻をチェック（1時間以内なら再取得しない）
        file_mtime = os.path.getmtime('data.json')
        file_age_seconds = datetime.now().timestamp() - file_mtime
        
        if file_age_seconds > 3600:  # 1時間 = 3600秒
            should_scrape = True
            print(f"data.json is {file_age_seconds/60:.1f} minutes old. Running scraper...")
    
    # 必要な場合はスクレイピング実行
    if should_scrape:
        run_scraper()
    
    # data.jsonを読み込んで返す
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Data file not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data'}), 500

@app.route('/api/refresh')
def force_refresh():
    """強制的にスクレイピングを実行するAPI"""
    run_scraper()
    
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Data file not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')