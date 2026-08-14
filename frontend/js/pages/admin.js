import { apiCall, showToast } from '../api.js';
import { store, API_BASE } from '../store.js';

export default async function renderAdmin() {
    const container = document.createElement('div');
    container.style.cssText = 'display: flex; flex-direction: column; height: 100%; overflow: hidden;';

    let period = 'daily';
    let days = 30;

    container.innerHTML = `
        <header style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--c-border); background: var(--bg-secondary);">
            <div>
                <h1 style="margin: 0; font-size: 1.2rem;">Admin Paneli</h1>
                <p style="margin: 4px 0 0; color: var(--text-muted); font-size: 0.9rem;">${store.user?.username || 'Admin'}</p>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <a href="${API_BASE}/admin/" style="padding: 8px 16px; background: var(--bg-primary); border: 1px solid var(--c-border); border-radius: 4px; color: var(--text-primary); text-decoration: none;">
                    <i class="ri-settings-3-line"></i> Boshqaruv paneli
                </a>
                <button id="logout-btn-top" style="padding: 8px 16px; background: var(--c-danger-alpha); color: var(--c-danger); border: none; border-radius: 4px; cursor: pointer;">
                    <i class="ri-logout-box-r-line"></i> Chiqish
                </button>
            </div>
        </header>
        <div style="flex: 1; overflow-y: auto; padding: 24px;">
            <div style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h2 style="margin-top: 0;">Daromad va Foyda Hisoboti</h2>
                    <p style="color: var(--text-muted); margin: 0;">Mahsulot tan narxidan kelib chiqib hisoblangan sof foyda</p>
                </div>

                <div style="display: flex; gap: 12px; align-items: center;">
                    <div style="display: flex; background: var(--bg-primary); padding: 4px; border-radius: 8px; border: 1px solid var(--c-border);">
                        <button class="btn btn-primary" id="tab-daily" style="padding: 6px 16px; border-radius: 4px; font-weight: 500;">Kunlik</button>
                        <button class="btn" id="tab-monthly" style="padding: 6px 16px; border-radius: 4px; font-weight: 500; background: transparent; border: 1px solid transparent; color: var(--text-muted);">Oylik</button>
                    </div>
                    <select id="days-select" class="input-field" style="width: auto;">
                        <option value="7">Oxirgi 7 kun</option>
                        <option value="30" selected>Oxirgi 30 kun</option>
                        <option value="90">Oxirgi 90 kun</option>
                        <option value="365">Oxirgi 1 yil</option>
                    </select>
                </div>
            </div>

            <div id="summary-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;"></div>

            <div id="report-table"></div>
        </div>
    `;

    function money(n) {
        return (n || 0).toLocaleString() + " so'm";
    }

    function renderSummary(report) {
        const cards = container.querySelector('#summary-cards');
        cards.innerHTML = `
            <div style="background: var(--bg-secondary); border: 1px solid var(--c-border); border-radius: var(--border-radius-md); padding: 16px;">
                <div style="color: var(--text-muted); font-size: 0.85rem;">Buyurtmalar</div>
                <div style="font-size: 1.4rem; font-weight: 600; margin-top: 4px;">${report.total_orders}</div>
            </div>
            <div style="background: var(--bg-secondary); border: 1px solid var(--c-border); border-radius: var(--border-radius-md); padding: 16px;">
                <div style="color: var(--text-muted); font-size: 0.85rem;">Jami daromad</div>
                <div style="font-size: 1.4rem; font-weight: 600; margin-top: 4px; color: var(--c-success);">${money(report.total_revenue)}</div>
            </div>
            <div style="background: var(--bg-secondary); border: 1px solid var(--c-border); border-radius: var(--border-radius-md); padding: 16px;">
                <div style="color: var(--text-muted); font-size: 0.85rem;">Tan narx sarfi</div>
                <div style="font-size: 1.4rem; font-weight: 600; margin-top: 4px; color: var(--c-warning);">${money(report.total_cost)}</div>
            </div>
            <div style="background: var(--bg-secondary); border: 1px solid var(--c-border); border-radius: var(--border-radius-md); padding: 16px;">
                <div style="color: var(--text-muted); font-size: 0.85rem;">Sof foyda</div>
                <div style="font-size: 1.4rem; font-weight: 600; margin-top: 4px; color: var(--c-primary);">${money(report.total_profit)}</div>
            </div>
        `;
    }

    function renderTable(report) {
        const wrap = container.querySelector('#report-table');

        if (!report.buckets || report.buckets.length === 0) {
            wrap.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted); background: var(--bg-secondary); border-radius: var(--border-radius-md); border: 1px solid var(--c-border);">
                    <p>Tanlangan davrda yopilgan buyurtma topilmadi</p>
                </div>
            `;
            return;
        }

        const rowsHTML = [...report.buckets].reverse().map(b => `
            <div class="cashier-row">
                <div>${b.period}</div>
                <div>${b.orders_count}</div>
                <div style="font-family: monospace; color: var(--c-success);">${money(b.revenue)}</div>
                <div style="font-family: monospace; color: var(--c-warning);">${money(b.cost)}</div>
                <div style="font-family: monospace; font-weight: 600; color: var(--c-primary);">${money(b.profit)}</div>
            </div>
        `).join('');

        wrap.innerHTML = `
            <div class="cashier-list">
                <div class="cashier-row header">
                    <div>Davr</div>
                    <div>Buyurtmalar</div>
                    <div>Daromad</div>
                    <div>Tan narx</div>
                    <div>Foyda</div>
                </div>
                ${rowsHTML}
            </div>
        `;
    }

    async function loadReport() {
        const wrap = container.querySelector('#report-table');
        wrap.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                <i class="ri-loader-4-line" style="font-size: 32px; animation: spin 1s linear infinite;"></i>
                <p>Hisobot yuklanmoqda...</p>
            </div>
        `;
        try {
            const report = await apiCall(`/reports/revenue?period=${period}&days=${days}`, 'GET');
            renderSummary(report);
            renderTable(report);
        } catch (error) {
            showToast('Hisobot yuklanishida xatolik: ' + error.message, 'error');
        }
    }

    const tabDaily = container.querySelector('#tab-daily');
    const tabMonthly = container.querySelector('#tab-monthly');

    tabDaily.addEventListener('click', () => {
        period = 'daily';
        tabDaily.className = 'btn btn-primary';
        tabDaily.style.background = '';
        tabDaily.style.color = '';
        tabMonthly.className = 'btn';
        tabMonthly.style.background = 'transparent';
        tabMonthly.style.color = 'var(--text-muted)';
        loadReport();
    });

    tabMonthly.addEventListener('click', () => {
        period = 'monthly';
        tabMonthly.className = 'btn btn-primary';
        tabMonthly.style.background = '';
        tabMonthly.style.color = '';
        tabDaily.className = 'btn';
        tabDaily.style.background = 'transparent';
        tabDaily.style.color = 'var(--text-muted)';
        loadReport();
    });

    container.querySelector('#days-select').addEventListener('change', (e) => {
        days = parseInt(e.target.value);
        loadReport();
    });

    container.querySelector('#logout-btn-top').addEventListener('click', () => {
        store.logout();
        window.dispatchEvent(new CustomEvent('navTo', { detail: '/login' }));
    });

    loadReport();

    return container;
}
