# Email protection

Skeleton, to be filled in when the function is ready.

## What is protected and why

TODO: the GDPR requirement, why a plain hash is not enough (emails are guessed by a dictionary), what the pseudonym and the encrypted value are for.

## Design

TODO: canonical form, HMAC pseudonym, encryption, chunked reading, quarantine.

## Other personal fields

TODO: decision about names and phone (see `decisions.md`).

## Where the result is stored

TODO: PostgreSQL table `users_protected` in this project; for a real service a bucket with encryption and restricted access, and how the function would be called from a storage event.

## Keys

TODO: where keys come from (environment), what happens when a key is lost, key rotation as a next step (not implemented).
