// static/script.js
document.addEventListener("DOMContentLoaded", function () {
    fetchRealizedProfit();
    fetchHeldStocks();
    fetchSoldStocks();
});

function fetchRealizedProfit() {
    fetch("/api/profit")
        .then(response => response.json())
        .then(data => {
            document.getElementById("realized-profit").textContent = `${data.realized_profit.toFixed(2)}`;
        })
        .catch(error => console.error("Error fetching realized profit:", error));
}

function fetchHeldStocks() {
    fetch("/api/held_stocks")
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById("portfolio-table").getElementsByTagName("tbody")[0];
            tbody.innerHTML = ""; // Clear existing rows
            data.forEach(stock => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${stock.Share}</td>
                    <td>${stock.Symbol}</td>
                    <td>${stock["Net Shares"]}</td>
                    <td>${stock["Current Price"].toFixed(2)}</td>
                    <td>${stock["Potential Sale Value"].toFixed(2)}</td>
                    <td>${stock["Potential Sale Profit/Loss"].toFixed(2)}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error("Error fetching held stocks:", error));
}

function fetchSoldStocks() {
    fetch("/api/sold_stocks")
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById("soldTable").getElementsByTagName("tbody")[0];
            tbody.innerHTML = ""; // Clear existing rows
            data.forEach(stock => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${stock["Transaction ID"]}</td>
                    <td>${stock["Stock Code"]}</td>
                    <td>${stock["Shares Sold"]}</td>
                    <td>${parseFloat(stock["Sell Price (per share)"]).toFixed(2)}</td>
                    <td>${parseFloat(stock["Avg Buy Price"]).toFixed(2)}</td>
                    <td>${parseFloat(stock["Total Buy Value"]).toFixed(2)}</td>
                    <td>${parseFloat(stock["Total Sell Value"]).toFixed(2)}</td>
                    <td>${parseFloat(stock["Profit/Loss"]).toFixed(2)}</td>
                    <td>${new Date(stock["Sell Date"]).toLocaleDateString()}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error("Error fetching sold stocks:", error));
}

