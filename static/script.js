// APIからデータを取得して画面に表示するJavaScript
async function fetchData(forceRefresh = false) {
    const postList = document.getElementById('post-list');
    const updatedTime = document.getElementById('updated-time');
    const reloadButton = document.getElementById('reload');
    
    // ローディング表示
    postList.innerHTML = '<li class="loading">データを読み込んでいます...</li>';
    updatedTime.textContent = '';
    reloadButton.disabled = true;
    reloadButton.textContent = '読み込み中...';
    
    try {
        // forceRefreshがtrueの場合は/api/refresh、falseの場合は/api/posts
        const endpoint = forceRefresh ? '/api/refresh' : '/api/posts';
        const response = await fetch(endpoint);
        
        if (!response.ok) {
            throw new Error('データの取得に失敗しました。');
        }
        
        const result = await response.json();
        console.log('API Response:', result);
        
        // /api/refreshの場合はresult.dataにデータが入っている
        const data = forceRefresh && result.data ? result.data : result;
        
        // データ構造の確認
        if (!data || !data.post_data) {
            throw new Error('データ形式が正しくありません。');
        }
        
        // リストをクリア
        postList.innerHTML = '';

        // 取得したデータでリスト項目を作成
        data.post_data.forEach(site => {
            const li = document.createElement('li');
            
            // 店名にリンクを追加
            const siteName = site.url 
                ? `<a href="${site.url}" target="_blank" rel="noopener noreferrer">${site.display_name}</a>`
                : site.display_name;
            
            // 性別情報がある場合は詳細表示
            if (site.type === 'gender' && site.gender_detail) {
                const detail = site.gender_detail;
                li.innerHTML = `
                    <div class="site-info">
                        <span class="site-name">${siteName}</span>
                        <div class="gender-detail">
                            <span class="gender-item male">👨 ${detail.male}件</span>
                            <span class="gender-item female">👩 ${detail.female}件</span>
                            <span class="gender-item unknown">❓ ${detail.unknown}件</span>
                            <span class="gender-ratio">予想男女比 = ${detail.ratio}</span>
                        </div>
                    </div>
                    <span class="post-count">${site.count}</span>
                `;
            } else {
                // 通常表示
                li.innerHTML = `
                    <span class="site-name">${siteName}</span>
                    <span class="post-count">${site.count}</span>
                `;
            }
            
            postList.appendChild(li);
        });

        // 更新日時を表示
        updatedTime.textContent = `最終更新: ${data.last_updated}`;

    } catch (error) {
        postList.innerHTML = `<li class="error">エラー: ${error.message}</li>`;
        console.error('Fetch error:', error);
    } finally {
        // ボタンを再度有効化
        reloadButton.disabled = false;
        reloadButton.textContent = '更新';
    }
}

// ページが読み込まれたらデータを取得
window.addEventListener('DOMContentLoaded', () => {
    fetchData(false);
});

// 更新ボタンクリック時の処理
const reloadButton = document.getElementById('reload');
reloadButton.addEventListener('click', () => {
    fetchData(true);
});