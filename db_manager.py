import sqlite3
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

DB_PATH = 'posts_data.db'
JST = timezone(timedelta(hours=9))

@contextmanager
def get_db_connection():
    """データベース接続のコンテキストマネージャー"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """データベースを初期化"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_name VARCHAR(100) NOT NULL,
                record_date DATE NOT NULL,
                total_count INTEGER NOT NULL,
                male_count INTEGER DEFAULT 0,
                female_count INTEGER DEFAULT 0,
                unknown_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(site_name, record_date)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_site_date 
            ON daily_posts(site_name, record_date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_record_date 
            ON daily_posts(record_date)
        ''')
        print("Database initialized successfully")

def save_daily_data(site_name, record_date, total_count, male_count=0, female_count=0, unknown_count=0):
    """日次データを保存（既存データは上書き）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO daily_posts 
            (site_name, record_date, total_count, male_count, female_count, unknown_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(site_name, record_date) 
            DO UPDATE SET 
                total_count = excluded.total_count,
                male_count = excluded.male_count,
                female_count = excluded.female_count,
                unknown_count = excluded.unknown_count,
                created_at = CURRENT_TIMESTAMP
        ''', (site_name, record_date, total_count, male_count, female_count, unknown_count))
        print(f"Saved data for {site_name} on {record_date}")

def get_data_by_date(site_name, target_date):
    """特定の日付のデータを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM daily_posts 
            WHERE site_name = ? AND record_date = ?
        ''', (site_name, target_date))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_comparison_data(site_name, current_date):
    """前日と前週同曜日のデータを取得"""
    current = datetime.strptime(current_date, '%Y-%m-%d')
    yesterday = (current - timedelta(days=1)).strftime('%Y-%m-%d')
    last_week = (current - timedelta(days=7)).strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 前日のデータ
        cursor.execute('''
            SELECT * FROM daily_posts 
            WHERE site_name = ? AND record_date = ?
        ''', (site_name, yesterday))
        yesterday_data = cursor.fetchone()
        
        # 前週同曜日のデータ
        cursor.execute('''
            SELECT * FROM daily_posts 
            WHERE site_name = ? AND record_date = ?
        ''', (site_name, last_week))
        last_week_data = cursor.fetchone()
        
        return {
            'yesterday': dict(yesterday_data) if yesterday_data else None,
            'last_week': dict(last_week_data) if last_week_data else None
        }

def get_all_sites_comparison(current_date):
    """全サイトの比較データを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT site_name FROM daily_posts')
        sites = [row['site_name'] for row in cursor.fetchall()]
        
    result = {}
    for site in sites:
        result[site] = get_comparison_data(site, current_date)
    
    return result

def get_recent_history(site_name, days=7):
    """直近N日分のデータを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM daily_posts 
            WHERE site_name = ? 
            ORDER BY record_date DESC 
            LIMIT ?
        ''', (site_name, days))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

if __name__ == '__main__':
    # テスト実行
    init_db()
    print("Database setup complete!")