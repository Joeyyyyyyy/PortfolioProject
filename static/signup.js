// Form validation and password confirmation
document.getElementById("signup-form").addEventListener("submit", function (event) {
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirm-password").value;

  if (password !== confirmPassword) {
    event.preventDefault();
    alert("Passwords do not match!");
  }
});

// Add a fade-in effect when the page loads
document.addEventListener("DOMContentLoaded", () => {
  document.body.style.opacity = 0;
  let fadeEffect = setInterval(() => {
    if (document.body.style.opacity < 1) {
      document.body.style.opacity = parseFloat(document.body.style.opacity) + 0.1;
    } else {
      clearInterval(fadeEffect);
    }
  }, 50);
});


function validateForm() {
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirm-password').value;

  if (password !== confirmPassword) {
    alert("Passwords do not match!");
    return false;
  }
  return true;
}

function togglePasswordVisibility(id) {
  const passwordField = document.getElementById(id);
  const eyeIcon = document.getElementById(id + '-eye-icon');

  if (passwordField.type === "password") {
    passwordField.type = "text";
    eyeIcon.classList.remove("fa-eye-slash");
    eyeIcon.classList.add("fa-eye");
  } else {
    passwordField.type = "password";
    eyeIcon.classList.remove("fa-eye");
    eyeIcon.classList.add("fa-eye-slash");
  }
}