import { authFetch, readJSON, finishAccountDeletion } from "./auth.js?v=7";
const $ = (selector) => document.querySelector(selector);
const message = $("#form-message"), loading = $("#loading-message"), profile = $("#profile-content");
const retry = $("#retry-button"), openDelete = $("#open-delete-account");
const dialog = $("#delete-account-dialog"), form = $("#delete-account-form");
const confirmDelete = $("#confirm-delete-account"), deleteMessage = $("#delete-account-message");
function showError(element, text) {element.textContent = text; element.dataset.state = "error"; element.focus();}
async function loadProfile() {
    loading.hidden = false; profile.hidden = true; retry.hidden = true; message.textContent = ""; openDelete.disabled = true;
    try {
        const response = await authFetch(document.body.dataset.meUrl);
        const user = await readJSON(response);
        if (!response.ok) throw new Error();
        $("#profile-name").textContent = document.body.dataset.demoSession === "true" ? "کاربر آزمایشی" : user.username;
        $("#profile-username").textContent = user.username;
        $("#profile-email").textContent = user.email;
        $("#avatar").textContent = Array.from(user.username)[0].toUpperCase();
        profile.hidden = false; openDelete.disabled = false;
    } catch {showError(message, "دریافت اطلاعات حساب انجام نشد. اتصال اینترنت را بررسی کن و دوباره تلاش کن."); retry.hidden = false;}
    finally {loading.hidden = true;}
}
function resetPassword() {
    form.reset(); form.elements.password.type = "password";
    const toggle = form.querySelector(".password-toggle");
    toggle.textContent = "نمایش"; toggle.setAttribute("aria-pressed", "false"); toggle.setAttribute("aria-label", "نمایش رمز عبور");
}
function closeDelete() {if (!confirmDelete.disabled) dialog.close();}
openDelete.addEventListener("click", () => {
    resetPassword(); deleteMessage.textContent = ""; dialog.showModal(); form.elements.password.focus();
});
$("#close-delete-account").addEventListener("click", closeDelete);
$("#cancel-delete-account").addEventListener("click", closeDelete);
dialog.addEventListener("cancel", (event) => {if (confirmDelete.disabled) event.preventDefault();});
dialog.addEventListener("close", resetPassword);
form.addEventListener("submit", async (event) => {
    event.preventDefault(); if (confirmDelete.disabled) return;
    if (!form.elements.password.value) {showError(deleteMessage, "رمز عبور فعلی را وارد کن."); return;}
    confirmDelete.disabled = true; confirmDelete.textContent = "در حال حذف حساب…"; deleteMessage.textContent = "";
    try {
        const response = await authFetch(document.body.dataset.meUrl, {
            method:"DELETE", headers:{"Content-Type":"application/json"},
            body:JSON.stringify({password:form.elements.password.value}),
        });
        if (!response.ok) {
            showError(deleteMessage, response.status === 400 ? "رمز عبور فعلی درست نیست یا وارد نشده است." : "حذف حساب انجام نشد. دوباره تلاش کن.");
            return;
        }
        resetPassword(); dialog.close(); await finishAccountDeletion();
    } catch {showError(deleteMessage, "ارتباط با سرور برقرار نشد. وضعیت حساب را بررسی کن و دوباره تلاش کن.");}
    finally {confirmDelete.disabled = false; confirmDelete.textContent = "حذف دائمی حساب";}
});
retry.addEventListener("click", loadProfile);
loadProfile();

document.addEventListener("demo:status", () => {
    $("#profile-name").textContent = "کاربر آزمایشی";
    const badge = document.querySelector(".profile-badge");
    if (badge) badge.textContent = "فضای آزمایشی شخصی";
});
