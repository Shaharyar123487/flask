let currentReport = 'customer';
let customers = [];
let suppliers = [];
let currentTransactions = [];

function showReport(type) {
    // Hide all reports
    document.querySelectorAll('.report-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected report
    document.getElementById(`${type}Report`).style.display = 'block';
    
    // Update active button
    document.querySelectorAll('.nav-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${type}Btn`).classList.add('active');
    
    // Update entity filter options
    const entitySelect = document.getElementById('entitySelect');
    entitySelect.innerHTML = '<option value="">All</option>';
    
    if (type === 'customer') {
        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = customer.name;
            entitySelect.appendChild(option);
        });
        document.getElementById('entityFilter').style.display = 'flex';
    } else if (type === 'supplier') {
        suppliers.forEach(supplier => {
            const option = document.createElement('option');
            option.value = supplier.id;
            option.textContent = supplier.name;
            entitySelect.appendChild(option);
        });
        document.getElementById('entityFilter').style.display = 'flex';
    } else {
        document.getElementById('entityFilter').style.display = 'none';
    }
    
    currentReport = type;
    updateReport();
}

function updateReport() {
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const entityId = document.getElementById('entitySelect').value;
    const searchTerm = document.getElementById('searchInput').value;
    const transactionType = document.getElementById('transactionTypeFilter')?.value || '';
    
    fetch('/api/reports', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            report_type: currentReport,
            date_from: dateFrom,
            date_to: dateTo,
            entity_id: entityId,
            search_term: searchTerm,
            transaction_type: transactionType
        })
    })
    .then(response => response.json())
    .then(data => {
        updateReportTable(data);
    });
}

function updateReportTable(data) {
    const tbody = document.getElementById(`${currentReport}Transactions`);
    tbody.innerHTML = '';
    currentTransactions = data.transactions;
    
    if (currentReport === 'all') {
        data.transactions.forEach((trans, index) => {
            tbody.innerHTML += `
                <tr onclick="showTransactionDetails(${index})">
                    <td>${formatDate(trans.date)}</td>
                    <td>${trans.type}</td>
                    <td>${trans.entity_name}</td>
                    <td>${trans.description}</td>
                    <td>$${formatNumber(trans.amount)}</td>
                    <td><span class="status-${trans.status.toLowerCase()}">${trans.status}</span></td>
                </tr>
            `;
        });
    } else if (currentReport === 'customer' || currentReport === 'supplier') {
        data.transactions.forEach((trans, index) => {
            const entityName = currentReport === 'customer' ? 
                trans.customer_name : trans.supplier_name;
            tbody.innerHTML += `
                <tr onclick="showTransactionDetails(${index})">
                    <td>${formatDate(trans.date)}</td>
                    <td>${entityName}</td>
                    <td>${trans.type}</td>
                    <td>${trans.description}</td>
                    <td>$${formatNumber(trans.debit)}</td>
                    <td>$${formatNumber(trans.credit)}</td>
                    <td>$${formatNumber(trans.balance)}</td>
                </tr>
            `;
        });
    } else if (currentReport === 'expense') {
        data.transactions.forEach(expense => {
            tbody.innerHTML += `
                <tr>
                    <td>${formatDate(expense.date)}</td>
                    <td>${expense.category_name}</td>
                    <td>${expense.description}</td>
                    <td>${expense.payment_method}</td>
                    <td>${expense.reference_no || '-'}</td>
                    <td>$${formatNumber(expense.amount)}</td>
                </tr>
            `;
        });
        document.getElementById('expenseTotal').textContent = `$${formatNumber(data.total)}`;
    } else if (currentReport === 'summary') {
        updateSummary(data);
    }
}

function updateSummary(data) {
    // Update summary cards with the new data
    document.querySelector('#summaryReport .summary-cards').innerHTML = `
        <div class="summary-card">
            <h3>Sales</h3>
            <div class="amount">$${formatNumber(data.total_sales)}</div>
            <div class="detail">Received: $${formatNumber(data.received_sales)}</div>
            <div class="detail">Outstanding: $${formatNumber(data.outstanding_sales)}</div>
        </div>
        <div class="summary-card">
            <h3>Purchases</h3>
            <div class="amount">$${formatNumber(data.total_purchases)}</div>
            <div class="detail">Paid: $${formatNumber(data.paid_purchases)}</div>
            <div class="detail">Outstanding: $${formatNumber(data.outstanding_purchases)}</div>
        </div>
        <div class="summary-card">
            <h3>Expenses</h3>
            <div class="amount">$${formatNumber(data.total_expenses)}</div>
        </div>
        <div class="summary-card">
            <h3>Net Position</h3>
            <div class="amount">$${formatNumber(data.net_position)}</div>
        </div>
    `;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

function formatNumber(number) {
    return number.toFixed(2);
}

function filterReport() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const tbody = document.getElementById(`${currentReport}Transactions`);
    const rows = tbody.getElementsByTagName('tr');
    
    for (let row of rows) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    }
}

