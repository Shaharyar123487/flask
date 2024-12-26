function showAddSupplierForm() {
    document.getElementById('addSupplierForm').style.display = 'block';
}

function hideAddSupplierForm() {
    document.getElementById('addSupplierForm').style.display = 'none';
}

function editSupplier(supplierId) {
    // Implement edit functionality
    console.log('Editing supplier:', supplierId);
}

function deleteSupplier(supplierId) {
    if (confirm('Are you sure you want to delete this supplier?')) {
        // Implement delete functionality
        console.log('Deleting supplier:', supplierId);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('addSupplierForm');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setupSearch('supplierSearch', 'suppliersTable', 'searchBy');
}); 