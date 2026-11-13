function listActiveEmails(subscribers) {
  return subscribers
    .filter((subscriber) => subscriber.isActive === true)
    .map((subscriber) => subscriber.email.trim().toLowerCase());
}

module.exports = { listActiveEmails };
