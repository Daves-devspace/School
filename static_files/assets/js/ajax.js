// ajax.js

// Fetch updated fee records and update the table dynamically
function fetchFeeRecords() {
    $.ajax({
        url: '/accounts/students-with-balances/', // Update to match your view URL
        method: 'GET',
        success: function(data) {
            // Update the fee records table
            $('#fee-records-table').html(data);
        },
        error: function(error) {
            console.error("Error fetching fee records:", error);
        }
    });
}

// Example: Call fetchFeeRecords() every 10 seconds to refresh data
setInterval(fetchFeeRecords, 10000);
