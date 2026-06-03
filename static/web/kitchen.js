"use strict";

const API = "/api";
const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let TOKEN = localStorage.getItem("of_token") || "";
let WHO = localStorage.getItem("of_user") || "";
let knownIds = new Set();
let pollTimer = null;
let tickTimer = null;
let audioCtx = null;

const authHeaders = () => ({ Authorization: "Token " + TOKEN });

function beep() {
  try {
    if (!audioCtx) return;
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.connect(g); g.connect(audioCtx.destination);
    o.type = "sine"; o.frequency.value = 760;
    g.gain.setValueAtTime(0.001, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.3, audioCtx.currentTime + 0.02);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
    o.start(); o.stop(audioCtx.currentTime + 0.41);
  } catch (e) { /* ovoz qo'llab-quvvatlanmasa - e'tiborsiz */ }
}

// ---------- Login ----------
$("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = $("username").value.trim();
  const password = $("password").value;
  $("loginError").hidden = true;
  try {
    const res = await fetch(`${API}/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error("Login yoki parol noto'g'ri.");
    const data = await res.json();
    if (!(data.role === "oshpaz" || data.role === "admin"))
      throw new Error("Bu hisob oshpaz emas.");
    TOKEN = data.token; WHO = data.username;
    localStorage.setItem("of_token", TOKEN);
    localStorage.setItem("of_user", WHO);
    try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {}
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
  if (pollTimer) clearInterval(pollTimer);
  if (tickTimer) clearInterval(tickTimer);
  $("board").hidden = true;
  $("login").hidden = false;
}
$("logout").addEventListener("click", logout);

// ---------- Board ----------
function startBoard() {
  $("login").hidden = true;
  $("board").hidden = false;
  $("who").textContent = WHO;
  knownIds = new Set();
  poll();
  pollTimer = setInterval(poll, 4000);
  tickTimer = setInterval(updateTimers, 1000);
}

async function poll() {
  try {
    const res = await fetch(`${API}/orders/kitchen/`, { headers: authHeaders() });
    if (res.status === 401) { logout(); return; }
    const orders = await res.json();
    const hasNew = orders.some((o) => !knownIds.has(o.public_id));
    if (hasNew && knownIds.size > 0) beep();
    knownIds = new Set(orders.map((o) => o.public_id));
    render(orders);
  } catch (e) { /* tarmoq xatosi - keyingi pollda qayta urinadi */ }
}

function render(orders) {
  $("empty").hidden = orders.length > 0;
  $("orders").innerHTML = orders.map(orderCard).join("");
  document.querySelectorAll("[data-ready]").forEach((b) =>
    b.addEventListener("click", () => markReady(b.dataset.ready, b)));
  updateTimers();
}

function orderCard(o) {
  const items = o.items.map((it) => `
    <li>${esc(it.name)} ×${it.quantity}
      ${it.modifiers.length ? `<span class="muted">(${it.modifiers.map(esc).join(", ")})</span>` : ""}
    </li>`).join("");
  return `
    <div class="card">
      <div class="card__head">
        <span class="num">#${o.number}</span>
        <span class="timer" data-since="${o.created_at}">--</span>
      </div>
      <div class="card__table">Stol ${o.table_number}</div>
      <ul class="items">${items}</ul>
      ${o.customer_note ? `<div class="note">📝 ${esc(o.customer_note)}</div>` : ""}
      <button class="btn btn--ok btn--block" data-ready="${o.public_id}">Tayyor</button>
    </div>`;
}

function updateTimers() {
  document.querySelectorAll(".timer[data-since]").forEach((el) => {
    const min = Math.floor((Date.now() - new Date(el.dataset.since).getTime()) / 60000);
    el.textContent = min + " daq";
    el.classList.toggle("timer--late", min >= 15);
  });
}

async function markReady(publicId, btn) {
  btn.disabled = true;
  btn.textContent = "...";
  try {
    const res = await fetch(`${API}/orders/kitchen/${publicId}/ready/`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error();
    knownIds.delete(publicId);
    poll();
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "Tayyor";
    alert("Xatolik yuz berdi. Qayta urinib ko'ring.");
  }
}

// ---------- Init ----------
if (TOKEN) startBoard();
