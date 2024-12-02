let isModified = false;

const apiUrl = "/api/transactionLogs"; // API endpoint for transaction logs

async function fetchTransactions() {
  try {
    const response = await fetch(apiUrl, {
      headers: {
        "x-api-key": "joel09-02-2024Adh",
      },
    });

    if (!response.ok) {
      // pass
    }

    const data = await response.json();
    if ("error" in data) {
      console.log("No data available:", data.error);
    } else {
      populateTable(data);
    }
  } catch (error) {
    alert("Failed to load transactions.");
    console.error(error);
  }
}

function populateTable(transactions) {
  const tbody = document
    .getElementById("editable-table")
    .querySelector("tbody");

  transactions.forEach((transaction) => {
    const row = document.createElement("tr");
    row.innerHTML = `
              <td>${transaction["Sl.No."]}</td>
              <td><input type="date" value="${formatDate(
                transaction.Date
              )}"></td>
              <td contenteditable="true">${transaction.Share}</td>
              <td contenteditable="true">${transaction.Symbol}</td>
              <td>
                  <select>
                      <option value="Buy" ${
                        transaction.Transaction === "Buy"
                          ? "selected"
                          : ""
                      }>Buy</option>
                      <option value="Sell" ${
                        transaction.Transaction === "Sell"
                          ? "selected"
                          : ""
                      }>Sell</option>
                  </select>
              </td>
              <td contenteditable="true">${transaction.Count}</td>
              <td contenteditable="true">${transaction.Price}</td>
              <td>${transaction["Total Amount"]}</td>
              <td>
                  <button class="action-btn" onclick="deleteRow(this)">Delete</button>
              </td>
          `;
    tbody.appendChild(row);
  });
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toISOString().split("T")[0]; // YYYY-MM-DD
}

function addRow() {
  const tbody = document
    .getElementById("editable-table")
    .querySelector("tbody");
  const lastRow = tbody.lastElementChild;
  const lastSlNo = lastRow
    ? parseInt(lastRow.querySelector("td:first-child").textContent)
    : 0;

  const row = document.createElement("tr");
  row.innerHTML = `
          <td>${lastSlNo + 1}</td>
          <td><input type="date"></td>
          <td contenteditable="true"></td>
          <td contenteditable="true"></td>
          <td>
              <select>
                  <option value="Buy">Buy</option>
                  <option value="Sell">Sell</option>
              </select>
          </td>
          <td contenteditable="true"></td>
          <td contenteditable="true"></td>
          <td>0</td>
          <td>
              <button class="action-btn" onclick="deleteRow(this)">Delete</button>
          </td>
      `;
  tbody.appendChild(row);
  markModified();
}

function deleteRow(button) {
  const row = button.parentElement.parentElement;
  row.remove();
  markModified();
}

function markModified() {
  isModified = true;
  document.getElementById("submit-btn").style.display = "inline-block";
  document.getElementById("reset-btn").style.display = "inline-block";
}

function calculateTotal(row) {
  const countCell = row.querySelector("td:nth-child(6)");
  const priceCell = row.querySelector("td:nth-child(7)");
  const totalCell = row.querySelector("td:nth-child(8)");

  const count = parseFloat(countCell.textContent) || 0;
  const price = parseFloat(priceCell.textContent) || 0;

  totalCell.textContent = (count * price).toFixed(2);
}

function handleCellChange(event) {
  const cell = event.target;
  const row = cell.parentElement;

  // If count or price changes, update the total amount
  if (cell.cellIndex === 5 || cell.cellIndex === 6) {
    calculateTotal(row);
  }

  markModified();
}

document
  .getElementById("editable-table")
  .addEventListener("input", handleCellChange);

async function resetChanges() {
  if (confirm("Are you sure you want to discard all changes?")) {
    const tbody = document
      .getElementById("editable-table")
      .querySelector("tbody");
    tbody.innerHTML = ""; // Clear the current table
    await fetchTransactions(); // Reload the original data
    isModified = false;
    document.getElementById("submit-btn").style.display = "none";
    document.getElementById("reset-btn").style.display = "none";
  }
}

