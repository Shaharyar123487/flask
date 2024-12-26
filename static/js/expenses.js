function showAddExpenseForm() {
    document.getElementById('addExpenseForm').style.display = 'block';
    // Set today's date as default
    document.getElementById('date').valueAsDate = new Date();
}

function hideAddExpenseForm() {
    document.getElementById('addExpenseForm').style.display = 'none';
}

function showAddCategoryForm() {
    document.getElementById('addCategoryForm').style.display = 'block';
}

function hideAddCategoryForm() {
    document.getElementById('addCategoryForm').style.display = 'none';
}

function editExpense(expenseId) {
    // Implement edit functionality
    console.log('Editing expense:', expenseId);
}

function deleteExpense(expenseId) {
    if (confirm('Are you sure you want to delete this expense?')) {
        // Implement delete functionality
        console.log('Deleting expense:', expenseId);
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
    }
} 