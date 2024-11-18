document.getElementById('transaction-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent default form submission

    // Collect form data
    const serialNo = document.getElementById('serial_no').value;
    const date = document.getElementById('date').value;
    const stockName = document.getElementById('name').value;
    const stockSymbol = document.getElementById('stock_symbol').value;
    const transactionType = document.getElementById('transaction_type').value;
    const shareCount = document.getElementById('count').value;
    const pricePerShare = document.getElementById('price').value;
    let totalAmount = document.getElementById('total_amount').value;

    // Auto-calculate total amount if left empty
    if (!totalAmount) {
        totalAmount = (shareCount * pricePerShare).toFixed(2);
        document.getElementById('total_amount').value = totalAmount;
    }

    // Prepare data for submission
    const formData = {
        serial_no: serialNo,
        date: date,
        name: stockName,
        stock_symbol: stockSymbol,
        transaction_type: transactionType,
        count: shareCount,
        price: pricePerShare,
        total_amount: totalAmount
    };

    try {
        // Send data to the server
        const response = await fetch('/transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert("Transaction submitted successfully!");
            window.location.href = "/stockDisplay"; // Redirect after success
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.message || 'An error occurred while submitting the transaction.'}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});
