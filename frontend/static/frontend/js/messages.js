const fields = {username:"نام کاربری",email:"ایمیل",password:"رمز عبور",password_confirm:"تکرار رمز عبور",non_field_errors:"اطلاعات فرم",detail:"خطا"};
function translate(message, field) {
    const text = String(message);
    if (/[\u0600-\u06ff]/u.test(text)) return text;
    const lower = text.toLowerCase();
    if (/already exists|unique/.test(lower)) return field === "email" ? "این ایمیل قبلاً ثبت شده است." : "این نام کاربری قبلاً استفاده شده است.";
    if (/do not match|does not match|don't match/.test(lower)) return "رمز عبور و تکرارش یکسان نیستند.";
    if (/whitespace|white space|space/.test(lower)) return "رمز عبور نباید فاصله، تب یا خط جدید داشته باشد.";
    if (/too short|at least/.test(lower)) {
        const minimum = text.match(/at least (\d+)/i)?.[1];
        return minimum ? `رمز عبور باید دست‌کم ${new Intl.NumberFormat("fa-IR").format(Number(minimum))} کاراکتر داشته باشد.` : "رمز عبور بیش از حد کوتاه است.";
    }
    if (/too common/.test(lower)) return "این رمز بیش از حد رایج است؛ رمز قوی‌تری انتخاب کن.";
    if (/entirely numeric/.test(lower)) return "رمز عبور نباید فقط از عدد تشکیل شود.";
    if (/too similar/.test(lower)) return "رمز عبور بیش از حد به اطلاعات شخصی‌ات شباهت دارد.";
    if (/valid email/.test(lower)) return "یک آدرس ایمیل معتبر وارد کن.";
    if (/valid username/.test(lower)) return "نام کاربری فقط می‌تواند شامل حروف، عدد و نشانه‌های @ . + - _ باشد.";
    if (/required|blank|null/.test(lower)) return "این فیلد را کامل کن.";
    if (/no more than|at most|max_length/.test(lower)) return "مقدار واردشده بیش از حد طولانی است.";
    return "مقدار این فیلد معتبر نیست؛ آن را بررسی کن.";
}
export function registrationErrors(errors) {
    if (!errors || typeof errors !== "object") return "اطلاعات فرم معتبر نیست؛ دوباره بررسی کن.";
    return Object.entries(errors).flatMap(([field,values]) => (Array.isArray(values) ? values : [values]).map(value=>`${fields[field] || "خطا"}: ${translate(value,field)}`)).join("\n");
}
