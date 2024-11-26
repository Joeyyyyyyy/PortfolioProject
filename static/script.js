/**
 * Initializes event listeners and starts the data-fetching process.
 * - Fetches and updates data immediately on page load.
 * - Periodically updates data every 3 seconds using `setInterval`.
 * - Prevents overlapping fetch operations by ensuring only one fetch runs at a time.
 * - Reloads the page in case of fatal errors during the data-fetch process.
 */
document.addEventListener("DOMContentLoaded", async function () {
    let isFetching = false; // Flag to check if a fetch operation is in progress
    let refreshInterval = null; // Variable to store the interval ID
    const marketStartTime = { hour: 9, minute: 0 }; // Market opens at 9:30 AM
    const marketEndTime = { hour: 16, minute: 0 }; // Market closes at 4:00 PM

    /**
     * Checks if the current time is within market hours.
     * @returns {boolean} - True if within market hours, false otherwise.
     */
    function isMarketOpen() {
        const now = new Date();
        const start = new Date();
        start.setHours(marketStartTime.hour, marketStartTime.minute, 0, 0);

        const end = new Date();
        end.setHours(marketEndTime.hour, marketEndTime.minute, 0, 0);
        /**if(now >= start && now <= end)
            console.log("Market is open")
        else
            console.log("Market is closed")*/

        return now >= start && now <= end;
    }

    /**
     * Starts the periodic refresh loop if the market is open.
     */
    function startRefreshLoop() {
        if (refreshInterval) return; // Prevent multiple intervals
        refreshInterval = setInterval(fetchAndUpdateData, 3000);
        console.log("Started refresh loop");
    }

    /**
     * Stops the periodic refresh loop.
     */
    function stopRefreshLoop() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
            console.log("Stopped refresh loop");
        }
    }

    /**
     * Toggles the refresh mechanism based on market hours.
     */
    function toggleRefreshBasedOnMarketHours() {
        if (isMarketOpen()) {
            startRefreshLoop();
        } else {
            stopRefreshLoop();
        }
    }

    /**
     * Fetches data and updates the UI, ensuring no overlap of fetch operations.
     */
    async function fetchAndUpdateData() {
        if (isFetching) return; // Exit if a fetch operation is already running
        isFetching = true;

        try {
            await fetchRealizedProfit();
            
            // Wait for all asynchronous functions to complete
            await Promise.all([
                fetchUnrealizedProfit(),
                fetchOneDayReturns(),
                fetchHeldStocks(),
                fetchSoldStocks()
            ]);
        } catch (error) {
            console.error("Error during data fetch and update:", error);
            location.reload(); // Reload the page on failure
        } finally {
            isFetching = false; // Reset the flag after the fetch operation is complete
        }
    }

    // Initial fetch and market hours check
    await fetchAndUpdateData();
    toggleRefreshBasedOnMarketHours();

    // Recheck market status every 30s
    setInterval(toggleRefreshBasedOnMarketHours, 0.5 * 60 * 1000);
});


// Define the API key to be included in headers
/** @constant {string} API_KEY - API key for authorization in request headers */
const API_KEY = "joel09-02-2024Adh";

/**
 * Fetches the realized profit data from the API and updates the DOM.
 * - The data is fetched from `/api/profit`.
 * - The "realized-profit" element is updated with the formatted value.
 * 
 * @function fetchRealizedProfit
 * @throws {Error} Throws an error if the API request fails or the response is invalid.
 */

async function fetchRealizedProfit() {
        const response = await fetch("/api/profit", {
            headers: {
                "x-api-key": API_KEY
            }
        });
        if (!response.ok) throw new Error("Failed to fetch realized profit");
        const data = await response.json();
        document.getElementById("realized-profit").textContent = `${data.realized_profit.toFixed(2)}`;

}

/**
 * Fetches the unrealized profit data from the API and updates the page with the profit value.
 * 
 * @function fetchUnrealizedProfit
 * @throws {Error} Throws an error if the API request fails.
 */
function fetchUnrealizedProfit() {
    fetch("/api/unrealisedprofit", {
        headers: {
            "x-api-key": API_KEY
        }
    })
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch unrealized profit");
            return response.json();
        })
        .then(data => {
            document.getElementById("unrealized-profit").textContent = `${data.unrealized_profit.toFixed(2)}`;
        })
        .catch(error => console.error("Error fetching unrealized profit:", error));
}

/**
 * Fetches the one day returns data from the API and updates the page with the value.
 * 
 * @function fetchOneDayReturns
 * @throws {Error} Throws an error if the API request fails.
 */
function fetchOneDayReturns() {
    fetch("/api/onedreturns", {
        headers: {
            "x-api-key": API_KEY
        }
    })
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch today's returns");
            return response.json();
        })
        .then(data => {
            document.getElementById("todays-returns").textContent = `${data.todays_returns.toFixed(2)}`;
        })
        .catch(error => console.error("Error fetching today's returns:", error));
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
async function fetchSoldStocks() {
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
        })
        .catch(error => console.error("Error fetching sold stocks:", error));
}

/**
 * Filters the table based on the search input.
 */
function searchTable() {
    const searchValue = document.getElementById("search-input").value.toLowerCase();

    const rows = document.querySelectorAll("#portfolio-table tbody tr");

    rows.forEach(row => {
        const shareCell = row.cells[0].textContent.toLowerCase();
        const symbolCell = row.cells[1].textContent.toLowerCase();

        if (shareCell.includes(searchValue) || symbolCell.includes(searchValue)) {
            row.style.display = ""; 
        } else {
            row.style.display = "none"; 
        }
    });
}

