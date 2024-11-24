// Toggle Password Visibility
function togglePassword() {
    const passwordField = document.getElementById("password");
    const confirmPasswordField = document.getElementById("confirm-password");
    const passwordType = passwordField.type === "password" ? "text" : "password";
    passwordField.type = passwordType;
    confirmPasswordField.type = passwordType;
  }
  
  // Form Validation and AJAX Submission
  document.getElementById("signup-form").addEventListener("submit", async function (e) {
    e.preventDefault();
  
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm-password").value;
  
    if (!username || !email || !password || !confirmPassword) {
      alert("All fields are required!");
      return;
    }
  
    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
  
    // Prepare the data to send
    const formData = {
      username,
      email,
      password,
    };
  
    try {
      // Send the POST request to the server
      const response = await fetch("/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          'x-api-key': 'joel09-02-2024Adh'
        },
        body: JSON.stringify(formData),
      });
  
      const result = await response.json();
  
      if (response.ok) {
        alert(result.message || "Signup successful! Please log in.");
        window.location.href = "/login"; // Redirect to login page
      } else {
        alert(result.error || "Signup failed. Please try again.");
      }
    } catch (error) {
      console.error("Error during signup:", error);
      alert("An error occurred. Please try again.");
    }
  });
  