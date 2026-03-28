document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authStatus = document.getElementById("auth-status");
  const authPill = document.getElementById("auth-pill");
  const authContainer = document.getElementById("auth-container");
  const authToggleBtn = document.getElementById("auth-toggle-btn");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const logoutBtn = document.getElementById("logout-btn");
  const showRegisterBtn = document.getElementById("show-register-btn");
  const showLoginBtn = document.getElementById("show-login-btn");

  let currentUser = null;

  function canManageRegistrations() {
    if (!currentUser || !currentUser.authenticated) {
      return false;
    }
    return ["admin", "faculty", "coordinator"].includes(currentUser.role);
  }

  function updateAuthUi() {
    if (!currentUser || !currentUser.authenticated) {
      authPill.textContent = "Not signed in";
      authPill.className = "auth-pill";
      authStatus.textContent = "Sign in as admin/faculty/coordinator to register or unregister students.";
      authStatus.className = "info";
      authToggleBtn.textContent = "Login";
      logoutBtn.classList.add("hidden");
      signupForm.querySelector("button[type='submit']").disabled = true;
      return;
    }

    authPill.textContent = `${currentUser.username} (${currentUser.role})`;
    authPill.className = "auth-pill auth-pill--active";
    authStatus.textContent = `Signed in as ${currentUser.username} (${currentUser.role})`;
    authStatus.className = "success";
    authToggleBtn.textContent = "Account";
    logoutBtn.classList.remove("hidden");
    signupForm.querySelector("button[type='submit']").disabled = !canManageRegistrations();

    if (!canManageRegistrations()) {
      authStatus.textContent += ". This role cannot register/unregister students.";
      authStatus.className = "info";
    }
  }

  function showLoginForm() {
    loginForm.classList.remove("hidden");
    registerForm.classList.add("hidden");
  }

  function showRegisterForm() {
    registerForm.classList.remove("hidden");
    loginForm.classList.add("hidden");
  }

  async function loadCurrentUser() {
    try {
      const response = await fetch("/auth/me");
      currentUser = await response.json();
      updateAuthUi();
    } catch (error) {
      currentUser = { authenticated: false };
      updateAuthUi();
    }
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}" ${canManageRegistrations() ? "" : "disabled title='Requires admin/faculty/coordinator login'"}>❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    if (!canManageRegistrations()) {
      messageDiv.textContent = "You must be logged in as admin, faculty, or coordinator.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      return;
    }

    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!canManageRegistrations()) {
      messageDiv.textContent = "You must be logged in as admin, faculty, or coordinator.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      return;
    }

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Login failed");
      }

      messageDiv.textContent = result.message;
      messageDiv.className = "success";
      messageDiv.classList.remove("hidden");
      loginForm.reset();
      await loadCurrentUser();
      await fetchActivities();
    } catch (error) {
      messageDiv.textContent = error.message || "Login failed";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
    }
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("register-username").value;
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;

    try {
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Registration failed");
      }

      messageDiv.textContent = `${result.message}. You can now log in.`;
      messageDiv.className = "success";
      messageDiv.classList.remove("hidden");
      registerForm.reset();
    } catch (error) {
      messageDiv.textContent = error.message || "Registration failed";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
    }
  });

  logoutBtn.addEventListener("click", async () => {
    await fetch("/auth/logout", { method: "POST" });
    await loadCurrentUser();
    await fetchActivities();
    messageDiv.textContent = "Logged out successfully";
    messageDiv.className = "success";
    messageDiv.classList.remove("hidden");
  });

  authToggleBtn.addEventListener("click", () => {
    authContainer.classList.toggle("hidden");
  });

  showRegisterBtn.addEventListener("click", showRegisterForm);
  showLoginBtn.addEventListener("click", showLoginForm);

  // Initialize app
  loadCurrentUser().then(fetchActivities);
});
