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
    /*async function fetchMarketStatus() {
        try {
            const response = await fetch("/api/market_status", {
                headers: {
                    "x-api-key": API_KEY
                }
            });

            if (!response.ok) throw new Error("Failed to fetch market status");

            const data = await response.json();
            return data.market_status; // Assuming this is true/false
        } catch (error) {
            console.error("Error fetching market status: ", error);
            return false; // Default to closed on error
        }
    }

    const marketStatus = fetchMarketStatus();
    console.log(marketStatus)*/

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

        document.getElementById('loader-container').style.display = 'none';
        document.getElementById('loader-container2').style.display = 'none';
        document.getElementById('portfolio-table').classList.remove('hidden');
        document.getElementById('soldTable').classList.remove('hidden');

        console.log("Portfolio data fetched successfully.");
    } catch (error) {
        console.error("Error fetching portfolio data:", error);
    }
    searchTable();
}

function updateRealizedProfit(profit) {
    const el = document.getElementById("realized-profit");

    // Remove both possible text colors first, to keep things clean
    el.classList.remove("text-[#15803D]", "text-red-500");

    // Add the correct color class based on sign
    if (profit < 0) {
        el.classList.add("text-red-500");
    } else {
        el.classList.add("text-[#15803D]");
    }

    // Set the final text (and optionally format it)
    el.textContent = profit.toFixed(2);
}

function updateUnrealizedProfit(profit) {
    const el = document.getElementById("unrealized-profit");

    // Remove both possible text colors first
    el.classList.remove("text-[#15803D]", "text-red-500");

    // Add color class
    if (profit < 0) {
        el.classList.add("text-red-500");
    } else {
        el.classList.add("text-[#15803D]");
    }

    el.textContent = profit.toFixed(2);
}

function updateOneDayReturns(returns) {
    const el = document.getElementById("todays-returns");

    // Remove both possible text colors first
    el.classList.remove("text-[#15803D]", "text-red-500");

    // Add color class
    if (returns < 0) {
        el.classList.add("text-red-500");
    } else {
        el.classList.add("text-[#15803D]");
    }

    el.textContent = returns.toFixed(2);
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

        const createStyledCell = (value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            cell.style.color = value.includes('+') ? "#66FF66" : "#FF6666"; // Set color based on value
            return cell;
        };

        row.appendChild(document.createElement("td")).textContent = stock.Share;
        row.appendChild(document.createElement("td")).textContent = stock["Net Shares"];
        row.appendChild(document.createElement("td")).textContent = stock["Avg Buying Price"].toFixed(2);
        row.appendChild(document.createElement("td")).textContent = stock["Current Price"].toFixed(2);
        row.appendChild(document.createElement("td")).textContent = stock["Potential Sale Value"].toFixed(2);
        row.appendChild(createStyledCell(stock["Price Change"]));
        row.appendChild(createStyledCell(stock["Percentage Change"]));
        row.appendChild(createStyledCell(stock["Potential Sale Profit/Loss"]));

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
            <td style="color: ${stock["Profit/Loss"].includes('+') ? '#66FF66' : '#FF6666'};">${stock["Profit/Loss"]}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Filters both tables based on the search input.
 */
function searchTable() {
    const searchValue = document.getElementById("search-input").value.toLowerCase();

    // Table 1: Portfolio Table (Filter by Share column)
    const portfolioRows = document.querySelectorAll("#portfolio-table tbody tr");
    portfolioRows.forEach(row => {
        const shareCell = row.cells[0] ? row.cells[0].textContent.toLowerCase() : "";
        row.style.display = shareCell.includes(searchValue) ? "" : "none";
    });

    const searchValue2 = document.getElementById("search-input-2").value.toLowerCase();

    // Table 2: Sold Table (Filter by Stock Code column)
    const stockRows = document.querySelectorAll("#soldTable tbody tr");
    stockRows.forEach(row => {
        const stockCodeCell = row.cells[2] ? row.cells[2].textContent.toLowerCase() : "";
        row.style.display = stockCodeCell.includes(searchValue2) ? "" : "none";
    });
}

