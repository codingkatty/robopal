function openModal() {
  document.getElementById("signupModal").classList.add("show");
}

function closeModal() {
  document.getElementById("signupModal").classList.remove("show");
}

document.getElementById("welcomeForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;

  try {
    const response = await fetch("https://robopal-c4dw.onrender.com/welcome", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        to_email: email,
        subject: `Welcome to RoboPal, ${name}!`,
        message: `Hi ${name},\n\nOMG did you just say you want to become my penpal!? So nice to have you here!! Feel free to email me anytime for a reply!\n\nYour favourite penpal,\nSarah (AI)`,
      }),
    });

    if (response.ok) {
      closeModal();
      const message = document.getElementById("message");
      message.classList.add("show");
      setTimeout(() => message.classList.remove("show"), 3000);
      e.target.reset();
    } else {
      throw new Error("Failed to send email");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Failed to send welcome email. Please try again.");
  }
});
