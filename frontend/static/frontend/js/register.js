import { signIn } from "./auth.js?v=5";

const form = document.querySelector("#register-form");
const message = document.querySelector("#form-message");
const submitButton = form.querySelector('button[type="submit"]');
const fieldLabels = {
    username: "Username", email: "Email address", password: "Password",
    password_confirm: "Confirm password", non_field_errors: "Error", detail: "Error",
};

function showMessage(text, state) {
    message.textContent = text;
    message.dataset.state = state;
    if (text) message.focus();
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitButton.disabled) return;
    showMessage("", "");
    const payload = Object.fromEntries(new FormData(form));
    if (payload.password !== payload.password_confirm) {
        showMessage("Passwords do not match.", "error");
        return;
    }
    submitButton.disabled = true;
    submitButton.textContent = "Creating account…";
    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            body: JSON.stringify(payload),
        });
        if (response.status === 201) {
            try {
                await signIn(payload.username, payload.password);
                form.reset();
                window.location.assign(document.body.dataset.tasksUrl);
            } catch {
                form.reset();
                showMessage("Your account was created, but automatic sign-in failed. Please use the Sign in link below.", "error");
            }
        } else if (response.status === 400) {
            const errors = await response.json();
            const lines = Object.entries(errors).map(([field, values]) => {
                const label = fieldLabels[field] || field;
                const text = Array.isArray(values) ? values.join(" ") : String(values);
                return `${label}: ${text}`;
            });
            showMessage(lines.join("\n"), "error");
        } else {
            showMessage("We couldn’t create your account. Please try again.", "error");
        }
    } catch {
        showMessage("Unable to reach the server. Check your connection and try again.", "error");
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Create account";
    }
});

