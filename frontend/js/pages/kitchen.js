import { apiCall } from '../api.js';
import { store } from '../store.js';

export default async function renderKitchen() {
    const container = document.createElement('div');
    container.style.cssText = 'display: flex; flex-direction: column; height: 100%; overflow: hidden;';
    
    let items = [];
    let autoRefreshInterval = null;

    async function loadQueue() {
        try {
            items = await apiCall('/kitchen/order-items/queue', 'GET');
            renderQueue();
        } catch (error) {
            console.error('Error loading kitchen queue:', error);
        }
    }

    function renderQueue() {
        const newItems = items.filter(i => i.status === 'sent') || [];
        const preparingItems = items.filter(i => i.status === 'preparing') || [];
        const readyItems = items.filter(i => i.status === 'ready') || [];
        
        container.innerHTML = `
            <header style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--c-border); background: var(--bg-secondary);">
                <div>
                    <h1 style="margin: 0; font-size: 1.2rem;">Oshxona</h1>
                    <p style="margin: 4px 0 0; color: var(--text-muted); font-size: 0.9rem;">${store.user?.username || 'User'}</p>
                </div>
                <button id="logout-btn-top" style="padding: 8px 16px; background: var(--c-danger-alpha); color: var(--c-danger); border: none; border-radius: 4px; cursor: pointer;">
                    <i class="ri-logout-box-r-line"></i> Chiqish
                </button>
            </header>
            <div style="flex: 1; overflow-y: auto; padding: 24px;">
                <div style="margin-bottom: 24px;">
                    <h2 style="margin-top: 0;">Tayyorlanishi Kerak Bo'lgan Ovqatlar</h2>
                    <p style="color:var(--text-muted);">Faqat tayyorlanishi kerak bo'lgan ovqatlarning ro'yxati</p>
                </div>
            
            <div class="kanban-board">
                <!-- Yangi buyurtmalar -->
                <div class="kanban-col">
                    <div class="kanban-header">
                        <span>🔥 Yangi</span>
                        <span class="kanban-badge">${newItems.length}</span>
                    </div>
                    <div class="kanban-items" id="new-items">
                        ${newItems.length === 0 
                            ? `<div style="text-align:center;color:var(--text-muted);padding:24px;">Hech narsa yo'q</div>`
                            : newItems.map(o => `
                                <div class="order-card" data-item-id="${o.id}">
                                    <ul class="order-item-list" style="list-style:none;padding:0;margin:0;">
                                        <li style="font-weight: 600; font-size: 1.1rem; margin-bottom: 8px;">${o.menu_item_name}${o.variant_name ? ' (' + o.variant_name + ')' : ''}</li>
                                        <li style="font-size: 1.3rem; font-weight: 700; color: var(--c-primary); margin-bottom: 8px;">${o.qty}x</li>
                                        ${o.note ? `<li style="color:var(--c-warning);font-size:0.9rem;padding:8px;background:rgba(245,158,11,0.1);border-radius:4px;">📝 ${o.note}</li>` : ''}
                                    </ul>
                                    <div style="display:flex; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--c-border);">
                                        <span style="font-size:0.8rem;color:var(--text-muted);flex:1;display:flex;align-items:center;"><i class="ri-time-line"></i> Yangi</span>
                                        <button class="btn btn-prepare" data-item-id="${o.id}" style="background:var(--c-primary-alpha);color:var(--c-primary);padding:6px 12px;border:none;border-radius:4px;cursor:pointer;font-weight:500;">
                                            Tayyorlash
                                        </button>
                                    </div>
                                </div>
                            `).join('')
                        }
                    </div>
                </div>

                <!-- Tayyorlanyapti -->
                <div class="kanban-col">
                    <div class="kanban-header">
                        <span>⏳ Pishmoqda</span>
                        <span class="kanban-badge" style="background: rgba(245, 158, 11, 0.15); color: var(--c-warning);">${preparingItems.length}</span>
                    </div>
                    <div class="kanban-items" id="preparing-items">
                        ${preparingItems.length === 0 
                            ? `<div style="text-align:center;color:var(--text-muted);padding:24px;">Hech narsa yo'q</div>`
                            : preparingItems.map(o => `
                                <div class="order-card" data-item-id="${o.id}">
                                    <ul class="order-item-list" style="list-style:none;padding:0;margin:0;">
                                        <li style="font-weight: 600; font-size: 1.1rem; margin-bottom: 8px;">${o.menu_item_name}${o.variant_name ? ' (' + o.variant_name + ')' : ''}</li>
                                        <li style="font-size: 1.3rem; font-weight: 700; color: var(--c-primary); margin-bottom: 8px;">${o.qty}x</li>
                                    </ul>
                                    <div style="display:flex; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--c-border);">
                                        <span style="font-size:0.8rem;color:var(--c-warning);flex:1;display:flex;align-items:center;"><i class="ri-loader-4-line" style="animation: spin 1s linear infinite;"></i> Pishmoqda</span>
                                        <button class="btn btn-ready" data-item-id="${o.id}" style="background:var(--c-success-alpha);color:var(--c-success);padding:6px 12px;border:none;border-radius:4px;cursor:pointer;font-weight:500;">
                                            Tayyor
                                        </button>
                                    </div>
                                </div>
                            `).join('')
                        }
                    </div>
                </div>

                <!-- Tayyor -->
                <div class="kanban-col">
                    <div class="kanban-header">
                        <span>✅ Tayyor</span>
                        <span class="kanban-badge" style="background: var(--c-success-alpha); color: var(--c-success);">${readyItems.length}</span>
                    </div>
                    <div class="kanban-items" id="ready-items">
                        ${readyItems.length === 0 
                            ? `<div style="text-align:center;color:var(--text-muted);padding:24px;">Hech narsa yo'q</div>`
                            : readyItems.map(o => `
                                <div class="order-card" style="background: var(--c-success-alpha); border: 2px solid var(--c-success);">
                                    <ul class="order-item-list" style="list-style:none;padding:0;margin:0;">
                                        <li style="font-weight: 600; font-size: 1.1rem; margin-bottom: 8px;">${o.menu_item_name}${o.variant_name ? ' (' + o.variant_name + ')' : ''}</li>
                                        <li style="font-size: 1.3rem; font-weight: 700; color: var(--c-success); margin-bottom: 8px;">${o.qty}x</li>
                                    </ul>
                                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--c-success);">
                                        <span style="font-size:0.8rem;color:var(--c-success);"><i class="ri-check-double-line"></i> Servaga tayyor</span>
                                    </div>
                                </div>
                            `).join('')
                        }
                    </div>
                </div>
            </div>
            </div>
        `;

        // Add event listeners to buttons
        container.querySelectorAll('.btn-prepare').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const itemId = parseInt(btn.dataset.itemId);
                try {
                    console.log('📢 Preparing item:', itemId);
                    await apiCall(`/kitchen/order-items/${itemId}/start`, 'POST');
                    console.log('✅ Item prepared, reloading queue...');
                    await loadQueue();
                } catch (error) {
                    console.error('❌ Preparation error:', error);
                    alert('Xatolik: ' + error.message);
                }
            });
        });

        container.querySelectorAll('.btn-ready').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const itemId = parseInt(btn.dataset.itemId);
                try {
                    console.log('✅ Marking ready:', itemId);
                    await apiCall(`/kitchen/order-items/${itemId}/ready`, 'POST');
                    console.log('🔄 Item marked ready, reloading queue...');
                    await loadQueue();
                } catch (error) {
                    console.error('❌ Ready error:', error);
                    alert('Xatolik: ' + error.message);
                }
            });
        });
    }

    // Load initial queue
    await loadQueue();

    // Auto-refresh every 5 seconds
    autoRefreshInterval = setInterval(() => {
        loadQueue();
    }, 5000);

    // Show loading state
    const loadingDiv = document.createElement('div');
    loadingDiv.style.cssText = 'position: fixed; bottom: 20px; right: 20px; font-size: 0.8rem; color: var(--text-muted);';
    loadingDiv.textContent = '↻ Har 5 sekundda yangilanadi';
    container.appendChild(loadingDiv);

    // Logout handler (Event Delegation to survive innerHTML re-renders)
    container.addEventListener('click', (e) => {
        if (e.target.closest('#logout-btn-top')) {
            // Clean up auto-refresh interval
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
            }
            store.logout();
            window.dispatchEvent(new CustomEvent('navTo', { detail: '/login' }));
        }
    });

    return container;
}
