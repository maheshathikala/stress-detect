// 🔐 Hidden Admin credentials
const ADMIN_USERNAME = "sanjay";
const ADMIN_SECRET = "jalsa2008";

// DOM references
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const loginMessage = document.getElementById("loginMessage");
const registerMessage = document.getElementById("registerMessage");
const tabButtons = document.querySelectorAll(".tab-btn");

// Utility: show message
function showMessage(element, message, type) {
    element.textContent = message;
    element.className = "message " + type;
    element.style.display = "block";
}

// 🔄 Switch between Login & Register forms
function switchTab(tab) {
    // remove active state from all
    tabButtons.forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".auth-form").forEach(form => form.classList.remove("active"));

    // activate the chosen one
    if (tab === "login") {
        document.querySelector("#loginForm").classList.add("active");
        tabButtons[0].classList.add("active");
    } else {
        document.querySelector("#registerForm").classList.add("active");
        tabButtons[1].classList.add("active");
    }
}

// Login form submission
loginForm.addEventListener("submit", async function(e) {
    e.preventDefault();

    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;

    if (!username || !password) {
        showMessage(loginMessage, "Please fill in all fields", "error");
        return;
    }

    // ✅ Check for admin login
   

    // Normal user login
    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        
        });

        const data = await response.json();

        if (data.success) {
  showMessage(loginMessage, "Login successful! Redirecting...", "success");
  setTimeout(() => {
    if (data.role === "admin") {
      window.location.href = "/dashboard"; // Flask renders admin.html
    } else {
      window.location.href = "/dashboard"; // Flask renders user dashboard
    }
  }, 1500);
} else {
  showMessage(loginMessage, data.message || "Login failed", "error");
}



  } catch (error) {
    console.error("Login error:", error);
    showMessage(loginMessage, "Connection error. Please try again.", "error");
  }
});


// Register form submission
registerForm.addEventListener("submit", async function(e) {
    e.preventDefault();

    const username = document.getElementById("registerUsername").value;
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;

    if (!username || !email || !password) {
        showMessage(registerMessage, "Please fill in all fields", "error");
        return;
    }

    try {
        const response = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();
         
        
        if (data.success) {
            showMessage(registerMessage, "Registration successful! Please login.", "success");
            switchTab("login"); // auto switch back to login
        } else {
            showMessage(registerMessage, data.message || "Registration failed", "error");
        }
    } catch (error) {
        console.error("Registration error:", error);
        showMessage(registerMessage, "Connection error. Please try again.", "error");
    }
});
