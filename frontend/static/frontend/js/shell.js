import { signOut, authFetch, readJSON } from "./auth.js?v=7";
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
async function endSession(button, errorTarget) {
    if (button.disabled) return;
    const original = button.textContent;
    button.disabled = true; button.textContent = "در حال خروج…";
    try {await signOut();}
    catch {errorTarget.textContent = "خروج انجام نشد. اتصال اینترنت را بررسی کن و دوباره تلاش کن.";errorTarget.dataset.state = "error";}
    finally {button.disabled = false;button.textContent = original;}
}
logout.addEventListener("click", () => endSession(logout,message));
const endDemo = document.querySelector("#end-demo");
endDemo.addEventListener("click", () => endSession(endDemo,document.querySelector("#demo-banner-message")));
async function loadDemoStatus() {
    try {
        const response = await authFetch(document.body.dataset.demoStatusUrl);
        if (!response.ok) return;
        const data = await readJSON(response);
        if (!data.is_demo) return;
        document.body.dataset.demoSession = "true";
        document.querySelector("#demo-banner").hidden = false;
        const danger = document.querySelector(".danger-zone");
        if (danger) danger.hidden = true;
        document.dispatchEvent(new CustomEvent("demo:status", {detail:data}));
        const expires = Date.parse(data.expires_at);
        if (!Number.isFinite(expires)) return;
        let timer;
        const update = () => {
            const remaining = Math.max(0,Math.ceil((expires-Date.now())/1000));
            const digits = new Intl.NumberFormat("fa-IR",{minimumIntegerDigits:2,useGrouping:false});
            document.querySelector("#demo-countdown").textContent = `${digits.format(Math.floor(remaining/60))}:${digits.format(remaining%60)}`;
            if (!remaining) {clearInterval(timer);window.location.replace(`${document.body.dataset.loginUrl}?demo_expired=1`);}
        };
        update(); timer = setInterval(update,1000);
    } catch { /* Profile/tasks retain their own retry and authentication handling. */ }
}
loadDemoStatus();
