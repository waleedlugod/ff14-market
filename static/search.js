let historySortNewest = true;

const tabs = document.querySelectorAll(".tab-item");
const panels = document.querySelectorAll(".content-panel");
const searchInput = document.getElementById("search-input");

tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.remove("active"));
        panels.forEach(p => p.classList.remove("active"));

        tab.classList.add("active");
        document.getElementById(tab.dataset.tab).classList.add("active");

        if (tab.dataset.tab === "items-tab") fetchItems(searchInput.value);
        else if (tab.dataset.tab === "history-tab") loadHistory();
    });
});

searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim();
    if (document.getElementById("items-tab").classList.contains("active")) {
        fetchItems(query);
    } else {
        filterHistory(query);
    }
});

function fetchItems(searchQuery = "") {
    fetch(`http://127.0.0.1:5000/postings?search=${encodeURIComponent(searchQuery)}`)
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById("items-body");
            tbody.innerHTML = "";

            data.forEach(item => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${item.itemName || "Unknown Item"}</td>
                    <td>${item.itemPrice || "N/A"}</td>
                    <td>${item.itemQuantity || "N/A"}</td>
                    <td>
                        <button class="cta-button cta-secondary"
                            style="padding: 4px 8px; font-size: 12px; margin-bottom:4px;
                            margin-left:4px;"
                            onclick="editItem('${item._id}', '${item.itemName}', 
                            '${item.itemPrice}', '${item.itemQuantity}')">Update</button><br>

                        <button class="cta-button cta-secondary"
                            style="padding: 4px 8px; font-size: 12px; margin-left: 4px;"
                            onclick="deleteItem('${item._id}')">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
}

let editingItemID = null;

function editItem(id, name, price, quantity) {
    editingItemID = id;

    document.getElementById("item-name").value = name;
    document.getElementById("item-price").value = price;
    document.getElementById("item-quantity").value = quantity;

    openItemModal();
}

function loadHistory() {
    fetch("http://127.0.0.1:5000/history")
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById("history-body");
            tbody.innerHTML = "";
            data.forEach(entry => {
                const row = document.createElement("tr");
                row.dataset.timestamp = new Date(entry.timestamp).getTime();
                const readableTime = new Date(entry.timestamp).toLocaleString();
                row.innerHTML = `
                    <td>${entry.userCustomer}</td>
                    <td>${entry.itemName}</td>
                    <td>${entry.itemPrice}</td>
                    <td>${entry.amountSold}</td>
                    <td>${readableTime}</td>
                    <td>
                        <button class="cta-button cta-secondary"
                                style="padding: 4px 8px; font-size: 12px; margin-bottom:4px;"
                                onclick="editHistory('${entry._id}', 
                                '${entry.userCustomer}', '${entry.itemName}', 
                                '${entry.itemPrice}', '${entry.amountSold}')">Update</button><br>

                        <button class="cta-button cta-secondary"
                            style="padding: 4px 8px; font-size: 12px;"
                            onclick="deleteHistory('${entry._id}')">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
}

let editingHistoryID = null;

function editHistory(id, buyer, itemName, price, amount) {
    editingHistoryID = id;

    document.getElementById("history-buyer").value = buyer;
    document.getElementById("history-item").value = itemName;
    document.getElementById("history-price").value = price;
    document.getElementById("history-quantity").value = amount;

    openHistoryModal();
}

function sortHistoryByTime() {
    const tbody = document.getElementById("history-body");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    rows.sort((a, b) => {
        const t1 = parseInt(a.dataset.timestamp);
        const t2 = parseInt(b.dataset.timestamp);
        return historySortNewest ? t2 - t1 : t1 - t2;
    });

    rows.forEach(row => tbody.appendChild(row));
    historySortNewest = !historySortNewest; 
}

function filterHistory(query) {
    const rows = document.querySelectorAll("#history-body tr");
    rows.forEach(row => {
        const match = row.cells[0].textContent.toLowerCase().includes(query.toLowerCase()) ||
                      row.cells[1].textContent.toLowerCase().includes(query.toLowerCase());
        row.style.display = match ? "" : "none";
    });
}

function filterItems(query) {
    const rows = document.querySelectorAll("#items-body tr");
    rows.forEach(row => {
        const nameMatch = row.cells[0].textContent.toLowerCase().includes(query.toLowerCase());
        const priceMatch = row.cells[1].textContent.toLowerCase().includes(query.toLowerCase());
        row.style.display = (nameMatch || priceMatch) ? "" : "none";
    });
}

function deleteHistory(entryID) {
    fetch("http://127.0.0.1:5000/delete_history", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ entryID })
    }).then(res => res.json())
      .then(res => {
        if(res.success) loadHistory();
        else alert(res.message);
    });
}

function deleteItem(itemID) {
    fetch("http://127.0.0.1:5000/delete", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ itemID })
    }).then(res => res.json())
      .then(res => {
        if(res.success) fetchItems();
        else alert(res.message);
    });
}

document.addEventListener("DOMContentLoaded", () => {

    const historyModal = document.getElementById("history-modal");
    const historyForm = document.getElementById("history-form");
    const historyCancel = document.getElementById("history-cancel");

    function openHistoryModal() { historyModal.classList.add("active"); }
    function closeHistoryModal() { historyModal.classList.remove("active"); historyForm.reset(); }

    historyCancel.addEventListener("click", closeHistoryModal);
    historyForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const buyer = document.getElementById("history-buyer").value;
        const itemName = document.getElementById("history-item").value;
        const price = parseFloat(document.getElementById("history-price").value);
        const quantity = parseInt(document.getElementById("history-quantity").value);

        const payload = {
            userCustomer: buyer,
            itemName,
            itemPrice: price,
            amountSold: quantity
        };

        let url = "http://127.0.0.1:5000/add_history";
    
        if (editingHistoryID) {
            payload.entryID = editingHistoryID;
            url = "http://127.0.0.1:5000/update_history";
        }

        fetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(res => {
            if(res.success) { 
                loadHistory(); 
                closeHistoryModal(); 
                editingHistoryID = null;
                alert(editingHistoryID ? "Updated!" : "Entry added!"); }
            else alert(res.message);
        });
    });

    const itemModal = document.getElementById("item-modal");
    const itemForm = document.getElementById("item-form");
    const itemCancel = document.getElementById("item-cancel");

    function openItemModal() { itemModal.classList.add("active"); }
    function closeItemModal() { itemModal.classList.remove("active"); itemForm.reset(); }

    itemCancel.addEventListener("click", closeItemModal);
    itemForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const username = document.getElementById("item-username").value;
        const name = document.getElementById("item-name").value;
        const price = parseFloat(document.getElementById("item-price").value);
        const quantity = parseInt(document.getElementById("item-quantity").value);

        const payload = {
            username,
            itemName: name,
            itemPrice: price,
            itemQuantity: quantity
        };

        let url = "http://127.0.0.1:5000/add";

        if (editingItemID) {
            payload.itemID = editingItemID;
            url = "http://127.0.0.1:5000/update_item";
        }
    
        fetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(res => {
            if(res.success) { 
                fetchItems(); 
                closeItemModal(); 
                editingItemID = null;
                alert(editingItemID ? "Updated!" : "Item added!"); }
            else alert(res.message);
        });
    });

    window.openHistoryModal = openHistoryModal;
    window.openItemModal = openItemModal;
});

fetchItems();
loadHistory();
