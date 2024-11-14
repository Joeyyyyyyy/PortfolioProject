// static/script.js

/**
 * Initializes event listeners for DOMContentLoaded.
 * Calls the functions to fetch realized profit, held stocks, and sold stocks data.
 */
document.addEventListener("DOMContentLoaded", function () {
    fetchRealizedProfit();
    fetchHeldStocks();
    fetchSoldStocks();
});

// Define the API key to be included in headers
/** @constant {string} API_KEY - API key for authorization in request headers */
const API_KEY = "joel09-02-2024Adh";

/**
 * Fetches the realized profit data from the API and updates the page with the profit value.
 * 
 * @function fetchRealizedProfit
 * @throws {Error} Throws an error if the API request fails.
 */
function fetchRealizedProfit() {
    fetch("/api/profit", {
        headers: {
            "x-api-key": API_KEY
        }
    })
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch realized profit");
            return response.json();
        })
        .then(data => {
            document.getElementById("realized-profit").textContent = `${data.realized_profit.toFixed(2)}`;
        })
        .catch(error => console.error("Error fetching realized profit:", error));
}

/**
 * Fetches the held stocks data from the API and populates the "portfolio-table" table
 * with stock information including share name, symbol, net shares, current price, potential sale value,
 * and potential sale profit/loss.
 * 
 * @function fetchHeldStocks
 * @throws {Error} Throws an error if the API request fails.
 */
function fetchHeldStocks() {
    fetch("/api/held_stocks", {
        headers: {
            "x-api-key": API_KEY
        }
    })
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch held stocks");
            return response.json();
        })
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

/**
 * Fetches the sold stocks data from the API and populates the "soldTable" table
 * with transaction details, including transaction ID, sell date, stock code, shares sold,
 * sell price, average buy price, total buy value, total sell value, and profit/loss.
 * 
 * @function fetchSoldStocks
 * @throws {Error} Throws an error if the API request fails.
 */
function fetchSoldStocks() {
    fetch("/api/sold_stocks", {
        headers: {
            "x-api-key": API_KEY
        }
    })
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch sold stocks");
            return response.json();
        })
        .then(data => {
            const tbody = document.getElementById("soldTable").getElementsByTagName("tbody")[0];
            tbody.innerHTML = ""; // Clear existing rows
            data.forEach(stock => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${stock["Transaction ID"]}</td>
                    <td>${new Date(stock["Sell Date"]).toLocaleDateString()}</td>
                    <td>${stock["Stock Code"]}</td>
                    <td>${stock["Shares Sold"]}</td>
                    <td>${stock["Sell Price (per share)"].toFixed(2)}</td>
                    <td>${stock["Avg Buy Price"].toFixed(2)}</td>
                    <td>${stock["Total Buy Value"].toFixed(2)}</td>
                    <td>${stock["Total Sell Value"].toFixed(2)}</td>
                    <td>${stock["Profit/Loss"].toFixed(2)}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error("Error fetching sold stocks:", error));
}
