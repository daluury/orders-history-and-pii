# Requirements

What the project builds and what the solutions must satisfy. The story: an online shop keeps customers and orders. Every hour a snapshot of the current state of all orders arrives, and separately a CSV with customers and their personal data.

Two things are needed:

- keep the history of order status changes (SCD Type 2), so it is known which status an order had at any moment;
- process the customers file under GDPR: protect the email so that it can be restored when needed.

Both parts use one dataset and are linked by `customer_id`. The order history holds identifiers only, no email.

## Data

`users.csv`:

| Field | Type | Note |
|:-----|:-----|:-----|
| customer_id | int | link to orders, not personal on its own |
| email | text | protected |
| first_name, last_name | text | personal |
| phone | text | personal |
| country | text | |
| registration_date | date | |
| subscription_type | text | free / basic / premium |

`stg_orders` (a snapshot of the current state; its content is replaced on every load):

| Field | Type | Note |
|:-----|:-----|:-----|
| order_id | int | |
| customer_id | int | |
| status | varchar(50) | new, processing, shipped, delivered, cancelled |
| updated_at | timestamp | update time in the source |

Allowed transitions: new → processing → shipped → delivered; from new and processing an order can go to cancelled. Delivered and cancelled orders do not change any more.

## Generator

Built on Faker with one seeded object per run: the same seed gives the same data. Modes:

- `clean`: a series of snapshots where some orders advance in status, new orders appear, cancelled orders stay in the snapshots; all emails are valid.
- `dirty`: the same plus four traps for orders:
  1. a snapshot is delivered twice;
  2. an old snapshot arrives after a newer one;
  3. an order row is duplicated inside one snapshot;
  4. an order is missing from one snapshot and comes back in the next one.

  Customers get broken emails too: with spaces and upper case, invalid, and duplicated with another case.

The generator also writes the expected results, so a solution can be checked: `expected_history.csv`, `expected_users_quarantine.csv`, and `traps.csv` with the places of the traps.

## Part A: order history (SCD2)

Result table `orders_history`:

| Field | Note |
|:-----|:-----|
| order_id, customer_id, status | |
| valid_from | `updated_at` of the version in the source |
| valid_to | NULL for the current version (or a placeholder, the choice is documented) |
| is_current | marks the current version |

Requirements:

- loading a snapshot and running the procedure adds new versions only for orders whose status changed;
- running it again with the same snapshot changes nothing (idempotent);
- a late old snapshot does not break the history or overwrite newer versions; versions that are not in the history yet are inserted at the right place;
- duplicated rows inside a snapshot do not create extra versions;
- a missing order is handled by an explicit, documented rule (keep the version open or close it);
- it runs in a reasonable time on a large dataset, and how it was measured is written down.

The same result is also built with a dbt snapshot, and the two variants are compared in [decisions.md](decisions.md).

## Part B: email protection

A function in `pii_protection`:

- takes a path to a CSV (or a stream of rows) and keys from environment variables, and writes a protected CSV; it knows nothing about the database or storage;
- reads the file in chunks and never holds the whole file in memory;
- brings the email to a canonical form (spaces, case) before processing;
- replaces `email` with `email_pseudonym` (HMAC with a secret key: the same email always gives the same value, so it can be searched and counted) and `email_encrypted` (encryption with a key, so the original email can be restored);
- has a separate function that restores the email from `email_encrypted`;
- sends rows with an invalid email to a quarantine file with the reason instead of failing;
- passes the other fields unchanged (names and phone: see [decisions.md](decisions.md));
- keeps keys out of the repository: `.env.example` has variable names only.

A plain hash such as SHA-256 of an email is not enough: emails can be guessed from a dictionary, so a secret key is needed.

The protected result is loaded into the PostgreSQL table `users_protected`, next to the orders. A real service would use an encrypted bucket with restricted access, see [pii-protection.md](pii-protection.md).