function showTransactionDetails(index) {
    const transaction = currentTransactions[index];
    const modal = document.getElementById('transactionModal');
    const detailsDiv = document.getElementById('transactionDetails');
    
    let detailsHtml = '';
    
    if (transaction.type === 'Sale') {
        detailsHtml = generateSaleDetails(transaction);
    } else if (transaction.type === 'Purchase') {
        detailsHtml = generatePurchaseDetails(transaction);
    } else if (transaction.type === 'Expense') {
        detailsHtml = generateExpenseDetails(transaction);
    }
    
    detailsDiv.innerHTML = detailsHtml;
    modal.style.display = 'block';
}

function generateSaleDetails(transaction) {
    return `
        <div class="transaction-details">
            <h3>Sale Details</h3>
            <table class="details-table">
                <tr>
                    <td>Date:</td>
                    <td>${formatDate(transaction.date)}</td>
                </tr>
                <tr>
                    <td>Customer:</td>
                    <td>${transaction.customer_name}</td>
                </tr>
                <tr>
                    <td>Total Amount:</td>
                    <td>$${formatNumber(transaction.debit)}</td>
                </tr>
                <tr>
                    <td>Paid Amount:</td>
                    <td>$${formatNumber(transaction.credit)}</td>
                </tr>
            </table>
            
            <h4>Items</h4>
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${transaction.items.map(item => `
                        <tr>
                            <td>${item.product_name}</td>
                            <td>${item.quantity}</td>
                            <td>$${formatNumber(item.price)}</td>
                            <td>$${formatNumber(item.quantity * item.price)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function generatePurchaseDetails(transaction) {
    return `
        <div class="transaction-details">
            <h3>Purchase Details</h3>
            <table class="details-table">
                <tr>
                    <td>Date:</td>
                    <td>${formatDate(transaction.date)}</td>
                </tr>
                <tr>
                    <td>Supplier:</td>
                    <td>${transaction.supplier_name}</td>
                </tr>
                <tr>
                    <td>Total Amount:</td>
                    <td>$${formatNumber(transaction.debit)}</td>
                </tr>
                <tr>
                    <td>Paid Amount:</td>
                    <td>$${formatNumber(transaction.credit)}</td>
                </tr>
            </table>
            
            <h4>Items</h4>
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${transaction.items.map(item => `
                        <tr>
                            <td>${item.product_name}</td>
                            <td>${item.quantity}</td>
                            <td>$${formatNumber(item.price)}</td>
                            <td>$${formatNumber(item.quantity * item.price)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function generateExpenseDetails(transaction) {
    return `
        <div class="transaction-details">
            <h3>Expense Details</h3>
            <table class="details-table">
                <tr>
                    <td>Date:</td>
                    <td>${formatDate(transaction.date)}</td>
                </tr>
                <tr>
                    <td>Category:</td>
                    <td>${transaction.category_name}</td>
                </tr>
                <tr>
                    <td>Description:</td>
                    <td>${transaction.description}</td>
                </tr>
                <tr>
                    <td>Amount:</td>
                    <td>$${formatNumber(transaction.amount)}</td>
                </tr>
                <tr>
                    <td>Payment Method:</td>
                    <td>${transaction.payment_method}</td>
                </tr>
                <tr>
                    <td>Reference:</td>
                    <td>${transaction.reference_no || '-'}</td>
                </tr>
            </table>
        </div>
    `;
}

function hideTransactionModal() {
    document.getElementById('transactionModal').style.display = 'none';
}

// Initialize date inputs and load data when page loads
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    
    document.getElementById('dateFrom').valueAsDate = firstDay;
    document.getElementById('dateTo').valueAsDate = today;
    
    // Update summary with initial data
    if (typeof initialSummary !== 'undefined') {
        updateSummary(initialSummary);
    }
    
    // Load initial data
    fetch('/api/entities')
        .then(response => response.json())
        .then(data => {
            customers = data.customers;
            suppliers = data.suppliers;
            showReport('customer');
        });
}); 