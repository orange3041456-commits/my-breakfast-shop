function buy(n, p, i, hasOpts) {
    if (curType === '內用' && !curT) { alert("⚠️ 內用請先選擇桌號！"); return; }
    
    let fn = n, fp = p;
    let selectedOpts = [];
    let drinkSelected = false;

    // 遍歷所有已選選項
    Object.keys(opts).forEach(k => {
        if (k.indexOf(i + '_') === 0) {
            fn += '+' + opts[k].n;
            fp += opts[k].p;
            // 檢查是否選了「飲品」或「炸物」這類套餐選項 (這類選項在 opts 中通常沒有加價，或是屬於套餐的一部分)
            if (opts[k].n.includes("選")) {
                drinkSelected = true;
            }
        }
    });

    // 強制邏輯：如果有套餐選單(hasOpts > 0) 但沒選飲品，不准加入
    if (hasOpts > 0 && !drinkSelected) {
        alert("⚠️ 請務必選擇飲品（紅茶或冷泡茶）！");
        return;
    }

    fetch('/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: "name=" + encodeURIComponent(fn) + "&price=" + fp
    })
    .then(r => r.json()).then(d => {
        document.getElementById('cc').innerText = d.count;
        document.getElementById('ct').innerText = d.total;
        // 清除該格已選狀態
        document.querySelectorAll(".opt[data-item='" + i + "']").forEach(x => x.classList.remove('active'));
        Object.keys(opts).forEach(k => { if (k.indexOf(i + '_') === 0) delete opts[k] });
    })
}
