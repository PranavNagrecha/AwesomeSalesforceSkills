export async function postJournal(base, token, journal) {
  journal.appliedPromotions = [{ promotionId: '0c8RM0000004FiXYAU' }];
  return fetch(`${base}/services/data/v67.0/connect/realtime/loyalty/programs/SkyRewards`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: JSON.stringify({ transactionJournals: [journal] })
  });
}
