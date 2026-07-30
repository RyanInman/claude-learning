const test = require("node:test");
const assert = require("node:assert/strict");
const { applyDiscount } = require("./discount");

test("gold tier over 100 gets 20% off", () => {
  const cart = { items: [{ price: 60, qty: 2 }] }; // total 120
  const customer = { tier: "gold" };
  assert.ok(Math.abs(applyDiscount(cart, customer) - 96) < 0.001);
});
