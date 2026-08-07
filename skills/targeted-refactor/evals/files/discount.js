function applyDiscount(cart, customer) {
  let total = cart.items.reduce((sum, i) => sum + i.price * i.qty, 0);
  if (customer.tier === "gold") {
    if (total > 100) {
      total = total - total * 0.2;
    } else {
      total = total - total * 0.1;
    }
  } else if (customer.tier === "silver") {
    if (total > 100) {
      total = total - total * 0.1;
    } else {
      total = total - total * 0.05;
    }
  } else {
    if (total > 200) {
      total = total - total * 0.05;
    }
  }
  return total;
}

module.exports = { applyDiscount };
