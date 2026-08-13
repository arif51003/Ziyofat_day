import { apiCall, showToast } from '../api.js';
import { store } from '../store.js';

export default async function renderCashier() {
    const container = document.createElement('div');
    container.style.cssText = 'display: flex; flex-direction: column; height: 100%; overflow: hidden;';
    
    let orders = [];
    let currentTab = 'unpaid';

    container.innerHTML = `
        <header style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--c-border); background: var(--bg-secondary);">
            <div>
                <h1 style="margin: 0; font-size: 1.2rem;">Kassir</h1>
                <p style="margin: 4px 0 0; color: var(--text-muted); font-size: 0.9rem;">${store.user?.username || 'User'}</p>
            </div>
            <button id="logout-btn-top" style="padding: 8px 16px; background: var(--c-danger-alpha); color: var(--c-danger); border: none; border-radius: 4px; cursor: pointer;">
                <i class="ri-logout-box-r-line"></i> Chiqish
            </button>
        </header>
        <div style="flex: 1; overflow-y: auto; padding: 24px;">
        <div style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin-top: 0;">Kassir Terminali</h2>
                <p style="color: var(--text-muted);">To'lovlarni qabul qilish va chek chiqarish</p>
            </div>
            
            <div style="display: flex; gap: 12px; align-items: center;">
                <div style="display: flex; background: var(--bg-primary); padding: 4px; border-radius: 8px; border: 1px solid var(--c-border);">
                    <button class="btn btn-primary" id="tab-unpaid" style="padding: 6px 16px; border-radius: 4px; font-weight: 500;">To'lanmagan</button>
                    <button class="btn" id="tab-paid" style="padding: 6px 16px; border-radius: 4px; font-weight: 500; background: transparent; border: 1px solid transparent; color: var(--text-muted);">To'langan</button>
                </div>
                <div class="input-group" style="margin: 0;">
                    <input type="text" class="input-field" id="search-input" placeholder="Buyurtma Qidiruv..." style="min-width: 300px;">
                </div>
            </div>
        </div>
        
        <div class="cashier-list" id="orders-container">
            <div class="cashier-row header">
                <div>ID</div>
                <div>Stol</div>
                <div>Jami</div>
                <div>To'langan</div>
                <div>Qoldiq</div>
                <div style="text-align: right;">Amal</div>
            </div>
            <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                <i class="ri-loader-4-line" style="font-size: 32px; animation: spin 1s linear infinite;"></i>
                <p>Buyurtmalar yuklanmoqda...</p>
            </div>
        </div>

        <!-- Payment Modal -->
        <div id="payment-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center;">
            <div style="background: var(--bg-primary); border-radius: var(--border-radius-lg); padding: 32px; max-width: 450px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                <h3 style="margin-top: 0;">To'lov Qabul</h3>
                
                <div style="background: var(--bg-secondary); padding: 16px; border-radius: var(--border-radius-md); margin-bottom: 24px;">
                    <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 4px;">Buyurtma #<span id="modal-order-id">-</span> (Stol <span id="modal-table-no">-</span>)</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Jami summa:</span>
                        <span style="font-weight: 600;" id="modal-total">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>To'langan:</span>
                        <span style="font-weight: 600; color: var(--c-success);" id="modal-paid">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-top: 1px solid var(--c-border); padding-top: 8px;">
                        <span style="font-weight: 600;">Qoldiq:</span>
                        <span style="font-weight: 600; color: var(--c-primary); font-size: 1.1rem;" id="modal-remaining">0</span>
                    </div>
                </div>

                <div class="input-group" style="margin-bottom: 16px;">
                    <label class="input-label">To'lov summasini kiriting:</label>
                    <input type="number" id="modal-payment-amount" class="input-field" style="font-size: 1.1rem;" min="0" placeholder="0">
                </div>

                <div class="input-group" style="margin-bottom: 20px;">
                    <label class="input-label">To'lov usuli:</label>
                    <select id="modal-payment-method" class="input-field">
                        <option value="cash">Naqd pul</option>
                        <option value="card">Karta</option>
                        <option value="mixed">Aralash</option>
                    </select>
                </div>

                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button class="btn" style="background: transparent; border: 1px solid var(--c-border); flex: 1;" id="modal-cancel-btn">Bekor qilish</button>
                    <button class="btn btn-primary" style="flex: 1;" id="modal-pay-btn">To'lov qabul</button>
                </div>
            </div>
        </div>

        <!-- Order Details Modal -->
        <div id="details-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; overflow-y: auto;">
            <div style="background: var(--bg-primary); border-radius: var(--border-radius-lg); padding: 32px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3); margin: 40px auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                    <h3 style="margin: 0;">Buyurtma Tafsiloti</h3>
                    <button class="btn" style="background: transparent; border: 1px solid var(--c-border);" id="details-close-btn">Yopish</button>
                </div>

                <div id="details-content" style="max-height: 70vh; overflow-y: auto;"></div>
            </div>
        </div>
        </div>
    `;

    // Load orders
    async function loadOrders() {
        try {
            const endpoint = currentTab === 'unpaid' ? '/cashier/orders/unpaid' : '/cashier/orders/paid';
            orders = await apiCall(endpoint, 'GET');
            renderOrders(orders);
        } catch (error) {
            showToast('Buyurtmalar yuklanishida xatolik: ' + error.message, 'error');
        }
    }

    // Render orders
    function renderOrders(filteredOrders) {
        const container = document.querySelector('#orders-container');
        
        if (!filteredOrders || filteredOrders.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <p>Hozircha to'lanmagan buyurtmalar yo'q</p>
                </div>
            `;
            return;
        }

        const rowsHTML = filteredOrders.map(o => `
            <div class="cashier-row" style="cursor: pointer;" data-order-id="${o.id}">
                <div style="color: var(--text-muted);">#${o.id}</div>
                <div style="font-weight: 500;">${o.table_no || 'N/A'}</div>
                <div style="font-family: monospace; font-weight: 500;">${o.total_amount.toLocaleString()} so'm</div>
                <div style="font-family: monospace; color: var(--c-success);">${o.paid_amount.toLocaleString()} so'm</div>
                <div style="font-family: monospace; color: ${o.remaining_amount > 0 ? 'var(--c-warning)' : 'var(--c-success)'}; font-weight: 600;">${o.remaining_amount.toLocaleString()} so'm</div>
                <div style="text-align: right;">
                    ${o.status === 'closed'
                        ? `<span style="color: var(--c-success); font-weight: 500;"><i class="ri-check-double-line"></i> To'langan</span>`
                        : o.remaining_amount > 0 
                            ? `<button class="btn btn-primary" style="padding: 6px 12px;" data-order-id="${o.id}" onclick="event.stopPropagation();">To'lov</button>`
                            : `<button class="btn btn-success" style="padding: 6px 12px;" onclick="event.stopPropagation();">Yopish</button>`
                    }
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="cashier-row header">
                <div>ID</div>
                <div>Stol</div>
                <div>Jami</div>
                <div>To'langan</div>
                <div>Qoldiq</div>
                <div style="text-align: right;">Amal</div>
            </div>
            ${rowsHTML}
        `;

        // Add event listeners
        container.querySelectorAll('.btn-primary').forEach(btn => {
            btn.addEventListener('click', () => {
                const orderId = parseInt(btn.dataset.orderId);
                showPaymentModal(orderId);
            });
        });

        container.querySelectorAll('.btn-success').forEach(btn => {
            btn.addEventListener('click', async () => {
                // Find the order row
                const row = btn.closest('.cashier-row');
                const cells = row.querySelectorAll('div');
                const orderId = parseInt(cells[0].textContent.replace('#', ''));
                await closeOrder(orderId);
            });
        });

        // Row click to show details
        container.querySelectorAll('.cashier-row:not(.header)').forEach(row => {
            row.addEventListener('click', () => {
                const orderId = parseInt(row.dataset.orderId);
                showDetailsModal(orderId);
            });
        });
    }

    // Show payment modal
    function showPaymentModal(orderId) {
        const order = orders.find(o => o.id === orderId);
        if (!order) return;

        const modal = document.querySelector('#payment-modal');
        document.querySelector('#modal-order-id').textContent = order.id;
        document.querySelector('#modal-table-no').textContent = order.table_no || 'N/A';
        document.querySelector('#modal-total').textContent = order.total_amount.toLocaleString() + ' so\'m';
        document.querySelector('#modal-paid').textContent = order.paid_amount.toLocaleString() + ' so\'m';
        document.querySelector('#modal-remaining').textContent = order.remaining_amount.toLocaleString() + ' so\'m';
        document.querySelector('#modal-payment-amount').value = order.remaining_amount;
        document.querySelector('#modal-payment-method').value = 'cash';

        document.querySelector('#modal-cancel-btn').onclick = () => {
            modal.style.display = 'none';
        };

        document.querySelector('#modal-pay-btn').onclick = async () => {
            const amount = parseInt(document.querySelector('#modal-payment-amount').value);
            const method = document.querySelector('#modal-payment-method').value;

            if (!amount || amount <= 0) {
                showToast('To\'lov summasini kiriting!', 'error');
                return;
            }

            try {
                await apiCall(`/cashier/orders/${orderId}/pay`, 'POST', {
                    amount: amount,
                    method: method
                });
                showToast('To\'lov qabul qilindi!', 'success');
                modal.style.display = 'none';
                await loadOrders();
            } catch (error) {
                showToast('Xatolik: ' + error.message, 'error');
            }
        };

        modal.style.display = 'flex';
    }

    // Show details modal
    async function showDetailsModal(orderId) {
        try {
            const order = await apiCall(`/cashier/orders/${orderId}/summary`, 'GET');
            const modal = container.querySelector('#details-modal');
            const content = container.querySelector('#details-content');

            let total = 0;
            const itemsHTML = order.items.map(item => {
                const subtotal = item.qty * item.unit_price;
                total += subtotal;
                return `
                    <div style="padding: 12px; background: var(--bg-secondary); border-radius: var(--border-radius-sm); margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="font-weight: 500;">${item.menu_item_name}${item.variant_name ? ' - ' + item.variant_name : ''}</span>
                            <span style="color: var(--text-muted);">${item.qty}x${item.unit_price}</span>
                        </div>
                        <div style="text-align: right; font-weight: 600; color: var(--c-primary);">${subtotal} so\'m</div>
                    </div>
                `;
            }).join('');

            content.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: var(--text-muted);">Stol:</span>
                        <span style="font-weight: 600;">${order.table_no}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: var(--text-muted);">Waiter:</span>
                        <span style="font-weight: 600;">ID: ${order.waiter_id}</span>
                    </div>
                </div>

                <h4 style="margin-top: 0;">Buyurtma Itemi:</h4>
                <div style="margin-bottom: 20px;">
                    ${itemsHTML}
                </div>

                <div style="background: var(--bg-secondary); padding: 16px; border-radius: var(--border-radius-md); margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Jami:</span>
                        <span style="font-weight: 600;">${order.total_amount.toLocaleString()} so\'m</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>To\'langan:</span>
                        <span style="font-weight: 600; color: var(--c-success);">${order.paid_amount.toLocaleString()} so\'m</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-top: 1px solid var(--c-border); padding-top: 8px;">
                        <span style="font-weight: 600;">Qoldiq:</span>
                        <span style="font-weight: 600; color: ${order.remaining_amount > 0 ? 'var(--c-warning)' : 'var(--c-success)'};">${order.remaining_amount.toLocaleString()} so\'m</span>
                    </div>
                </div>

                <div style="display: flex; gap: 12px;">
                    <button class="btn" style="flex: 1; background: transparent; border: 1px solid var(--c-primary); color: var(--c-primary);" id="details-print-btn">
                        <i class="ri-printer-line"></i> Chek chiqarish
                    </button>
                    ${order.remaining_amount > 0 
                        ? `<button class="btn btn-primary" style="flex: 1;" class="details-action-btn" id="details-pay-btn">To'lov Qabul</button>`
                        : `<button class="btn btn-success" style="flex: 1;" class="details-action-btn" id="details-close-btn-bottom">Yopish</button>`
                    }
                </div>
            `;

            // Close header button
            modal.querySelector('#details-close-btn').addEventListener('click', () => {
                modal.style.display = 'none';
            }, { once: true });

            // Close bottom button if it exists
            const bottomCloseBtn = modal.querySelector('#details-close-btn-bottom');
            if (bottomCloseBtn) {
                bottomCloseBtn.addEventListener('click', () => {
                    modal.style.display = 'none';
                }, { once: true });
            }

            const printBtn = modal.querySelector('#details-print-btn');
            if (printBtn) {
                printBtn.addEventListener('click', () => {
                    printReceipt(order);
                });
            }

            const payBtn = modal.querySelector('#details-pay-btn');
            if (payBtn) {
                payBtn.addEventListener('click', () => {
                    modal.style.display = 'none';
                    showPaymentModal(orderId);
                });
            }

            modal.style.display = 'flex';
        } catch (error) {
            showToast('Tafsilot yuklanishida xatolik: ' + error.message, 'error');
        }
    }

    // Print receipt
    function printReceipt(order) {
        let itemsHtml = order.items.map(i => `
            <tr>
                <td style="padding: 4px 0;">${i.menu_item_name} ${i.variant_name ? '('+i.variant_name+')' : ''}</td>
                <td style="text-align: right; white-space: nowrap;">${i.qty} x ${i.unit_price}</td>
            </tr>
            <tr>
                <td colspan="2" style="text-align: right; font-weight: bold; padding-bottom: 8px;">${i.subtotal.toLocaleString()} so'm</td>
            </tr>
        `).join('');

        const html = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Chek #${order.id}</title>
                <style>
                    body { font-family: monospace; font-size: 14px; margin: 0; padding: 16px; color: #000; }
                    .center { text-align: center; }
                    .line { border-bottom: 1px dashed #000; margin: 10px 0; }
                    table { width: 100%; border-collapse: collapse; }
                </style>
            </head>
            <body>
                <h2 class="center" style="margin:0;">Ziyofat Day</h2>
                <p class="center" style="margin: 4px 0;">Kassir Cheki</p>
                <div class="line"></div>
                <p>Sana: ${new Date().toLocaleString('uz-UZ')}</p>
                <p>Buyurtma ID: #${order.id}</p>
                <p>Stol: ${order.table_no || 'N/A'}</p>
                <p>Ofitsiant ID: ${order.waiter_id}</p>
                <div class="line"></div>
                <table>
                    ${itemsHtml}
                </table>
                <div class="line"></div>
                <table>
                    <tr>
                        <td style="font-size: 16px; font-weight: bold;">Jami:</td>
                        <td style="font-size: 16px; font-weight: bold; text-align: right;">${order.total_amount.toLocaleString()}</td>
                    </tr>
                    <tr>
                        <td>To'langan:</td>
                        <td style="text-align: right;">${order.paid_amount.toLocaleString()}</td>
                    </tr>
                </table>
                <div class="line"></div>
                <p class="center" style="margin-top:20px;">Xaridingiz uchun rahmat!</p>
                <script>
                    window.onload = function() {
                        window.print();
                        setTimeout(() => window.close(), 500);
                    }
                </script>
            </body>
            </html>
        `;

        const printWindow = window.open('', '_blank', 'width=350,height=600');
        if (printWindow) {
            printWindow.document.open();
            printWindow.document.write(html);
            printWindow.document.close();
        } else {
            showToast('Chek ochish uchun popup ruxsati berilmadi', 'error');
        }
    }

    // Close order

    async function closeOrder(orderId) {
        if (confirm('Buyurtmani yopish rostmi?')) {
            try {
                await apiCall(`/cashier/orders/${orderId}/close`, 'POST');
                showToast('Buyurtma yopildi!', 'success');
                await loadOrders();
            } catch (error) {
                showToast('Xatolik: ' + error.message, 'error');
            }
        }
    }

    // Search functionality
    const searchInput = container.querySelector('#search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = orders.filter(o => 
                (o.table_no && o.table_no.toString().toLowerCase().includes(query)) || 
                o.id.toString().includes(query)
            );
            renderOrders(filtered);
        });
    }

    // Tab toggles
    const tabUnpaid = container.querySelector('#tab-unpaid');
    const tabPaid = container.querySelector('#tab-paid');

    if (tabUnpaid && tabPaid) {
        tabUnpaid.addEventListener('click', () => {
            currentTab = 'unpaid';
            tabUnpaid.className = 'btn btn-primary';
            tabUnpaid.style.background = '';
            tabUnpaid.style.color = '';
            tabPaid.className = 'btn';
            tabPaid.style.background = 'transparent';
            tabPaid.style.color = 'var(--text-muted)';
            loadOrders();
        });

        tabPaid.addEventListener('click', () => {
            currentTab = 'paid';
            tabPaid.className = 'btn btn-primary';
            tabPaid.style.background = '';
            tabPaid.style.color = '';
            tabUnpaid.className = 'btn';
            tabUnpaid.style.background = 'transparent';
            tabUnpaid.style.color = 'var(--text-muted)';
            loadOrders();
        });
    }

    // Close modals on background click
    const paymentModal = container.querySelector('#payment-modal');
    const detailsModal = container.querySelector('#details-modal');

    if (paymentModal) {
        paymentModal.addEventListener('click', (e) => {
            if (e.target === paymentModal) {
                paymentModal.style.display = 'none';
            }
        });
    }

    if (detailsModal) {
        detailsModal.addEventListener('click', (e) => {
            if (e.target === detailsModal) {
                detailsModal.style.display = 'none';
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

    // Load initial orders
    loadOrders();

    return container;
}
