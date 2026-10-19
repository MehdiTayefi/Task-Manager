import { authFetch, readJSON } from "./auth.js?v=5";
const $ = (selector) => document.querySelector(selector);
const list = $("#task-list"), loading = $("#tasks-loading"), empty = $("#tasks-empty");
const message = $("#page-message"), retry = $("#reload-tasks"), pager = $("#pagination");
const statusFilter = $("#status-filter"), priorityFilter = $("#priority-filter");
const dialog = $("#task-dialog"), form = $("#task-form"), saveButton = $("#save-task");
const deleteDialog = $("#delete-dialog"), deleteButton = $("#confirm-delete");
const api = document.body.dataset.tasksApiUrl;
const statusLabels = {todo:"انجام‌نشده", in_progress:"در حال انجام", done:"انجام‌شده"};
const priorityLabels = {low:"کم", medium:"متوسط", high:"زیاد"};
let page = 1, editing = null, deleting = null, requestNumber = 0;
function showMessage(element, text, state = "error") {
    element.textContent = text; element.dataset.state = state;
}
function itemURL(id) { return `${api}${encodeURIComponent(id)}/`; }
function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
}
function button(label, className, action) {
    const element = node("button", className, label);
    element.type = "button"; element.addEventListener("click", () => action(element));
    return element;
}
function formatDate(value) {
    if (!value) return "بدون مهلت";
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? "بدون مهلت" : new Intl.DateTimeFormat("fa-IR", {year:"numeric",month:"short",day:"numeric"}).format(date);
}
function renderTask(task) {
    const card = node("article", `task-card${task.status === "done" ? " is-done" : ""}`);
    const top = node("div", "task-card-top");
    const priority = priorityLabels[task.priority] ? task.priority : "medium";
    top.append(node("span", `priority-badge priority-${priority}`, `اولویت ${priorityLabels[priority]}`));
    const status = statusLabels[task.status] ? task.status : "todo";
    top.append(node("span", `status-badge status-${status}`, statusLabels[status]));
    card.append(top, node("h2", "task-title", task.title));
    if (task.description) card.append(node("p", "task-description", task.description));
    card.append(node("p", "task-date", `مهلت: ${formatDate(task.due_date)}`));
    const actions = node("div", "task-actions");
    actions.append(button(task.status === "done" ? "بازگشایی" : "انجام شد", "task-complete", async (control) => {
        control.disabled = true; showMessage(message, "");
        try {
            const response = await authFetch(itemURL(task.id), {
                method:"PATCH", headers:{"Content-Type":"application/json"},
                body:JSON.stringify({status:task.status === "done" ? "todo" : "done"}),
            });
            if (!response.ok) throw new Error();
            await loadTasks();
        } catch { showMessage(message, "تغییر وضعیت انجام نشد. دوباره تلاش کن."); }
        finally { control.disabled = false; }
    }));
    actions.append(button("جزئیات", "task-details", () => openDetails(task.id)));
    actions.append(button("ویرایش", "task-edit", () => openForm(task)));
    actions.append(button("حذف", "task-delete", () => {
        deleting = task; $("#delete-task-name").textContent = task.title;
        showMessage($("#delete-message"), ""); deleteDialog.showModal();
    }));
    card.append(actions); return card;
}
async function loadTasks() {
    const current = ++requestNumber;
    loading.hidden = false; empty.hidden = true; retry.hidden = true; pager.hidden = true;
    list.replaceChildren(); showMessage(message, "");
    $("#task-count").textContent = "";
    const url = new URL(api, window.location.origin);
    url.searchParams.set("page", page);
    if (statusFilter.value) url.searchParams.set("status", statusFilter.value);
    if (priorityFilter.value) url.searchParams.set("priority", priorityFilter.value);
    try {
        const response = await authFetch(url);
        if (current !== requestNumber) return;
        if (response.status === 404 && page > 1) { page--; return loadTasks(); }
        if (!response.ok) throw new Error();
        const data = await readJSON(response);
        if (current !== requestNumber) return;
        if (!Array.isArray(data.results)) throw new Error();
        list.replaceChildren(...data.results.map(renderTask));
        empty.hidden = data.results.length !== 0;
        $("#task-count").textContent = `${new Intl.NumberFormat("fa-IR").format(data.count)} کار`;
        const total = Math.max(1, Math.ceil(data.count / 10));
        pager.hidden = data.count <= 10;
        $("#page-number").textContent = `صفحه ${new Intl.NumberFormat("fa-IR").format(page)} از ${new Intl.NumberFormat("fa-IR").format(total)}`;
        $("#previous-page").disabled = !data.previous;
        $("#next-page").disabled = !data.next;
    } catch {
        if (current !== requestNumber) return;
        showMessage(message, "دریافت کارها انجام نشد. اتصال اینترنت را بررسی کن و دوباره تلاش کن.");
        retry.hidden = false;
    } finally { if (current === requestNumber) loading.hidden = true; }
}
function openForm(task = null) {
    editing = task; form.reset(); showMessage($("#task-form-message"), "");
    $("#task-dialog-title").textContent = task ? "ویرایش کار" : "کار جدید";
    if (task) {
        for (const field of ["title", "description", "status", "priority", "due_date"]) form.elements[field].value = task[field] || "";
    }
    dialog.showModal(); form.elements.title.focus();
}
function closeForm() { if (!saveButton.disabled) dialog.close(); }
$("#new-task").addEventListener("click", () => openForm());
$("#close-task-dialog").addEventListener("click", closeForm);
$("#cancel-task").addEventListener("click", closeForm);
dialog.addEventListener("cancel", (event) => {if (saveButton.disabled) event.preventDefault();});
form.addEventListener("submit", async (event) => {
    event.preventDefault(); if (saveButton.disabled) return;
    const payload = Object.fromEntries(new FormData(form));
    payload.title = payload.title.trim(); payload.due_date = payload.due_date || null;
    if (!payload.title) {showMessage($("#task-form-message"), "عنوان کار نمی‌تواند خالی باشد."); return;}
    saveButton.disabled = true; saveButton.textContent = "در حال ذخیره…";
    showMessage($("#task-form-message"), "");
    try {
        const response = await authFetch(editing ? itemURL(editing.id) : api, {
            method:editing ? "PATCH" : "POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload),
        });
        if (!response.ok) {
            showMessage($("#task-form-message"), response.status === 400 ? "اطلاعات واردشده معتبر نیست. عنوان، وضعیت، اولویت و تاریخ را بررسی کن." : "ذخیره کار انجام نشد. دوباره تلاش کن.");
            return;
        }
        dialog.close(); if (!editing) page = 1; await loadTasks();
    } catch {showMessage($("#task-form-message"), "ارتباط با سرور برقرار نشد. دوباره تلاش کن.");}
    finally {saveButton.disabled = false; saveButton.textContent = "ذخیره کار";}
});
$("#cancel-delete").addEventListener("click", () => {if (!deleteButton.disabled) deleteDialog.close();});
deleteDialog.addEventListener("cancel", (event) => {if (deleteButton.disabled) event.preventDefault();});
deleteButton.addEventListener("click", async () => {
    if (deleteButton.disabled || !deleting) return;
    deleteButton.disabled = true; deleteButton.textContent = "در حال حذف…";
    try {
        const response = await authFetch(itemURL(deleting.id), {method:"DELETE"});
        if (!response.ok) throw new Error();
        deleteDialog.close(); await loadTasks();
    } catch {showMessage($("#delete-message"), "حذف کار انجام نشد. دوباره تلاش کن.");}
    finally {deleteButton.disabled = false; deleteButton.textContent = "حذف کار";}
});
for (const filter of [statusFilter, priorityFilter]) filter.addEventListener("change", () => {page = 1; loadTasks();});
$("#previous-page").addEventListener("click", () => {if(page > 1) {page--; loadTasks();}});
$("#next-page").addEventListener("click", () => {page++; loadTasks();});
retry.addEventListener("click", loadTasks);
loadTasks();


