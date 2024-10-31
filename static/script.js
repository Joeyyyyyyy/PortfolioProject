// static/script.js
document.addEventListener("DOMContentLoaded", function () {
    fetchRealizedProfit();
    fetchHeldStocks();
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

      // Scroll to the table section 
      document.addEventListener('DOMContentLoaded', function() {
        const getStartedButton = document.querySelector('#button1');
        const servicesLink = document.querySelector('a[href="#portfolio-section"]');
    
        getStartedButton.addEventListener('click', function(event) {
            event.preventDefault();
            const targetSection = document.querySelector('#portfolio-section');
    
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
        });
    
        servicesLink.addEventListener('click', function(event) {
            event.preventDefault();
            const targetSection = document.querySelector('#portfolio-section');
    
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
        });
    });
