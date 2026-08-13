import { apiCall, showToast } from '../api.js';
import { store } from '../store.js';

export default async function renderWaiter() {
    const container = document.createElement('div');
    container.style.cssText = 'display: flex; flex-direction: column; height: 100%; overflow: hidden;';
    
    let currentOrder = null;
    let menuData = null;
    let modalItemData = null;
    let allOrders = [];

    // Main layout
    container.innerHTML = `
        <header style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--c-border); background: var(--bg-secondary);">
            <div>
                <h1 style="margin: 0; font-size: 1.2rem;">Ofitsiant</h1>
                <p style="margin: 4px 0 0; color: var(--text-muted); font-size: 0.9rem;">${store.user?.username || 'User'}</p>
            </div>
            <button id="logout-btn-top" style="padding: 8px 16px; background: var(--c-danger-alpha); color: var(--c-danger); border: none; border-radius: 4px; cursor: pointer;">
                <i class="ri-logout-box-r-line"></i> Chiqish
            </button>
        </header>
        <div style="flex: 1; display: flex; gap: 24px; overflow: hidden; padding: 24px;">
        <div style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
            <div style="margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0;">Aktiv Buyurtmalar</h3>
                    <button class="btn btn-sm btn-primary" id="new-order-btn" style="padding: 6px 12px;">+ Yangi</button>
                </div>
            </div>
            <div id="orders-list" style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px;">
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <i class="ri-loader-4-line" style="font-size: 32px; animation: spin 1s linear infinite;"></i>
                    <p>Buyurtmalar yuklanmoqda...</p>
                </div>
            </div>

            <div style="margin-top: 16px; border-top: 1px solid var(--c-border); padding-top: 16px;">
                <h3 style="margin: 0 0 12px;">Bo'sh Stollar</h3>
                <div class="tables-grid" id="tables-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px;">
                    <div style="grid-column: 1/-1; text-align: center; padding: 20px; color: var(--text-muted); font-size: 0.9rem;">
                        Stollar yuklanmoqda...
                    </div>
                </div>
            </div>
        </div>
        
        <div style="flex: 1; display: flex; flex-direction: column; border-left: 1px solid var(--c-border); padding-left: 24px; overflow: hidden;">
            <div style="margin-bottom: 24px;">
                <h2 id="order-header">Buyurtma tanlang</h2>
            </div>
            <div id="order-content" style="flex: 1; overflow-y: auto;">
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <p>Buyurtma tanlang yoki yangi buyurtma oching</p>
                </div>
            </div>
        </div>

        <!-- Add Item Modal -->
        <div id="add-item-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; overflow-y: auto;">
            <div style="background: var(--bg-primary); border-radius: var(--border-radius-lg); padding: 24px; max-width: 400px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3); my-auto; margin: 40px auto;">
                <h3 id="modal-item-name" style="margin: 0 0 20px;">Item qo'shish</h3>
                <div class="input-group" style="margin-bottom: 16px;">
                    <label class="input-label">Miqdor:</label>
                    <input type="number" id="modal-qty" class="input-field" value="1" min="1" style="font-size: 1rem;">
                </div>

                <div id="modal-variants" style="margin-bottom: 16px;"></div>

                <div class="input-group" style="margin-bottom: 20px;">
                    <label class="input-label">Eslatma (ixtiyoriy):</label>
                    <textarea id="modal-note" class="input-field" placeholder="Izoh yozing..." style="resize: vertical; min-height: 60px;"></textarea>
                </div>

                <div style="display: flex; gap: 12px;">
                    <button class="btn" style="background: transparent; border: 1px solid var(--c-border); flex: 1;" id="modal-cancel-btn">Bekor</button>
                    <button class="btn btn-primary" id="modal-add-btn" style="flex: 1;">Qo'shish</button>
                </div>
            </div>
        </div>
        </div>
    `;

    // Load tables
    async function loadTables() {
        try {
            const tables = await apiCall('/waiter/tables/free', 'GET');
            const grid = container.querySelector('#tables-grid');
            
            if (!tables || tables.length === 0) {
                grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 20px; color: var(--text-muted); font-size: 0.9rem;">Bo'sh stol yo'q</div>`;
                return;
            }
            
            grid.innerHTML = tables.map(t => `
                <div class="table-card free" data-table-id="${t.id}" data-table-no="${t.table_no}" style="cursor: pointer;">
                    <div class="table-no">${t.table_no}</div>
                    <div class="table-cap"><i class="ri-group-line"></i> ${t.capacity}</div>
                </div>
            `).join('');
            
            grid.querySelectorAll('.table-card').forEach(card => {
                card.addEventListener('click', () => openOrderForTable(
                    parseInt(card.dataset.tableId),
                    card.dataset.tableNo
                ));
            });
        } catch (err) {
            console.error('Tables load error:', err);
            showToast('Stollar yuklanishida xatolik: ' + err.message, 'error');
        }
    }

    // Load active orders
    async function loadOrders() {
        try {
            const orders = await apiCall('/waiter/orders/my-active', 'GET');
            allOrders = orders || [];
            renderOrdersList();
        } catch (err) {
            console.error('Orders load error:', err);
            showToast('Buyurtmalar yuklanishida xatolik: ' + err.message, 'error');
        }
    }

    // Render orders list
    function renderOrdersList() {
        const ordersList = container.querySelector('#orders-list');
        
        if (!allOrders || allOrders.length === 0) {
            ordersList.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-muted); font-size: 0.9rem;">Aktiv buyurtma yo'q</div>`;
            return;
        }

        ordersList.innerHTML = `
            <div style="margin-bottom: 16px;">
                <input type="text" id="orders-search" class="input-field" placeholder="Order ID, stol raqami yoki item..." style="width: 100%;">
            </div>
            <div id="orders-list-items">
                ${allOrders.map(o => `
                    <div class="order-card" data-order-id="${o.id}" style="padding: 12px; background: var(--bg-secondary); border-radius: var(--border-radius-md); cursor: pointer; border-left: 4px solid ${o.status === 'open' ? 'var(--c-warning)' : 'var(--c-primary)'}; transition: all 0.2s;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: 600; color: var(--c-primary);">Stol ${o.table_no}</span>
                            <span style="font-size: 0.75rem; color: var(--text-muted);">#${o.id}</span>
                        </div>
                        <div style="font-size: 0.9rem; color: var(--text-muted);">
                            ${o.items.length} item • ${o.total_amount} so'm
                        </div>
                        <div style="font-size: 0.8rem; color: ${o.status === 'open' ? 'var(--c-warning)' : 'var(--c-success)'}; margin-top: 4px;">
                            ${o.status === 'open' ? '✏️ Tahrirlash' : '✓ Yuborilgan'}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Search functionality
        const searchInput = ordersList.querySelector('#orders-search');
        if (searchInput) {
            searchInput.addEventListener('input', async (e) => {
                const query = e.target.value.trim();
                if (query.length === 0) {
                    // Show all orders
                    const listItems = ordersList.querySelector('#orders-list-items');
                    listItems.querySelectorAll('.order-card').forEach(card => {
                        card.style.display = '';
                    });
                } else {
                    // Search via API
                    try {
                        const results = await apiCall(`/waiter/orders/search?q=${encodeURIComponent(query)}`, 'GET');
                        const listItems = ordersList.querySelector('#orders-list-items');
                        
                        // Hide all cards first
                        listItems.querySelectorAll('.order-card').forEach(card => {
                            card.style.display = 'none';
                        });
                        
                        // Show only matching results
                        results.forEach(result => {
                            const card = listItems.querySelector(`[data-order-id="${result.id}"]`);
                            if (card) card.style.display = '';
                        });
                    } catch (err) {
                        console.error('Search error:', err);
                    }
                }
            });
        }

        ordersList.querySelectorAll('.order-card').forEach(card => {
            card.addEventListener('click', async () => {
                const orderId = parseInt(card.dataset.orderId);
                const order = allOrders.find(o => o.id === orderId);
                if (order) {
                    currentOrder = order;
                    menuData = menuData || await apiCall('/waiter/menu', 'GET');
                    renderOrderForm(order.table_no);
                }
            });
        });
    }

    // Open order
    async function openOrderForTable(tableId, tableNo) {
        try {
            const newOrder = await apiCall('/waiter/orders/open', 'POST', { table_id: tableId });
            currentOrder = newOrder;
            
            if (!menuData) {
                menuData = await apiCall('/waiter/menu', 'GET');
            }
            
            renderOrderForm(tableNo);
        } catch (err) {
            showToast('Xatolik: ' + err.message, 'error');
        }
    }

    // Render order form
    function renderOrderForm(tableNo) {
        const content = container.querySelector('#order-content');
        const header = container.querySelector('#order-header');
        
        if (!currentOrder) {
            content.innerHTML = '<div style="color: var(--c-danger);">Order ma\'lumotlari xatosi</div>';
            return;
        }

        const isOpenOrder = currentOrder.status === 'open';
        header.textContent = `Stol ${tableNo} - Buyurtma #${currentOrder.id} ${!isOpenOrder ? '(Yuborilgan)' : ''}`;
        
        if (!menuData || menuData.length === 0) {
            content.innerHTML = '<div style="color: var(--c-warning);">Menyular yuklanmoqda...</div>';
            return;
        }

        const hasNewItems = currentOrder.items && currentOrder.items.some(i => i.status === 'new');
        
        let html = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: 100%;">
                <!-- Menu -->
                <div style="overflow-y: auto;">
                    <h3 style="margin-top: 0;">Menyular</h3>
                    <div style="margin-bottom: 16px;">
                        <input type="text" id="menu-search" class="input-field" placeholder="Qidiruv..." style="width: 100%;">
                    </div>
                    <div id="menu-container">
        `;
        
        // Menu with search
        html += menuData.map(cat => `
            <div style="margin-bottom: 20px;">
                <h4 style="margin: 8px 0; color: var(--c-primary);">${cat.name}</h4>
                <div style="display: grid; grid-template-columns: 1fr; gap: 8px;">
                    ${(cat.items || []).map(item => `
                        <div class="menu-item-card" 
                             style="padding: 12px; background: var(--bg-secondary); border-radius: 4px; cursor: pointer; transition: all 0.2s; border: 2px solid transparent;" 
                             data-item-id="${item.id}" 
                             data-item-name="${item.name.replace(/"/g, '&quot;')}" 
                             data-item-price="${item.base_price}" 
                             data-item-variants='${JSON.stringify(item.variants || [])}'>
                            <div style="font-weight: 500; font-size: 0.9rem;">${item.name}</div>
                            <div style="font-size: 0.8rem; color: var(--text-muted);">${item.base_price} so'm</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
        html += `
                    </div>
                </div>

                <!-- Order Items -->
                <div style="display: flex; flex-direction: column; border-left: 1px solid var(--c-border); padding-left: 16px;">
                    <h3 style="margin-top: 0;">Buyurtma Items</h3>
                    <div id="items-list" style="flex: 1; overflow-y: auto; margin-bottom: 16px;"></div>
                    <div id="total-amount" style="border-top: 1px solid var(--c-border); padding-top: 12px; font-weight: 500; font-size: 1.1rem; margin-bottom: 16px;">Jami: 0 so'm</div>
                    <div id="order-action-btns" style="display: flex; gap: 12px;">
                        ${isOpenOrder || hasNewItems ? `
                            ${isOpenOrder ? `<button class="btn" style="background: transparent; border: 1px solid var(--c-border); flex: 1;" id="cancel-order-btn">Bekor</button>` : ''}
                            <button class="btn btn-primary" id="submit-btn" style="flex: 1;">Yuborish</button>
                        ` : `
                            <button class="btn" style="background: transparent; border: 1px solid var(--c-border); flex: 1;" id="close-order-btn">Yopish</button>
                        `}
                    </div>
                </div>
            </div>
        `;
        
        content.innerHTML = html;

        // Menu search
        const searchInput = content.querySelector('#menu-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                const cards = content.querySelectorAll('.menu-item-card');
                cards.forEach(card => {
                    const name = card.dataset.itemName.toLowerCase();
                    card.style.display = name.includes(query) ? '' : 'none';
                });
            });
        }

        // Menu item click handlers (for both open and submitted orders)
        content.querySelectorAll('.menu-item-card').forEach(card => {
            card.addEventListener('click', () => showAddItemModal(card));
        });

        // Cancel order (only for open orders)
        const cancelBtn = content.querySelector('#cancel-order-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', async () => {
                if (confirm('Buyurtmani bekor qilish rostmi?')) {
                    await loadOrders();
                    container.querySelector('#order-header').textContent = 'Buyurtma tanlang';
                    container.querySelector('#order-content').innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);"><p>Buyurtma tanlang yoki yangi buyurtma oching</p></div>';
                }
            });
        }

        // Submit order (only for open orders)
        const submitBtn = content.querySelector('#submit-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', submitOrder);
        }

        // Close order (for submitted orders - just goes back)
        const closeBtn = content.querySelector('#close-order-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', async () => {
                currentOrder = null;
                container.querySelector('#order-header').textContent = 'Buyurtma tanlang';
                container.querySelector('#order-content').innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);"><p>Buyurtma tanlang yoki yangi buyurtma oching</p></div>';
            });
        }

        loadOrderItems();
    }

    // Show add item modal
    function showAddItemModal(card) {
        const itemId = parseInt(card.dataset.itemId);
        const itemName = card.dataset.itemName;
        const basePrice = parseInt(card.dataset.itemPrice);
        
        try {
            const variants = JSON.parse(card.dataset.itemVariants || '[]');

            const modal = container.querySelector('#add-item-modal');
            const qtyInput = container.querySelector('#modal-qty');
            const noteInput = container.querySelector('#modal-note');

            if (!modal || !qtyInput || !noteInput) {
                showToast('Modal elementlari topilmadi!', 'error');
                return;
            }

            // Store item data for adding
            modalItemData = { itemId, basePrice };

            // Update modal content
            container.querySelector('#modal-item-name').textContent = itemName;
            qtyInput.value = '1';
            noteInput.value = '';

            // Show variants
            const variantsDiv = container.querySelector('#modal-variants');
            if (variants && variants.length > 0) {
                variantsDiv.innerHTML = `
                    <div class="input-group">
                        <label class="input-label">Variant:</label>
                        <select id="modal-variant-select" class="input-field">
                            <option value="">Variant tanlanmagan</option>
                            ${variants.map(v => `<option value="${v.id}">${v.name} (+${v.price_delta} so'm)</option>`).join('')}
                        </select>
                    </div>
                `;
            } else {
                variantsDiv.innerHTML = '';
            }

            modal.style.display = 'flex';
        } catch (err) {
            console.error('❌ showAddItemModal error:', err);
            showToast('Modal ochishida xatolik: ' + err.message, 'error');
        }
    }

    // Load order items
    async function loadOrderItems() {
        try {
            const order = await apiCall(`/waiter/orders/${currentOrder.id}`, 'GET');
            currentOrder = order;
            
            const itemsList = container.querySelector('#items-list');
            const isOpenOrder = currentOrder.status === 'open';
            
            if (!order.items || order.items.length === 0) {
                itemsList.innerHTML = '<div style="color: var(--text-muted);">Hozircha item yo\'q</div>';
                container.querySelector('#total-amount').textContent = `Jami: 0 so'm`;
                return;
            }
            
            const statusLabels = {
                new: { text: 'Yangi', color: 'var(--text-muted)' },
                sent: { text: 'Oshxonada', color: 'var(--c-warning)' },
                preparing: { text: 'Pishmoqda', color: 'var(--c-warning)' },
                ready: { text: 'Tayyor - berish kerak', color: 'var(--c-success)' },
                served: { text: 'Berildi', color: 'var(--c-success)' },
            };

            itemsList.innerHTML = order.items.map(item => `
                <div style="background: var(--bg-secondary); padding: 12px; margin-bottom: 8px; border-radius: var(--border-radius-sm);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <div style="font-weight: 500; font-size: 0.9rem;">${item.menu_item_name}${item.variant_name ? ` (${item.variant_name})` : ''}</div>
                        ${!isOpenOrder && statusLabels[item.status] ? `<span style="font-size: 0.75rem; color: ${statusLabels[item.status].color};">${statusLabels[item.status].text}</span>` : ''}
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px;">${item.qty}x ${item.unit_price} so'm = ${item.subtotal} so'm</div>
                    <div style="display: flex; gap: 4px;">
                        ${isOpenOrder || item.status === 'new' ? `
                            <button class="btn qty-minus" style="padding: 4px 8px; font-size: 0.8rem; flex: 0.3; cursor: pointer;" data-item-id="${item.id}">−</button>
                            <span style="flex: 0.4; text-align: center; padding: 4px; background: var(--bg-primary); border-radius: 4px; font-size: 0.8rem; font-weight: 500;">${item.qty}</span>
                            <button class="btn qty-plus" style="padding: 4px 8px; font-size: 0.8rem; flex: 0.3; cursor: pointer;" data-item-id="${item.id}">+</button>
                            <button class="btn delete-item" style="padding: 4px 8px; font-size: 0.8rem; background: var(--c-danger-alpha); color: var(--c-danger); flex: 1; margin-left: 4px; cursor: pointer; border: 1px solid var(--c-danger);" data-item-id="${item.id}">O'chirish</button>
                        ` : item.status === 'ready' ? `
                            <button class="btn serve-item" style="padding: 6px 8px; font-size: 0.8rem; background: var(--c-success-alpha); color: var(--c-success); flex: 1; cursor: pointer; border: 1px solid var(--c-success);" data-item-id="${item.id}"><i class="ri-check-line"></i> Mijozga berildi</button>
                        ` : ''}
                    </div>
                </div>
            `).join('');

            // Add event listeners for qty buttons
            itemsList.querySelectorAll('.qty-minus').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const itemId = parseInt(btn.dataset.itemId);
                    // Re-fetch current state instead of relying on stale reference
                    const latestOrder = await apiCall(`/waiter/orders/${currentOrder.id}`, 'GET');
                    const currentItem = latestOrder.items.find(i => i.id === itemId);
                    const newQty = currentItem.qty - 1;

                    if (newQty < 1) {
                        if ((isOpenOrder || currentItem.status === 'new') && confirm('Item o\'chirib tashlaymanmi?')) {
                            await deleteItem(itemId);
                        }
                        return;
                    }

                    try {
                        console.log('🔵 Updating item:', { itemId, orderId: currentOrder.id, newQty });
                        await apiCall(`/waiter/orders/${currentOrder.id}/items/${itemId}`, 'PATCH', { qty: newQty });
                        console.log('✅ Item updated, reloading...');
                        await loadOrderItems();
                    } catch (err) {
                        console.error('❌ Update error:', err);
                        showToast('Xatolik: ' + err.message, 'error');
                    }
                });
            });

            itemsList.querySelectorAll('.qty-plus').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const itemId = parseInt(btn.dataset.itemId);
                    // Re-fetch current state instead of relying on stale reference
                    const latestOrder = await apiCall(`/waiter/orders/${currentOrder.id}`, 'GET');
                    const currentItem = latestOrder.items.find(i => i.id === itemId);
                    const newQty = currentItem.qty + 1;

                    try {
                        console.log('🔵 Updating item:', { itemId, orderId: currentOrder.id, newQty });
                        await apiCall(`/waiter/orders/${currentOrder.id}/items/${itemId}`, 'PATCH', { qty: newQty });
                        console.log('✅ Item updated, reloading...');
                        await loadOrderItems();
                    } catch (err) {
                        console.error('❌ Update error:', err);
                        showToast('Xatolik: ' + err.message, 'error');
                    }
                });
            });

            itemsList.querySelectorAll('.delete-item').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const itemId = parseInt(btn.dataset.itemId);
                    if (confirm('Item o\'chirib tashlaymanmi?')) {
                        await deleteItem(itemId);
                    }
                });
            });

            itemsList.querySelectorAll('.serve-item').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const itemId = parseInt(btn.dataset.itemId);
                    try {
                        await apiCall(`/waiter/orders/${currentOrder.id}/items/${itemId}/serve`, 'POST');
                        showToast('Taom mijozga berildi deb belgilandi', 'success');
                        await loadOrderItems();
                    } catch (err) {
                        showToast('Xatolik: ' + err.message, 'error');
                    }
                });
            });

            container.querySelector('#total-amount').textContent = `Jami: ${order.total_amount} so'm`;
            
            // Dynamic buttons
            const hasNewItemsDyn = order.items && order.items.some(i => i.status === 'new');
            const actionBtns = container.querySelector('#order-action-btns');
            if (actionBtns) {
                actionBtns.innerHTML = (isOpenOrder || hasNewItemsDyn) ? `
                    ${isOpenOrder ? `<button class="btn" style="background: transparent; border: 1px solid var(--c-border); flex: 1;" id="cancel-order-btn">Bekor</button>` : ''}
                    <button class="btn btn-primary" id="submit-btn" style="flex: 1;">Yuborish</button>
                ` : `
                    <button class="btn" style="background: transparent; border: 1px solid var(--c-border); flex: 1;" id="close-order-btn">Yopish</button>
                `;
                
                // Rebind
                const sb = actionBtns.querySelector('#submit-btn');
                if (sb) sb.addEventListener('click', submitOrder);
                
                const cb = actionBtns.querySelector('#close-order-btn');
                if (cb) cb.addEventListener('click', async () => {
                    currentOrder = null;
                    container.querySelector('#order-header').textContent = 'Buyurtma tanlang';
                    container.querySelector('#order-content').innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);"><p>Buyurtma tanlang yoki yangi buyurtma oching</p></div>';
                });
                
                const cancelB = actionBtns.querySelector('#cancel-order-btn');
                if (cancelB) cancelB.addEventListener('click', async () => {
                    if (confirm('Buyurtmani bekor qilish rostmi?')) {
                        await loadOrders();
                        container.querySelector('#order-header').textContent = 'Buyurtma tanlang';
                        container.querySelector('#order-content').innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);"><p>Buyurtma tanlang yoki yangi buyurtma oching</p></div>';
                    }
                });
            }
        } catch (err) {
            console.error('❌ Order load error:', err);
            showToast('Order yuklanishida xatolik: ' + err.message, 'error');
        }
    }

    // Delete item
    async function deleteItem(itemId) {
        try {
            await apiCall(`/waiter/orders/${currentOrder.id}/items/${itemId}`, 'DELETE');
            showToast('Item o\'chirildi', 'success');
            await loadOrderItems();
        } catch (err) {
            showToast('Xatolik: ' + err.message, 'error');
        }
    }

    // Submit order
    async function submitOrder() {
        if (!currentOrder.items || currentOrder.items.length === 0) {
            showToast('Hech bo\'lmaganda bitta item qo\'shing!', 'error');
            return;
        }
        
        try {
            await apiCall(`/waiter/orders/${currentOrder.id}/submit`, 'POST', {});
            showToast('Buyurtma yuborildi!', 'success');
            currentOrder = null;
            
            container.querySelector('#order-header').textContent = 'Buyurtma tanlang';
            container.querySelector('#order-content').innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);"><p>Stol tanlang yoki buyurtma oching</p></div>';
            
            await loadOrders();
            await loadTables();
        } catch (err) {
            showToast('Xatolik: ' + err.message, 'error');
        }
    }

    // Initialize
    async function init() {
        try {
            // Load menu data first
            menuData = await apiCall('/waiter/menu', 'GET');
            
            // Load orders and tables
            await Promise.all([
                loadOrders(),
                loadTables()
            ]);

            // New order button handler
            const newOrderBtn = container.querySelector('#new-order-btn');
            if (newOrderBtn) {
                newOrderBtn.addEventListener('click', async () => {
                    try {
                        const tables = await apiCall('/waiter/tables/free', 'GET');
                        if (!tables || tables.length === 0) {
                            showToast('Bo\'sh stol yo\'q!', 'error');
                            return;
                        }
                        
                        const selectedTable = tables[0]; // Select first free table
                        await openOrderForTable(selectedTable.id, selectedTable.table_no);
                    } catch (err) {
                        showToast('Xatolik: ' + err.message, 'error');
                    }
                });
            }
        } catch (err) {
            console.error('Init error:', err);
            showToast('Yangilashda xatolik: ' + err.message, 'error');
        }
    }

    // Modal elements
    const modal = container.querySelector('#add-item-modal');
    const cancelBtn = container.querySelector('#modal-cancel-btn');
    const addBtn = container.querySelector('#modal-add-btn');

    // Modal button handlers
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    if (addBtn) {
        addBtn.addEventListener('click', async () => {
            if (!modalItemData) return;

            const qty = parseInt(container.querySelector('#modal-qty').value) || 1;
            const variantSelect = container.querySelector('#modal-variant-select');
            const variantId = variantSelect && variantSelect.value ? parseInt(variantSelect.value) : null;
            const note = container.querySelector('#modal-note').value.trim() || null;

            if (qty < 1) {
                showToast('Miqdor 1 dan katta bo\'lishi kerak!', 'error');
                return;
            }

            try {
                console.log('🔵 Adding item to order:', { 
                    orderId: currentOrder.id, 
                    itemId: modalItemData.itemId, 
                    qty, 
                    variantId, 
                    note 
                });
                await apiCall(`/waiter/orders/${currentOrder.id}/items`, 'POST', {
                    menu_item_id: modalItemData.itemId,
                    qty: qty,
                    variant_id: variantId,
                    note: note
                });
                showToast('✅ Item qo\'shildi!', 'success');
                modal.style.display = 'none';
                await loadOrderItems();
            } catch (err) {
                console.error('❌ Add item error:', err);
                showToast('❌ Xatolik: ' + err.message, 'error');
            }
        });
    }

    // Close modal on background click
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    // Logout handler
    const logoutBtn = container.querySelector('#logout-btn-top');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            store.logout();
            window.dispatchEvent(new CustomEvent('navTo', { detail: '/login' }));
        });
    }

    init();

    return container;
}
