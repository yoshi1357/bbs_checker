"""
共通設定ファイル
店舗情報や基本設定を一元管理
"""
from dotenv import load_dotenv
from datetime import timezone, timedelta

load_dotenv()

# 日本時間（JST）のタイムゾーン定義
JST = timezone(timedelta(hours=9))

# 静的ファイルのベースURL
BASE_URL_PLACEHOLDER = "/static"

# 対象サイトの設定
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
        'date_selector': 'div.user-meta',
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
    {
        'type': 'element',
        'display_name': 'カラーズバー',
        'name': 'colors',
        'url': 'https://t-colors.net/',
        'selector': 'span.sum',
        'image_url': BASE_URL_PLACEHOLDER + '/images/colors.png'
    },
]

# データベース設定
DB_PATH = 'posts_data.db'

# キャッシュ有効期限（秒）
CACHE_EXPIRATION = 3600  # 1時間

# バッチ実行時刻
BATCH_HOUR = 19  # 19時
BATCH_MINUTE = 0