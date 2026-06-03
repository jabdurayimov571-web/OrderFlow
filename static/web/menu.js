"use strict";

const TOKEN = document.body.dataset.token;
const API = "/api";

let MENU = [];
let CART = []; // {uid, item, modifiers:[mod], quantity, note}

const $ = (id) => document.getElementById(id);
const money = (n) => Math.round(Number(n)).toLocaleString("ru-RU") + " so'm";
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const show = (id) => ($(id).hidden = false);
const hide = (id) => ($(id).hidden = true);

// ---------- Init ----------
async function init() {
  try {
    const tRes = await fetch(`${API}/tables/${TOKEN}/`);
    if (!tRes.ok) throw new Error("Stol topilmadi yoki faol emas. QR kodni qayta skanerlang.");
    const table = await tRes.json();
    $("tableBadge").textContent = "Stol #" + table.number;

    const mRes = await fetch(`${API}/menu/categories/`);
    MENU = await mRes.json();
    renderMenu();
    hide("loading");
    show("menu");
  } catch (e) {
    hide("loading");
    $("error").textContent = e.message;
    show("error");
  }
}

// ---------- Menyu ----------
function renderMenu() {
  const root = $("menu");
  root.innerHTML = "";
  let count = 0;
  MENU.forEach((cat) => {
    if (!cat.items.length) return;
    count += cat.items.length;
    const sec = document.createElement("section");
    sec.innerHTML = `<h2 class="menu__cat-title">${esc(cat.name)}</h2>`;
    cat.items.forEach((item) => sec.appendChild(itemCard(item)));
    root.appendChild(sec);
  });
  if (!count) root.innerHTML = '<div class="state">Hozircha taomlar yo\'q.</div>';
}

function itemCard(item) {
  const el = document.createElement("div");
  el.className = "item";
  const img = item.image
    ? `<img class="item__img" src="${item.image}" alt="">`
    : `<div class="item__img">🍽️</div>`;
  el.innerHTML = `
    ${img}
    <div class="item__body">
      <div class="item__name">${esc(item.name)}</div>
      <div class="item__desc">${esc(item.description || "")}</div>
      <div class="item__row">
        <span class="item__price">${money(item.price)}</span>
        <button class="btn btn--primary">Qo'shish</button>
      </div>
    </div>`;
  el.querySelector("button").addEventListener("click", () => openItem(item));
  return el;
}

// ---------- Taom tanlash ----------
let draft = null;
function openItem(item) {
  draft = { item, modifiers: [], quantity: 1, note: "" };
  const mods = (item.modifiers || [])
    .map(
      (m) => `
    <label class="mod">
      <input type="checkbox" value="${m.id}" data-price="${m.price_delta}">
      <span class="mod__name">${esc(m.name)}</span>
      <span class="mod__price">+${money(m.price_delta)}</span>
    </label>`
    )
    .join("");
  $("itemSheetPanel").innerHTML = `
    <div class="sheet__title">${esc(item.name)}</div>
    <div class="sheet__price" id="dPrice">${money(item.price)}</div>
    ${item.description ? `<p style="color:var(--muted);font-size:14px;margin-bottom:10px">${esc(item.description)}</p>` : ""}
    ${mods}
    <div class="field"><label>Izoh (ixtiyoriy)</label><input id="dNote" placeholder="masalan: piyozsiz"></div>
    <div class="field qty"><button id="dMinus">−</button><span id="dQty">1</span><button id="dPlus">+</button></div>
    <button class="btn btn--primary btn--block" id="dAdd">Savatga qo'shish · <span id="dAddTotal">${money(item.price)}</span></button>`;
  show("itemSheet");

  const recalc = () => {
    const modSum = [...$("itemSheetPanel").querySelectorAll("input:checked")].reduce(
      (s, c) => s + Number(c.dataset.price),
      0
    );
    $("dPrice").textContent = money(Number(item.price) + modSum);
    $("dAddTotal").textContent = money((Number(item.price) + modSum) * draft.quantity);
  };
  $("itemSheetPanel").querySelectorAll("input[type=checkbox]").forEach((c) => c.addEventListener("change", recalc));
  $("dMinus").onclick = () => { if (draft.quantity > 1) { draft.quantity--; $("dQty").textContent = draft.quantity; recalc(); } };
  $("dPlus").onclick = () => { draft.quantity++; $("dQty").textContent = draft.quantity; recalc(); };
  $("dAdd").onclick = () => {
    draft.modifiers = [...$("itemSheetPanel").querySelectorAll("input:checked")].map((c) =>
      item.modifiers.find((x) => String(x.id) === c.value)
    );
    draft.note = $("dNote").value.trim();
    CART.push({ uid: String(CART.length) + "-" + draft.item.id, ...draft });
    hide("itemSheet");
    updateCartBar();
  };
}

