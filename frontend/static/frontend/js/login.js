import { signIn } from "./auth.js?v=6";
const form = document.querySelector("#login-form");
const message = document.querySelector("#form-message");
const button = form.querySelector('[type="submit"]');
function showError(text) {message.textContent = text; message.dataset.state = "error"; message.focus();}
form.addEventListener("submit", async (event) => {
    event.preventDefault(); if (button.disabled) return;
    message.textContent = ""; button.disabled = true; button.textContent = "در حال ورود…";
    try {
        await signIn(form.elements.username.value, form.elements.password.value);
        form.elements.password.value = "";
        window.location.assign(document.body.dataset.tasksUrl);
    } catch (error) {
        showError(error instanceof TypeError ? "ارتباط با سرور برقرار نشد. اتصال اینترنت را بررسی کن." : error.message);
    } finally {button.disabled = false; button.textContent = "ورود به حساب ←";}
});
if (new URLSearchParams(window.location.search).get("deleted") === "1") {
    message.textContent = "حساب و کارهایت حذف و تمام ورودهای قبلی باطل شدند."; message.dataset.state = "success";
}
