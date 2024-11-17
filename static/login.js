// Toggle password visibility
function togglePassword() {
    const passwordField = document.getElementById("password");
    const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
    passwordField.setAttribute("type", type);
  }  

document.addEventListener("DOMContentLoaded", function () {
  const serverData = document.getElementById("server-data");
  const loginFailed = JSON.parse(serverData.dataset.loginFailed); // Parse the flag from the data attribute

    if (loginFailed) {
        const warningText = document.getElementById("invalid-login");
        warningText.style.display = "block"; // Show the warning message
        warningText.style.color = "red"; // Set color to red
    }
});