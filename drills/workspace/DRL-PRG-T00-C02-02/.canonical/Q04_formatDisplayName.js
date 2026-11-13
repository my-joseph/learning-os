function formatDisplayName(profile) {
  const fullName = (profile?.fullName ?? '').trim();
  if (fullName) {
    return fullName;
  }
  const username = (profile?.username ?? '').trim();
  if (username) {
    return username;
  }
  return 'Guest';
}

module.exports = { formatDisplayName };
