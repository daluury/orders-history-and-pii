-- Tables that exist before the solutions run.
-- orders_history is created by scd2_orders/solution.sql (it is part of the solution).

-- Current-state snapshot of orders. The content is replaced on every load.
-- No primary key on purpose: a dirty snapshot can contain duplicated rows.
CREATE TABLE IF NOT EXISTS stg_orders (
    order_id    integer     NOT NULL,
    customer_id integer     NOT NULL,
    status      varchar(50) NOT NULL,
    updated_at  timestamp   NOT NULL
);

-- Result of pii_protection: email replaced by two fields, other fields unchanged.
CREATE TABLE IF NOT EXISTS users_protected (
    customer_id       integer PRIMARY KEY,
    email_pseudonym   text    NOT NULL,
    email_encrypted   text    NOT NULL,
    first_name        text,
    last_name         text,
    phone             text,
    country           text,
    registration_date date,
    subscription_type text
);
