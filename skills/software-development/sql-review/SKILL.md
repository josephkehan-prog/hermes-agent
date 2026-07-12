---
name: sql-review
description: "Use when the user wants a SQL query or statement reviewed for correctness, safety, and performance before running it."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: software-development
    tags: [sql, database, review, query, performance]
    related_skills: [requesting-code-review, systematic-debugging]
---

# SQL Review

## Boundary

Review a SQL statement and report risks before it runs. Use for correctness,
data-safety, and performance concerns. Do not execute the query, and do not
assume a schema the user has not shown — flag assumptions instead.

## Safety First (report as CRITICAL, before anything else)

| Check | Problem |
|---|---|
| `UPDATE`/`DELETE` without `WHERE` | Rewrites/erases the whole table |
| `WHERE` on a nullable column with `= NULL` | Never matches; use `IS NULL` |
| `DROP`/`TRUNCATE` | Irreversible; confirm intent and backups explicitly |
| String-built values (injection shape) | Parameterize; never concatenate input |
| Missing transaction around multi-statement writes | Partial failure leaves inconsistent state |

If any CRITICAL item fires, lead with it and tell the user to confirm before
running.

## Correctness

- `JOIN` without an `ON` (or with a wrong key) → accidental cross join.
- Aggregates (`SUM`, `COUNT`) mixed with non-grouped columns → wrong results or
  an error depending on the engine; every non-aggregated select column must be
  in `GROUP BY`.
- `NOT IN (subquery)` where the subquery can return NULL → returns no rows
  unexpectedly; prefer `NOT EXISTS`.
- `HAVING` used for row filters that belong in `WHERE`.

## Performance

- Leading wildcard `LIKE '%x'` → cannot use an index.
- Function on an indexed column in `WHERE` (`WHERE lower(email) = …`) → defeats
  the index unless a matching functional index exists.
- `SELECT *` in application queries → over-fetch; name columns.
- Missing `LIMIT` on an exploratory or UI-facing query.
- Correlated subquery that could be a `JOIN` → possible N+1 at the DB level.

## Procedure

1. Classify the statement (read vs write). Writes get the Safety pass first.
2. Walk the clauses (`SELECT`/`FROM`/`JOIN`/`WHERE`/`GROUP BY`/`HAVING`/
   `ORDER BY`/`LIMIT`) against the checks above.
3. For each finding: quote the clause, state the problem, give the fix.
4. Note any schema/index assumption you had to make to judge performance.

## Rules

1. State the SQL dialect if the user named one; if not, flag any check that is
   dialect-specific rather than assuming.
2. Do not rewrite the whole query unasked — report findings; offer a corrected
   version only when the user wants one or a CRITICAL fix requires it.
3. Never claim a query is "safe to run" — report what you checked and what you
   could not verify without the schema.

## Stop Conditions

- Input is not SQL: say so.
- Query references tables/columns whose types you cannot see and the judgment
  depends on them: report the finding as conditional and name what you need.

## Completion Gate

Done when CRITICAL safety issues are surfaced first, each finding has clause +
problem + fix, and unverifiable assumptions are stated explicitly.
