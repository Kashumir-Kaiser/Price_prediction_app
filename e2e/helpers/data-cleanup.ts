export async function cleanupTestUser(email: string): Promise<void> {
  const res = await fetch(`http://localhost:8000/api/admin/cleanup-test-user?email=${encodeURIComponent(email)}`, {
    method: 'DELETE',
    headers: { 'X-Test-Secret': process.env.TEST_SECRET || 'test-secret' },
  });
  if (!res.ok && res.status !== 404) {
    console.warn('Failed to cleanup test user:', await res.text());
  }
}

export async function cleanupTestData(symbol: string): Promise<void> {
  await fetch(`http://localhost:8000/api/admin/cleanup-test-data?symbol=${symbol}`, {
    method: 'DELETE',
    headers: { 'X-Test-Secret': process.env.TEST_SECRET || 'test-secret' },
  });
}