async function submitChanges() {
  const rows = document.querySelectorAll("#editable-table tbody tr");
  const transactions = [];
  let hasErrors = false;
  const changesSummary = [];

  rows.forEach((row) => {
    const cells = row.querySelectorAll("td");
    const dateInput = cells[1].querySelector('input[type="date"]');
    const dateValue = dateInput.value;

    // Validate each field
    const share = cells[2].textContent.trim();
    const symbol = cells[3].textContent.trim();
    const transactionType = cells[4].querySelector("select").value;
    const count = parseFloat(cells[5].textContent.trim());
    const price = parseFloat(cells[6].textContent.trim());

    if (
      !dateValue ||
      !share ||
      !symbol ||
      !transactionType ||
      isNaN(count) ||
      isNaN(price) ||
      count <= 0 ||
      price <= 0
    ) {
      // Highlight the row with errors
      row.style.backgroundColor = "#ffcccc"; // Red background for error
      hasErrors = true;
    } else {
      // Reset row color if no error
      row.style.backgroundColor = "";
    }

    // Only add valid rows to the transactions list
    if (!hasErrors) {
      const formattedDate = formatDateForSubmit(dateValue);

      const transaction = {
        "Sl.No.": parseFloat(cells[0].textContent.trim(), 10),
        Date: formattedDate,
        Share: share,
        Symbol: symbol,
        Transaction: transactionType,
        Count: count,
        Price: price,
        "Total Amount": parseFloat(cells[7].textContent.trim()) || 0,
      };
      transactions.push(transaction);

      changesSummary.push(`
                  <p><strong>Row ${cells[0].textContent.trim()}:</strong> 
                  ${transaction.Share} (${transaction.Symbol}) - 
                  ${transaction.Transaction} ${transaction.Count} at ${
        transaction.Price
      }</p>
              `);
    }
  });

  if (hasErrors) {
    setTimeout(() => {
      alert("Please correct the highlighted rows before submitting.");
    }, 0);
    return; // Stop submission
  }

  // Show confirmation modal with changes summary
  document.getElementById("confirm-sub").style.display = "inline-block";
  document.getElementById("cancel-sub").style.display = "inline-block";
  document.getElementById("changes-summary").innerHTML =
    changesSummary.join("");
  document.getElementById("confirmation-modal").style.display = "flex";

  // Store transactions globally for later confirmation
  window.pendingTransactions = transactions;
}

function closeModal() {
    const modal = document.getElementById('cancel-sub');
    modal.classList.add('hidden');
  }

  function cancelModal(){
    document.getElementById("confirmation-modal").style.display = "none";
  }
  
  document.getElementById('cancel-sub').addEventListener('click', cancelModal);
  
  async function confirmSubmission() {
    const loadingModal = document.getElementById("loading-modal");
    const confirmationModal = document.getElementById("confirmation-modal");
  
    confirmationModal.style.display = "none";
    loadingModal.style.display = "flex";
  
    try {
      const response = await fetch("/api/submit_transactions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": "joel09-02-2024Adh",
        },
        body: JSON.stringify(window.pendingTransactions),
      });
  
      if (response.ok) {
        alert("Changes submitted successfully!");
        loadingModal.style.display = "none"; 
        isModified = false;
        document.getElementById("submit-btn").style.display = "none";
        document.getElementById("reset-btn").style.display = "none";
      } else {
        loadingModal.style.display = "none"; 
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      loadingModal.style.display = "none";
      console.error("Failed to submit transactions:", error);
      alert("Failed to submit changes. Please try again.");
    }
  
    closeModal(); // Close the modal after confirmation
    location.reload();
  }
  

// Utility function to format date to dd-mm-yyyy
function formatDateForSubmit(dateStr) {
  const date = new Date(dateStr);
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}-${month}-${year}`;
}

// Fetch transactions on page load
fetchTransactions();