const detailDialog = $("#task-detail-dialog");
let detailedTask = null, detailRequest = 0;
function dateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : new Intl.DateTimeFormat("fa-IR", {dateStyle:"medium",timeStyle:"short"}).format(date);
}
async function openDetails(id) {
    const current = ++detailRequest;
    detailedTask = null; $("#task-detail-content").hidden = true;
    $("#edit-task-from-detail").hidden = true; $("#task-detail-loading").hidden = false;
    showMessage($("#task-detail-message"), ""); detailDialog.showModal();
    try {
        const response = await authFetch(itemURL(id));
        if (current !== detailRequest) return;
        if (!response.ok) {
            showMessage($("#task-detail-message"), response.status === 404 ? "این کار پیدا نشد یا به آن دسترسی نداری." : "دریافت جزئیات انجام نشد. دوباره تلاش کن."); return;
        }
        const task = await readJSON(response);
        if (current !== detailRequest) return;
        detailedTask = task;
        $("#detail-title").textContent = task.title;
        $("#detail-description").textContent = task.description || "توضیحی ثبت نشده است.";
        $("#detail-status").textContent = statusLabels[task.status] || "—";
        $("#detail-priority").textContent = priorityLabels[task.priority] || "—";
        $("#detail-due").textContent = formatDate(task.due_date);
        $("#detail-created").textContent = dateTime(task.created_at);
        $("#detail-updated").textContent = dateTime(task.updated_at);
        $("#task-detail-content").hidden = false; $("#edit-task-from-detail").hidden = false;
    } catch {if (current === detailRequest) showMessage($("#task-detail-message"), "ارتباط با سرور برقرار نشد. دوباره تلاش کن.");}
    finally {if (current === detailRequest) $("#task-detail-loading").hidden = true;}
}
for (const selector of ["#close-task-detail", "#dismiss-task-detail"]) $(selector).addEventListener("click", () => detailDialog.close());
detailDialog.addEventListener("close", () => {detailRequest++;});
$("#edit-task-from-detail").addEventListener("click", () => {if(detailedTask) {const task = detailedTask; detailDialog.close(); openForm(task);}});
