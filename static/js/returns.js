let customers = [];
let suppliers = [];

function showAddReturnForm(type) {
    document.getElementById('addReturnForm').style.display = 'block';
    document.getElementById('return_type').value = type;
    
    const title = document.getElementById('returnFormTitle');
    const label = document.getElementById('entityLabel');
    const entitySelect = document.getElementById('entity');
    
    // Clear previous options
    entitySelect.innerHTML = '<option value="">Select...</option>';
    
    if (type === 'customer') {
        title.textContent = 'Add Customer Return';
        label.textContent = 'Customer:';
        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = customer.name;
            entitySelect.appendChild(option);
        });
    } else {
        title.textContent = 'Add Supplier Return';
        label.textContent = 'Supplier:';
        suppliers.forEach(supplier => {
            const option = document.createElement('option');
            option.value = supplier.id;
            option.textContent = supplier.name;
            entitySelect.appendChild(option);
        });
    }
}

function hideAddReturnForm() {
    document.getElementById('addReturnForm').style.display = 'none';
}

function addItem() {
    const tbody = document.getElementById('itemsTableBody');
    const firstRow = tbody.querySelector('.item-row');
    const newRow = firstRow.cloneNode(true);
    
    // Clear values in the new row
    newRow.querySelectorAll('input').forEach(input => input.value = '');
    newRow.querySelector('select').selectedIndex = 0;
    newRow.querySelector('.original-price').textContent = '0.00';
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

function updateReturnPrice(select) {
    const row = select.closest('tr');
    const selectedOption = select.options[select.selectedIndex];
    const returnType = document.getElementById('return_type').value;
    
    if (selectedOption.value) {
        const originalPrice = returnType === 'customer' 
            ? selectedOption.dataset.retailPrice 
            : selectedOption.dataset.supplierPrice;
            
        row.querySelector('.original-price').textContent = originalPrice;
        row.querySelector('input[name="prices[]"]').value = originalPrice;
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
    
    // Update refund amount to match total by default
    document.getElementById('refund_amount').value = total.toFixed(2);
}

function viewReturn(returnId) {
    // Implement view functionality
    console.log('Viewing return:', returnId);
}

function deleteReturn(returnId) {
    if (confirm('Are you sure you want to delete this return?')) {
        // Implement delete functionality
        console.log('Deleting return:', returnId);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('addReturnForm');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Load customers and suppliers when page loads
fetch('/api/entities')
    .then(response => response.json())
    .then(data => {
        customers = data.customers;
        suppliers = data.suppliers;
    }); 