function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatNumber(number) {
    return parseFloat(number).toFixed(2);
}

function filterTable(searchInput, tableBody, searchBy) {
    const searchTerm = searchInput.value.toLowerCase();
    const rows = tableBody.getElementsByTagName('tr');
    
    for (let row of rows) {
        let text = '';
        if (searchBy === 'all') {
            text = row.textContent.toLowerCase();
        } else {
            const cell = row.querySelector(`[data-field="${searchBy}"]`);
            text = cell ? cell.textContent.toLowerCase() : '';
        }
        
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    }
}

function setupSearch(searchId, tableId, searchById) {
    const searchInput = document.getElementById(searchId);
    const searchBySelect = document.getElementById(searchById);
    const tableBody = document.getElementById(tableId).getElementsByTagName('tbody')[0];
    
    searchInput.addEventListener('keyup', () => {
        filterTable(searchInput, tableBody, searchBySelect.value);
    });
    
    searchBySelect.addEventListener('change', () => {
        filterTable(searchInput, tableBody, searchBySelect.value);
    });
} 

let currentEntityId = null;
let currentEntityType = null;

function showCustomerHistory(customerId, customerName) {
    currentEntityId = customerId;
    currentEntityType = 'customer';
    loadEntityHistory(customerId, customerName, 'Customer');
}

function showSupplierHistory(supplierId, supplierName) {
    currentEntityId = supplierId;
    currentEntityType = 'supplier';
    loadEntityHistory(supplierId, supplierName, 'Supplier');
}

function loadEntityHistory(entityId, entityName, entityType) {
    fetch(`/api/${entityType.toLowerCase()}_history/${entityId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('historyTitle').textContent = `${entityName}'s History`;
            document.getElementById('currentBalance').textContent = 
                `$${formatNumber(data.current_balance || 0)}`;
            
            const tbody = document.getElementById('historyTransactions');
            tbody.innerHTML = '';
            
            let runningBalance = 0;
            data.transactions.forEach(trans => {
                runningBalance += ((trans.debit || 0) - (trans.credit || 0));
                tbody.innerHTML += `
                    <tr>
                        <td>${formatDate(trans.date)}</td>
                        <td>${trans.type}</td>
                        <td>${trans.description}</td>
                        <td>$${formatNumber(trans.debit || 0)}</td>
                        <td>$${formatNumber(trans.credit || 0)}</td>
                        <td>$${formatNumber(runningBalance)}</td>
                    </tr>
                `;
            });
            
            document.getElementById('historyModal').style.display = 'block';
        });
}

function showPaymentForm() {
    document.getElementById('paymentForm').style.display = 'block';
}

function submitPayment(event) {
    event.preventDefault();
    
    const paymentData = {
        entity_id: currentEntityId,
        entity_type: currentEntityType,
        amount: parseFloat(document.getElementById('paymentAmount').value),
        payment_method: document.getElementById('paymentMethod').value,
        reference: document.getElementById('paymentReference').value
    };
    
    fetch('/api/submit_payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(paymentData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload history to show new payment
            loadEntityHistory(currentEntityId, 
                document.getElementById('historyTitle').textContent.replace("'s History", ''),
                currentEntityType.charAt(0).toUpperCase() + currentEntityType.slice(1));
            document.getElementById('paymentForm').style.display = 'none';
        } else {
            alert('Error submitting payment: ' + data.error);
        }
    });
}

function hideHistoryModal() {
    document.getElementById('historyModal').style.display = 'none';
    document.getElementById('paymentForm').style.display = 'none';
} 

function generateSaleDetails(transaction) {
    return `
        <div class="transaction-details">
            <h3>Sale Details</h3>
            <div class="action-buttons">
                <a href="/invoice/sale/${transaction.id}" target="_blank" class="primary-button">View/Print Invoice</a>
            </div>
            <table class="details-table">
                <tr>
                    <td>Sale ID:</td>
                    <td>#${transaction.id}</td>
                </tr>
                <!-- rest of the table -->
    `;
}

function generatePurchaseDetails(transaction) {
    return `
        <div class="transaction-details">
            <h3>Purchase Details</h3>
            <div class="action-buttons">
                <a href="/invoice/purchase/${transaction.id}" target="_blank" class="primary-button">View/Print Invoice</a>
            </div>
            <table class="details-table">
                <tr>
                    <td>Purchase ID:</td>
                    <td>#${transaction.id}</td>
                </tr>
                <!-- rest of the table -->
    `;
}

function generateReturnDetails(transaction) {
    return `
        <div class="transaction-details">
            <h3>Return Details</h3>
            <div class="action-buttons">
                <a href="/invoice/return/${transaction.id}" target="_blank" class="primary-button">View/Print Invoice</a>
            </div>
            <table class="details-table">
                <tr>
                    <td>Return ID:</td>
                    <td>#${transaction.id}</td>
                </tr>
                <!-- rest of the table -->
    `;
} 