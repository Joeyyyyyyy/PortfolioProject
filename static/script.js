/**
 * Initializes event listeners for DOMContentLoaded.
 * Calls the functions to fetch realized profit, held stocks, and sold stocks data during market hours.
 */
document.addEventListener("DOMContentLoaded", function () {
    try {
        fetchPortfolioData(); // Always fetch data once when the page loads
        checkMarketStatus(); // Start checking market status periodically
    } catch (error) {
        console.error("Error during initialization:", error);
    }
});

const API_KEY = "joel09-02-2024Adh";
let periodicFetchActive = false; // Flag to track if periodic fetching is active

/**
 * Checks if the market is open (9 AM to 4 PM).
 * @returns {boolean} True if market is open, otherwise false.
 */
function isMarketOpen() {
    const now = new Date();
    const start = new Date();
    const startHour = 9; // 9 AM
    const endHour = 16; // 4 PM

    return now.getHours() >= startHour && now.getHours() < endHour;
}

/**
 * Periodically checks the market status every 5 minutes.
 * If the market is open, starts the portfolio data refresh functionality.
 */
function checkMarketStatus() {
    const marketOpen = isMarketOpen();

    if (marketOpen && !periodicFetchActive) {
        periodicFetchActive = true;
        startPeriodicFetch();
    } else if (!marketOpen && periodicFetchActive) {
        periodicFetchActive = false;
    } 

    // Recheck market status every 1 minute
    setTimeout(checkMarketStatus, 1 * 60 * 1000); // 1 minute
}

/**
 * Starts periodic fetching of portfolio data.
 */
function startPeriodicFetch() {
    const periodicFetch = async () => {
        if (!isMarketOpen()) {
            console.log("Market has closed during periodic fetch. Stopping further execution.");
            periodicFetchActive = false;
            return; // Stop fetching data if the market is closed
        }

        await fetchPortfolioData();
        if (periodicFetchActive) {
            setTimeout(periodicFetch, 3000); // Schedule next fetch
        }
    };

    periodicFetch(); // Start the first periodic fetch
}

/**
 * Fetches the portfolio data from the API and updates the relevant sections of the page.
 */
async function fetchPortfolioData() {
    try {
        const response = await fetch("/api/portfolio_data", {
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

        console.log("Portfolio data fetched successfully.");
    } catch (error) {
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