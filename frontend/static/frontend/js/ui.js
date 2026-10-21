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

for (const field of document.querySelectorAll("input,textarea,select")) {
    field.addEventListener("invalid", () => {
        field.setCustomValidity("");
        if (field.validity.valueMissing) field.setCustomValidity("این فیلد را کامل کن.");
        else if (field.validity.typeMismatch && field.type === "email") field.setCustomValidity("یک آدرس ایمیل معتبر وارد کن.");
        else if (field.validity.tooLong) field.setCustomValidity("متن واردشده بیش از حد طولانی است.");
        else if (field.validity.badInput) field.setCustomValidity("مقدار معتبری وارد کن.");
    });
    field.addEventListener("input", () => field.setCustomValidity(""));
    field.addEventListener("change", () => field.setCustomValidity(""));
}
