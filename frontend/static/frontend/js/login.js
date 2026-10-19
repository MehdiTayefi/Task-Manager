import { signIn } from "./auth.js?v=5";
const form = document.querySelector("#login-form");
const message = document.querySelector("#form-message");
const button = form.querySelector('[type="submit"]');
function showError(text) {
    message.textContent = text; message.dataset.state = "error"; message.focus();
}
form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    message.textContent = "";
    button.disabled = true; button.textContent = "Signing in…";
    try {
        await signIn(form.elements.username.value, form.elements.password.value);
        form.elements.password.value = "";
        window.location.assign(document.body.dataset.tasksUrl);
    } catch (error) {
        showError(error instanceof TypeError ? "Unable to reach the server. Check your connection and try again." : error.message);
    } finally {
        button.disabled = false; button.textContent = "Sign in →";
    }
});

if (new URLSearchParams(window.location.search).get("deleted") === "1") {
    message.textContent = "Your account and tasks have been deleted. All sessions have been revoked.";
    message.dataset.state = "success";
}
