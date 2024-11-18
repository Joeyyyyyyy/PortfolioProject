// API Endpoint for transaction logs
const API_URL = "http://localhost:5000/api/transactions"; // Replace with the correct endpoint

document.addEventListener("DOMContentLoaded", () => {
    const loadingElement = document.getElementById("loading");
    const tableBody = document.querySelector("#transaction-table tbody");

    // Function to fetch and display data
    async function fetchTransactionLogs() {
        loadingElement.classList.remove("hidden");
        try {
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error("Failed to fetch data");
            
            const data = await response.json();
            populateTable(data);
        } catch (error) {
            console.error("Error:", error);
            alert("Failed to load transaction data.");
        } finally {
            loadingElement.classList.add("hidden");
        }
    }

    // Function to populate table with data
    function populateTable(data) {
        tableBody.innerHTML = ""; // Clear existing rows
        data.forEach(transaction => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${transaction.id}</td>
                <td>${transaction.user}</td>
                <td>${transaction.stock}</td>
                <td>${transaction.type}</td>
                <td>${transaction.quantity}</td>
                <td>${new Date(transaction.date).toLocaleString()}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Load data on page load
    fetchTransactionLogs();
});
