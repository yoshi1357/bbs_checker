// APIからデータを取得して画面に表示するJavaScript
async function fetchData(forceRefresh = false) {
    const postList = document.getElementById('post-list');
    const updatedTime = document.getElementById('updated-time');
    const reloadButton = document.getElementById('reload');
    
    // ローディング表示
    postList.innerHTML = '<div class="card loading-card"><div class="card-content"><p>データを読み込んでいます...</p></div></div>';
    updatedTime.textContent = '';
    reloadButton.disabled = true;
    reloadButton.textContent = '読み込み中...';
    
    try {
        const endpoint = forceRefresh ? '/api/refresh' : '/api/posts';
        const response = await fetch(endpoint);
        
        if (!response.ok) {
            throw new Error('データの取得に失敗しました。');
        }
        
        const result = await response.json();
        console.log('API Response:', result);
        
        const data = forceRefresh && result.data ? result.data : result;
        
        if (!data || !data.post_data) {
            throw new Error('データ形式が正しくありません。');
        }

        updatedTime.textContent = `最終更新: ${data.last_updated}`;
        
        // カードグリッドをクリア
        postList.innerHTML = '';
        postList.className = 'card-grid'

        // 各サイトのカードを作成
        data.post_data.forEach(site => {
            const card = document.createElement('div');
            card.className = 'card';
            card.style.backgroundImage = `url('${site.image_url}')`;

            const cardContent = document.createElement('div');
            cardContent.className = 'card-content';
            
            // 店名
            const titleElement = document.createElement('div');
            titleElement.className = 'card-title';
            if (site.url) {
                titleElement.innerHTML = `<a href="${site.url}" target="_blank" rel="noopener noreferrer">${site.display_name}</a>`;
            } else {
                titleElement.textContent = site.display_name;
            }
            
            // 件数
            const countElement = document.createElement('div');
            countElement.className = 'card-count';
            countElement.textContent = site.count;
            
            cardContent.appendChild(titleElement);
            cardContent.appendChild(countElement);
            
            // 性別詳細がある場合
            if (site.type === 'gender' && site.gender_detail) {
                const detail = site.gender_detail;
                
                const genderDiv = document.createElement('div');
                genderDiv.className = 'gender-detail';
                
                genderDiv.innerHTML = `
                    <span class="gender-item">👨 ${detail.male}件</span>
                    <span class="gender-item">👩 ${detail.female}件</span>
                    <span class="gender-item">❓ ${detail.unknown}件</span>
                `;
                
                const ratioElement = document.createElement('div');
                ratioElement.className = 'gender-ratio';
                ratioElement.textContent = `男女比率 ${detail.ratio}`;
                
                cardContent.appendChild(genderDiv);
                cardContent.appendChild(ratioElement);
            }
            
            card.appendChild(cardContent);
            postList.appendChild(card);
        });
    } catch (error) {
        postList.innerHTML = `<div class="card error-card"><div class="card-content"><p>エラー: ${error.message}</p></div></div>`;
        console.error('Fetch error:', error);
    } finally {
        reloadButton.disabled = false;
        reloadButton.textContent = '更新';
    }
}

window.addEventListener('DOMContentLoaded', () => {
    fetchData(false);
});

const reloadButton = document.getElementById('reload');
reloadButton.addEventListener('click', () => {
    fetchData(true);
});