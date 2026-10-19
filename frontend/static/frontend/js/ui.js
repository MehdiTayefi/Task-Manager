"use strict";
const persianUI = document.documentElement.lang === "fa";
document.querySelectorAll(".password-toggle").forEach((button) => {
    button.addEventListener("click", () => {
        const input = document.getElementById(button.getAttribute("aria-controls"));
        const visible = input.type === "password";
        input.type = visible ? "text" : "password";
        button.textContent = persianUI ? (visible ? "پنهان" : "نمایش") : (visible ? "Hide" : "Show");
        button.setAttribute("aria-pressed", String(visible));
        button.setAttribute("aria-label", persianUI ? `${visible ? "پنهان‌کردن" : "نمایش"} رمز عبور` : `${visible ? "Hide" : "Show"} ${input.id === "password" ? "password" : "password confirmation"}`);
    });
});
