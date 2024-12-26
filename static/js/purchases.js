function showAddPurchaseForm() {
    document.getElementById('addPurchaseForm').style.display = 'block';
}

function hideAddPurchaseForm() {
    document.getElementById('addPurchaseForm').style.display = 'none';
}

function addItem() {
    const tbody = document.getElementById('itemsTableBody');
    const firstRow = tbody.querySelector('.item-row');
    const newRow = firstRow.cloneNode(true);
    
    // Clear values in the new row
    newRow.querySelectorAll('input').forEach(input => input.value = '');
    newRow.querySelector('select').selectedIndex = 0;
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

function updatePrice(select) {
    const row = select.closest('tr');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        row.querySelector('input[name="supplier_prices[]"]').value = 
            selectedOption.dataset.supplierPrice;
        row.querySelector('input[name="wholesale_prices[]"]').value = 
            selectedOption.dataset.wholesalePrice;
        row.querySelector('input[name="retail_prices[]"]').value = 
            selectedOption.dataset.retailPrice;
        updateTotal(row.querySelector('input[name="supplier_prices[]"]'));
    }
}

function updateTotal(input) {
    const row = input.closest('tr');
    const quantity = parseFloat(row.querySelector('input[name="quantities[]"]').value) || 0;
    const price = parseFloat(row.querySelector('input[name="supplier_prices[]"]').value) || 0;
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

function viewPurchase(purchaseId) {
    fetch(`/api/purchases/${purchaseId}`)
        .then(response => response.json())
        .then(data => {
            const purchase = data.purchase;
            const items = data.items;
            
            let detailsHtml = `
                <div class="transaction-details">
                    <h3>Purchase Details</h3>
                    <table class="details-table">
                        <tr>
                            <td>Date:</td>
                            <td>${purchase.date}</td>
                        </tr>
                        <tr>
                            <td>Supplier:</td>
                            <td>${purchase.supplier_name}</td>
                        </tr>
                        <tr>
                            <td>Total Amount:</td>
                            <td>$${formatNumber(purchase.total_amount)}</td>
                        </tr>
                        <tr>
                            <td>Paid Amount:</td>
                            <td>$${formatNumber(purchase.paid_amount)}</td>
                        </tr>
                        <tr>
                            <td>Balance:</td>
                            <td>$${formatNumber(purchase.total_amount - purchase.paid_amount)}</td>
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

function deletePurchase(purchaseId) {
    if (confirm('Are you sure you want to delete this purchase?')) {
        // Implement delete functionality
        console.log('Deleting purchase:', purchaseId);
    }
}

function hideTransactionModal() {
    document.getElementById('transactionModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('addPurchaseForm');
    const transactionModal = document.getElementById('transactionModal');
    if (event.target == modal) {
        modal.style.display = "none";
    } else if (event.target == transactionModal) {
        transactionModal.style.display = "none";
    }
}

function addPurchase(event) {
    event.preventDefault();
    
    // Get form data
    const items = [];
    const rows = document.querySelectorAll('#itemsTableBody tr');
    
    rows.forEach(row => {
        const productSelect = row.querySelector('select[name="products[]"]');
        const quantity = row.querySelector('input[name="quantities[]"]').value;
        const price = row.querySelector('input[name="supplier_prices[]"]').value;
        
        if (productSelect.value && quantity && price) {
            items.push({
                product_id: parseInt(productSelect.value),
                quantity: parseInt(quantity),
                price: parseFloat(price)
            });
        }
    });
    
    const purchaseData = {
        supplier_id: parseInt(document.getElementById('supplier_id').value),
        items: items,
        paid_amount: parseFloat(document.getElementById('paid_amount').value || 0)
    };
    
    fetch('/add_purchase', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(purchaseData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Purchase added successfully');
            hideAddPurchaseForm();
            location.reload();
        } else {
            alert('Error adding purchase: ' + data.message);
        }
    });
}

function updateProductPrices(supplierPrices) {
    for (let productId in supplierPrices) {
        localStorage.setItem(`supplier_price_${productId}`, supplierPrices[productId]);
    }
} 