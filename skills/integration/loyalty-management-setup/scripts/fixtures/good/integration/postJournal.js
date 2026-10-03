export async function postJournal(base, token, cart, journal) {
  const eligible = await fetch(`${base}/services/data/v67.0/global-promotions-management/eligible-promotions`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: JSON.stringify(cart)
  }).then((r) => r.json());
  journal.appliedPromotions = eligible.promotions;
  return fetch(`${base}/services/data/v67.0/connect/realtime/loyalty/programs/SkyRewards`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: JSON.stringify({ transactionJournals: [journal] })
  });
}
