// transaction.js
document.getElementById('transaction-form').addEventListener('submit', function(event) {
    event.preventDefault();

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

    // Display transaction summary
    alert(`Transaction Summary:
    Serial No: ${serialNo}
    Date: ${date}
    Stock Name: ${stockName}
    Stock Symbol: ${stockSymbol}
    Transaction Type: ${transactionType}
    Number of Shares: ${shareCount}
    Price per Share: ₹${pricePerShare}
    Total Amount: ₹${totalAmount}`);
});
