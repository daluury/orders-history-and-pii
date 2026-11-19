# Decisions

Assumptions, choices between options and the comparison with the first version of this task. It is filled in while the solutions are written; the headings below are the frame.

## 1. Assumptions

- `customer_id` is added to `stg_orders` and `users.csv`, so orders and customers are one dataset (the original task has no link between them).
- The generator changes an order at most once per hour, and the expected history contains every version that was visible in at least one delivered snapshot.
- TODO: anything else assumed while writing the solutions.

## 2. Open choices

| Question | Options | Choice | Why |
|:-----|:-----|:-----|:-----|
| An order disappears from a snapshot | keep the version open / close it | TODO | TODO |
| `valid_to` of the current version | `NULL` / a far-future date | TODO | TODO |
| Late snapshot with versions that are not in the history yet | insert them in the right place / ignore the late snapshot | TODO | TODO |
| Reversible email protection | symmetric encryption / separate lookup table | TODO | TODO |
| First name, last name, phone | keep as is / mask / remove | TODO | TODO |
| Where the dbt `profiles.yml` lives | in the repository without passwords (`env_var`) / in `~/.dbt/` | TODO | TODO |
| Where to store the protected result | PostgreSQL table / bucket | PostgreSQL table `users_protected` (orders are next to it); a bucket for a real service, see `pii-protection.md` | |

## 3. Performance notes

| What | Dataset | Time | How measured |
|:-----|:-----|:-----|:-----|
| SCD2 for one snapshot | large | TODO | TODO |
| Email protection of the whole file | large | TODO | TODO |
| Peak memory of the email protection | large | TODO | TODO |

## 4. dbt snapshot vs SQL solution

TODO: where dbt is simpler, where its behaviour differs from the requirements (late snapshot, disappearing order, duplicates).

## 5. Comparison with the first solution

Do this only after the SQL and Python solutions are finished: open the first version of the solution for the first time here, not earlier.

Order of work:

1. Write down, from memory and without opening the old code, how the new solution handles each row of the table below.
2. Open the old solution and fill in the "old" column.
3. For every difference, write why the solutions diverged and which one is better for which reason. A difference without a reason does not count.
4. Optional: run the old SQL on the same data (it has no `customer_id`; the extra column has to be ignored).

| Aspect | New solution | Old solution | Why they differ |
|:-----|:-----|:-----|:-----|
| Idempotence (same snapshot twice) | | | |
| Late old snapshot | | | |
| Duplicated rows in one snapshot | | | |
| Order missing from a snapshot | | | |
| Speed on the large dataset | | | |
| Email canonicalization | | | |
| Pseudonym (key, algorithm) | | | |
| Reversibility (how, with which key) | | | |
| Invalid emails | | | |
| Memory use on a big file | | | |
| Keys and secrets handling | | | |
| What each one checks with its own tests | | | |

Summary (3–5 sentences): what was found in the new solution that the old one did better, and the other way round.