// ---------- Savat ----------
function lineTotal(c) {
  const modSum = c.modifiers.reduce((s, m) => s + Number(m.price_delta), 0);
  return (Number(c.item.price) + modSum) * c.quantity;
}
const cartTotal = () => CART.reduce((s, c) => s + lineTotal(c), 0);
const cartCount = () => CART.reduce((s, c) => s + c.quantity, 0);

function updateCartBar() {
  const bar = $("cartBar");
  if (!CART.length) { bar.hidden = true; return; }
  bar.hidden = false;
  $("cartCount").textContent = cartCount();
  $("cartTotal").textContent = money(cartTotal());
}

function openCart() {
  if (!CART.length) return;
  const lines = CART.map(
    (c, i) => `
    <div class="cart-line">
      <div class="cart-line__body">
        <div class="cart-line__name">${esc(c.item.name)} ×${c.quantity}</div>
        <div class="cart-line__meta">${c.modifiers.map((m) => esc(m.name)).join(", ")}${c.note ? " · " + esc(c.note) : ""}</div>
      </div>
      <div>
        <div class="cart-line__total">${money(lineTotal(c))}</div>
        <button class="btn btn--ghost" data-rm="${i}" style="margin-top:6px;padding:4px 10px">O'chirish</button>
      </div>
    </div>`
  ).join("");
  $("cartSheetPanel").innerHTML = `
    <div class="sheet__title">Savat</div>
    ${lines}
    <div class="cart-total-row"><span>Jami</span><span>${money(cartTotal())}</span></div>
    <div class="field"><label>Umumiy izoh (ixtiyoriy)</label><input id="orderNote" placeholder="masalan: tezroq bo'lsa"></div>
    <button class="btn btn--ok btn--block" id="placeBtn">Zakaz berish</button>`;
  $("cartSheetPanel").querySelectorAll("[data-rm]").forEach((b) =>
    b.addEventListener("click", () => {
      CART.splice(Number(b.dataset.rm), 1);
      updateCartBar();
      CART.length ? openCart() : hide("cartSheet");
    })
  );
  $("placeBtn").onclick = placeOrder;
  show("cartSheet");
}

// ---------- Zakaz berish ----------
async function placeOrder() {
  const btn = $("placeBtn");
  btn.disabled = true;
  btn.textContent = "Yuborilmoqda…";
  const payload = {
    table_token: TOKEN,
    payment_method: "cash",
    note: ($("orderNote") && $("orderNote").value.trim()) || "",
    items: CART.map((c) => ({
      menu_item: c.item.id,
      quantity: c.quantity,
      modifiers: c.modifiers.map((m) => m.id),
      note: c.note || "",
    })),
  };
  try {
    const res = await fetch(`${API}/orders/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Zakaz yuborishda xatolik yuz berdi.");
    const order = await res.json();
    CART = [];
    updateCartBar();
    hide("cartSheet");
    showConfirm(order);
  } catch (e) {
    alert(e.message);
    btn.disabled = false;
    btn.textContent = "Zakaz berish";
  }
}

function showConfirm(order) {
  $("confirmBox").innerHTML = `
    <div class="confirm__icon">✅</div>
    <h2>Zakaz qabul qilindi!</h2>
    <div class="confirm__num">#${order.number}</div>
    <p style="color:var(--muted);margin-bottom:6px">Jami: <b>${money(order.total)}</b></p>
    <p style="margin-bottom:18px">Iltimos, <b>kassaga borib to'lov qiling</b>. To'lovdan so'ng taom tayyorlanadi.</p>
    <button class="btn btn--primary btn--block" id="newOrderBtn">Yangi zakaz</button>`;
  $("newOrderBtn").onclick = () => location.reload();
  show("confirm");
}

// ---------- Global ----------
document.addEventListener("click", (e) => {
  if (e.target.matches("[data-close]")) { hide("itemSheet"); hide("cartSheet"); }
});
$("cartBar").addEventListener("click", openCart);
init();
