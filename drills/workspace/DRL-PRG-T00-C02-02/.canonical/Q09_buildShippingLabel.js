function buildShippingLabel(order) {
  const {
    customer: {
      name,
      address: { city, postalCode },
    },
    items,
  } = order;
  const noun = items.length === 1 ? 'item' : 'items';
  return `${name} - ${city} ${postalCode} (${items.length} ${noun})`;
}

module.exports = { buildShippingLabel };
