function showAddSaleForm() {
    document.getElementById('addSaleForm').style.display = 'block';
}

function hideAddSaleForm() {
    document.getElementById('addSaleForm').style.display = 'none';
}

function addItem() {
    const tbody = document.getElementById('itemsTableBody');
    const firstRow = tbody.querySelector('.item-row');
    const newRow = firstRow.cloneNode(true);
    
    // Clear values in the new row
    newRow.querySelectorAll('input').forEach(input => input.value = '');
    newRow.querySelector('select').selectedIndex = 0;
    newRow.querySelector('.available-qty').textContent = '0';
    newRow.querySelector('.supplier-price').textContent = '0.00';
    newRow.querySelector('.wholesale-price').textContent = '0.00';
    newRow.querySelector('.retail-price').textContent = '0.00';
    newRow.querySelector('.item-total').textContent = '0.00';
    
    tbody.appendChild(newRow);
}

function removeItem(button) {
    const tbody = document.getElementById('itemsTableBody');
    if (tbody.children.length > 1) {
        button.closest('tr').remove();
        calculateTotal();
    }
}

function updatePrices(select) {
    const row = select.closest('tr');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        row.querySelector('.available-qty').textContent = selectedOption.dataset.quantity;
        row.querySelector('.supplier-price').textContent = selectedOption.dataset.supplierPrice;
        row.querySelector('.wholesale-price').textContent = selectedOption.dataset.wholesalePrice;
        row.querySelector('.retail-price').textContent = selectedOption.dataset.retailPrice;
        row.querySelector('input[name="prices[]"]').value = selectedOption.dataset.retailPrice;
        updateTotal(row.querySelector('input[name="prices[]"]'));
    }
}

function updateTotal(input) {
    const row = input.closest('tr');
    const quantity = parseFloat(row.querySelector('input[name="quantities[]"]').value) || 0;
    const price = parseFloat(row.querySelector('input[name="prices[]"]').value) || 0;
    const total = quantity * price;
    
    row.querySelector('.item-total').textContent = total.toFixed(2);
    calculateTotal();
}

function calculateTotal() {
    const totals = Array.from(document.getElementsByClassName('item-total'))
        .map(span => parseFloat(span.textContent) || 0);
    const total = totals.reduce((sum, val) => sum + val, 0);
    document.getElementById('totalAmount').textContent = `$${total.toFixed(2)}`;
}

function viewSale(saleId) {
    fetch(`/api/sales/${saleId}`)
        .then(response => response.json())
        .then(data => {
            const sale = data.sale;
            const items = data.items;
            
            let detailsHtml = `
                <div class="transaction-details">
                    <h3>Sale Details</h3>
                    <table class="details-table">
                        <tr>
                            <td>Date:</td>
                            <td>${sale.date}</td>
                        </tr>
                        <tr>
                            <td>Customer:</td>
                            <td>${sale.customer_name}</td>
                        </tr>
                        <tr>
                            <td>Total Amount:</td>
                            <td>$${formatNumber(sale.total_amount)}</td>
                        </tr>
                        <tr>
                            <td>Paid Amount:</td>
                            <td>$${formatNumber(sale.paid_amount)}</td>
                        </tr>
                        <tr>
                            <td>Balance:</td>
                            <td>$${formatNumber(sale.total_amount - sale.paid_amount)}</td>
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
                            ${items.map(item => `
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
            
            document.getElementById('transactionDetails').innerHTML = detailsHtml;
            document.getElementById('transactionModal').style.display = 'block';
        });
}

function formatNumber(number) {
    return parseFloat(number).toFixed(2);
}

function deleteSale(saleId) {
    if (confirm('Are you sure you want to delete this sale?')) {
        // Implement delete functionality
        console.log('Deleting sale:', saleId);
    }
}

function hideTransactionModal() {
    document.getElementById('transactionModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('addSaleForm');
    const transactionModal = document.getElementById('transactionModal');
    if (event.target == modal) {
        modal.style.display = "none";
    } else if (event.target == transactionModal) {
        transactionModal.style.display = "none";
    }
} 