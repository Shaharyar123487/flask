function showAddCustomerForm() {
    document.getElementById('addCustomerForm').style.display = 'block';
}

function hideAddCustomerForm() {
    document.getElementById('addCustomerForm').style.display = 'none';
}

function editCustomer(customerId) {
    // Implement edit functionality
    console.log('Editing customer:', customerId);
}

function deleteCustomer(customerId) {
    if (confirm('Are you sure you want to delete this customer?')) {
        // Implement delete functionality
        console.log('Deleting customer:', customerId);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('addCustomerForm');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setupSearch('customerSearch', 'customersTable', 'searchBy');
}); 