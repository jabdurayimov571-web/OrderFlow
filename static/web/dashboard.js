"use strict";

const API = "/api";
const $ = (id) => document.getElementById(id);
const money = (n) => Math.round(Number(n)).toLocaleString("ru-RU") + " so'm";
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let TOKEN = localStorage.getItem("of_token") || "";
let WHO = localStorage.getItem("of_user") || "";
let timer = null;

const authHeaders = () => ({ Authorization: "Token " + TOKEN });

const STATUS_LABELS = {
  created: "Yaratildi",
  awaiting_payment: "To'lov kutmoqda",
  preparing: "Tayyorlanmoqda",
  ready: "Tayyor",
  completed: "Berildi",
  cancelled: "Bekor qilindi",
};

// ---------- Login ----------
$("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("loginError").hidden = true;
  try {
    const res = await fetch(`${API}/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: $("username").value.trim(), password: $("password").value }),
    });
    if (!res.ok) throw new Error("Login yoki parol noto'g'ri.");
    const data = await res.json();
    if (data.role !== "admin") throw new Error("Bu hisob admin emas.");
    TOKEN = data.token; WHO = data.username;
    localStorage.setItem("of_token", TOKEN);
    localStorage.setItem("of_user", WHO);
    startBoard();
  } catch (err) {
    $("loginError").textContent = err.message;
    $("loginError").hidden = false;
  }
});

function logout() {
  TOKEN = ""; WHO = "";
  localStorage.removeItem("of_token");
  localStorage.removeItem("of_user");
  if (timer) clearInterval(timer);
  $("board").hidden = true;
  $("login").hidden = false;
}
$("logout").addEventListener("click", logout);

// ---------- Board ----------
function startBoard() {
  $("login").hidden = true;
  $("board").hidden = false;
  $("who").textContent = WHO;
  load();
  timer = setInterval(load, 10000);
}

async function load() {
  try {
    const res = await fetch(`${API}/analytics/summary/`, { headers: authHeaders() });
    if (res.status === 401 || res.status === 403) { logout(); return; }
    render(await res.json());
  } catch (e) { /* tarmoq xatosi - keyingi yangilanishda qayta urinadi */ }
}

function card(label, val) {
  return `<div class="card"><div class="card__val">${val}</div><div class="card__label">${label}</div></div>`;
}

function render(d) {
  $("cards").innerHTML = [
    card("Bugungi zakazlar", d.orders_today),
    card("Jami zakazlar", d.orders_total),
    card("Bugungi savdo", money(d.revenue_today)),
    card("Jami savdo", money(d.revenue_total)),
    card("O'rtacha chek", money(d.avg_check)),
  ].join("");

  const max = Math.max(...d.last_7_days.map((x) => x.revenue), 1);
  $("chart").innerHTML = d.last_7_days.map((x) => `
    <div class="cbar" title="${esc(x.date)}: ${money(x.revenue)}">
      <div class="cbar__fill" style="height:${Math.round((x.revenue / max) * 100)}%"></div>
      <div class="cbar__label">${x.date.slice(5)}</div>
    </div>`).join("");

  $("top").innerHTML = d.top_items.length
    ? d.top_items.map((t, i) => `<div class="trow"><span>${i + 1}. ${esc(t.name)}</span><span>${t.qty} ta · ${money(t.revenue)}</span></div>`).join("")
    : '<p class="muted">Ma\'lumot yo\'q</p>';

  const entries = Object.entries(d.by_status);
  $("statuses").innerHTML = entries.length
    ? entries.map(([k, v]) => `<div class="srow"><span>${STATUS_LABELS[k] || k}</span><b>${v}</b></div>`).join("")
    : '<p class="muted">Ma\'lumot yo\'q</p>';
}

// ---------- Init ----------
if (TOKEN) startBoard();
