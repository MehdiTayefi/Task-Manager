import { signIn } from "./auth.js?v=6";
import { registrationErrors } from "./messages.js?v=6";
const form = document.querySelector("#register-form");
const message = document.querySelector("#form-message");
const submitButton = form.querySelector('button[type="submit"]');
function showMessage(text, state) {message.textContent = text; message.dataset.state = state; if(text) message.focus();}
form.addEventListener("submit", async (event) => {
    event.preventDefault(); if (submitButton.disabled) return;
    showMessage("", "");
    const payload = Object.fromEntries(new FormData(form));
    if (/\s/u.test(payload.password)) {showMessage("رمز عبور نباید فاصله، تب یا خط جدید داشته باشد.", "error"); return;}
    if (payload.password !== payload.password_confirm) {showMessage("رمز عبور و تکرارش یکسان نیستند.", "error"); return;}
    submitButton.disabled = true; submitButton.textContent = "در حال ساخت حساب…";
    try {
        const response = await fetch(form.action, {
            method:"POST", headers:{"Content-Type":"application/json", "Accept":"application/json"}, body:JSON.stringify(payload),
        });
        if (response.status === 201) {
            try {await signIn(payload.username,payload.password);form.reset();window.location.assign(document.body.dataset.tasksUrl);}
            catch {form.reset();showMessage("حسابت ساخته شد، ولی ورود خودکار انجام نشد. از لینک «وارد شو» استفاده کن.", "error");}
        } else if (response.status === 400) {showMessage(registrationErrors(await response.json()), "error");}
        else {showMessage("ساخت حساب انجام نشد. دوباره تلاش کن.", "error");}
    } catch {showMessage("ارتباط با سرور برقرار نشد یا پاسخ معتبر نبود. دوباره تلاش کن.", "error");}
    finally {submitButton.disabled = false;submitButton.textContent = "ساخت حساب و شروع ←";}
});
