import { signOut } from "./auth.js?v=5";
const menu = document.querySelector("#app-menu");
const toggle = document.querySelector("#menu-toggle");
const close = document.querySelector("#menu-close");
const logout = document.querySelector("#logout-button");
const message = document.querySelector("#shell-message");
toggle.addEventListener("click", () => {
    message.textContent = "";
    menu.showModal(); toggle.setAttribute("aria-expanded", "true");
});
close.addEventListener("click", () => menu.close());
menu.addEventListener("close", () => {toggle.setAttribute("aria-expanded", "false"); toggle.focus();});
menu.addEventListener("click", (event) => {
    const box = menu.getBoundingClientRect();
    if (event.target === menu && (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom)) menu.close();
});
logout.addEventListener("click", async () => {
    if (logout.disabled) return;
    logout.disabled = true; logout.textContent = "در حال خروج…";
    try { await signOut(); }
    catch { message.textContent = "خروج از حساب انجام نشد. اتصال اینترنت را بررسی کن و دوباره تلاش کن."; message.dataset.state = "error"; }
    finally { logout.disabled = false; logout.textContent = "خروج از حساب ↗"; }
});
