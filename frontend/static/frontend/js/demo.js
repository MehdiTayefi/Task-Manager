import { startDemo } from "./auth.js?v=7";
const controls = document.querySelectorAll("[data-demo-start]");
let busy = false;
for (const control of controls) control.addEventListener("click", async () => {
    if (busy) return;
    busy = true;
    const message = document.querySelector("#demo-start-message");
    message.textContent = "";
    for (const button of controls) {button.disabled = true;button.textContent = "در حال آماده‌کردن فضای تو…";}
    try {await startDemo();window.location.assign(document.body.dataset.tasksUrl);}
    catch (error) {message.textContent = error instanceof TypeError ? "ارتباط با سرور برقرار نشد. دوباره تلاش کن." : error.message;message.dataset.state = "error";message.focus();}
    finally {busy = false;for (const button of controls) {button.disabled = false;button.textContent = "✦ امتحان دمو ←";}}
});
