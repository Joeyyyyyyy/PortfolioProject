/**
 * Initializes event listeners for DOMContentLoaded.
 * Calls the functions to fetch realized profit, held stocks, and sold stocks data.
 */
document.addEventListener("DOMContentLoaded", function () {
    try {
        fetchPortfolioData();
    } catch (error) {
        console.error("Error during initialization:", error);
    }
});

const API_KEY = "joel09-02-2024Adh";

/**
 * Fetches the portfolio data from the API and updates the relevant sections of the page.
 */
async function fetchPortfolioData() {
    try{
        const response=await fetch("/api/portfolio_data", {
            headers: {
                "x-api-key": API_KEY
            }
        });

        if (!response.ok) throw new Error("Failed to fetch portfolio data");

        const data = await response.json();

        updateRealizedProfit(data.realized_profit);
        updateUnrealizedProfit(data.unrealized_profit);
        updateOneDayReturns(data.todays_returns);
        updateHeldStocks(data.held_stocks);
        updateSoldStocks(data.sold_stocks);

        // Schedule the next fetch after completion
        setTimeout(fetchPortfolioData, 3000);
    } catch(error) {
        console.error("Error fetching portfolio data:", error);
        location.reload();
    }
}

/**
 * Updates the realized profit section.
 * @param {number} profit - Realized profit value.
 */
function updateRealizedProfit(profit) {
    document.getElementById("realized-profit").textContent = `${profit.toFixed(2)}`;
}

/**
 * Updates the unrealized profit section.
 * @param {number} profit - Unrealized profit value.
 */
function updateUnrealizedProfit(profit) {
    document.getElementById("unrealized-profit").textContent = `${profit.toFixed(2)}`;
}

/**
 * Updates the one day returns section.
 * @param {number} returns - One day returns value.
 */
function updateOneDayReturns(returns) {
    document.getElementById("todays-returns").textContent = `${returns.toFixed(2)}`;
}

/**
 * Updates the held stocks table.
 * @param {Array} stocks - List of held stocks.
 */
function updateHeldStocks(stocks) {
    const tbody = document.getElementById("portfolio-table").getElementsByTagName("tbody")[0];
    tbody.innerHTML = ""; // Clear existing rows
    stocks.forEach(stock => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${stock.Share}</td>
            <td>${stock["Net Shares"]}</td>
            <td>${stock["Avg Buying Price"].toFixed(2)}</td>
            <td>${stock["Current Price"].toFixed(2)}</td>
            <td>${stock["Potential Sale Value"].toFixed(2)}</td>
            <td>${stock["Price Change"]}</td>
            <td>${stock["Percentage Change"]}</td>
            <td>${stock["Potential Sale Profit/Loss"]}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Updates the sold stocks table.
 * @param {Array} stocks - List of sold stocks.
 */
function updateSoldStocks(stocks) {
    const tbody = document.getElementById("soldTable").getElementsByTagName("tbody")[0];
    tbody.innerHTML = ""; // Clear existing rows
    stocks.forEach(stock => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${stock["Transaction ID"]}</td>
            <td>${new Date(stock["Sell Date"]).toLocaleDateString('en-GB')}</td>
            <td>${stock["Stock Code"]}</td>
            <td>${stock["Shares Sold"]}</td>
            <td>${stock["Sell Price (per share)"].toFixed(2)}</td>
            <td>${stock["Avg Buy Price"].toFixed(2)}</td>
            <td>${stock["Total Buy Value"].toFixed(2)}</td>
            <td>${stock["Total Sell Value"].toFixed(2)}</td>
            <td>${stock["Profit/Loss"]}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Filters the table based on the search input.
 */
function searchTable() {
    const searchValue = document.getElementById("search-input").value.toLowerCase();

    const rows = document.querySelectorAll("#portfolio-table tbody tr");

    rows.forEach(row => {
        const shareCell = row.cells[0].textContent.toLowerCase();

        if (shareCell.includes(searchValue)) {
            row.style.display = ""; 
        } else {
            row.style.display = "none"; 
        }
    });
}