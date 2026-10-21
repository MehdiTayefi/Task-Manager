// Access stays in this module's memory; refresh is an HttpOnly server cookie.
const routes = document.body.dataset;
let accessToken = null;
let pendingRefresh = null;
const channel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("taskly-session") : null;
if (channel) channel.onmessage = (event) => {
    if (event.data === "signed-out") {
        accessToken = null;
        window.location.replace(routes.loginUrl);
    }
};

export function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}

export async function readJSON(response) {
    try { return await response.json(); } catch { return {}; }
}

export function errorText(data, fallback) {
    const value = data.errors || data;
    if (typeof value === "string") return value;
    if (Array.isArray(value)) return value.map(String).join(" ");
    if (value && typeof value === "object") {
        const values = Object.values(value).flat().map(String);
        if (values.length) return values.join(" ");
    }
    return fallback;
}

export async function postBrowser(url, data = {}) {
    const target = new URL(url, window.location.origin);
    if (target.origin !== window.location.origin) throw new Error("ارسال درخواست فقط به همین سایت مجاز است.");
    return fetch(target, {
        method: "POST", credentials: "same-origin", mode: "same-origin", cache: "no-store",
        headers: {"Content-Type": "application/json", "Accept": "application/json", "X-CSRFToken": csrfToken()},
        body: JSON.stringify(data),
    });
}

export async function signIn(username, password) {
    const response = await postBrowser(routes.browserLoginUrl, {username, password});
    const data = await readJSON(response);
    if (!response.ok) throw new Error(response.status === 403 ? "اعتبار صفحه تمام شده؛ صفحه را تازه کن و دوباره تلاش کن." : response.status === 401 ? "نام کاربری یا رمز عبور درست نیست، یا حساب غیرفعال شده است." : "ورود انجام نشد. اطلاعات را بررسی کن و دوباره تلاش کن.");
    accessToken = data.access;
    if (!accessToken) throw new Error("پاسخ سرور کامل نبود. دوباره تلاش کن.");
}

export function refreshAccess() {
    if (pendingRefresh) return pendingRefresh;
    const perform = async () => {
        const response = await postBrowser(routes.refreshUrl);
        const data = await readJSON(response);
        if (!response.ok) {
            accessToken = null;
            if (response.status === 401) {
                window.location.replace(routes.loginUrl);
                throw new Error("برای ادامه دوباره وارد حساب شو.");
            }
            throw new Error("تمدید ورود انجام نشد. صفحه را تازه کن و دوباره تلاش کن.");
        }
        if (!data.access) throw new Error("پاسخ سرور کامل نبود. دوباره تلاش کن.");
        accessToken = data.access;
        return accessToken;
    };
    // Serialize cookie rotation across tabs where the Web Locks API is available.
    pendingRefresh = (navigator.locks
        ? navigator.locks.request("taskly-refresh", perform)
        : perform()).finally(() => { pendingRefresh = null; });
    return pendingRefresh;
}

export async function authFetch(url, options = {}) {
    const target = new URL(url, window.location.origin);
    if (target.origin !== window.location.origin) throw new Error("ارسال درخواست فقط به همین سایت مجاز است.");
    if (!accessToken) await refreshAccess();
    const send = () => {
        const headers = new Headers(options.headers || {});
        headers.set("Authorization", `Bearer ${accessToken}`);
        headers.set("Accept", "application/json");
        return fetch(target, {...options, headers, credentials: "same-origin", mode: "same-origin", cache: "no-store"});
    };
    let response = await send();
    if (response.status === 401) {
        await refreshAccess();
        response = await send();
        if (response.status === 401) {
            accessToken = null;
            window.location.replace(routes.loginUrl);
            throw new Error("برای ادامه دوباره وارد حساب شو.");
        }
    }
    return response;
}

export async function signOut() {
    const perform = async () => {
        const response = await postBrowser(routes.logoutUrl);
        if (!response.ok) throw new Error("خروج از حساب انجام نشد. دوباره تلاش کن.");
        accessToken = null;
        if (channel) channel.postMessage("signed-out");
        window.location.replace(routes.loginUrl);
    };
    if (pendingRefresh) await pendingRefresh.catch(() => {});
    return navigator.locks ? navigator.locks.request("taskly-refresh", perform) : perform();
}


export async function finishAccountDeletion() {
    // The API has already revoked all user refresh tokens. Clear this browser too.
    accessToken = null;
    if (channel) channel.postMessage("signed-out");
    try { await postBrowser(routes.logoutUrl); } catch { /* The remaining cookie is revoked and cannot authenticate. */ }
    window.location.replace(`${routes.loginUrl}?deleted=1`);
}


export async function startDemo() {
    const response = await postBrowser(routes.demoStartUrl);
    const data = await readJSON(response);
    if (response.status !== 201 || !data.access) {
        throw new Error(response.status === 403 ? "اعتبار صفحه تمام شده است؛ صفحه را تازه کن." : response.status === 429 ? "تعداد درخواست‌های دمو زیاد است. کمی بعد دوباره امتحان کن." : "شروع دمو انجام نشد. دوباره تلاش کن.");
    }
    accessToken = data.access;
    return data;
}
