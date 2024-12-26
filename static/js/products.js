function showAddProductForm() {
    document.getElementById('addProductForm').style.display = 'block';
}

function hideAddProductForm() {
    document.getElementById('addProductForm').style.display = 'none';
}

function editProduct(productId) {
    // Implement edit functionality
    console.log('Editing product:', productId);
}

function deleteProduct(productId) {
    if (confirm('Are you sure you want to delete this product?')) {
        // Implement delete functionality
        console.log('Deleting product:', productId);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('addProductForm');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setupSearch('productSearch', 'productsTable', 'searchBy');
}); 