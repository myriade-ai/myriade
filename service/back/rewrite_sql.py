from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import sqlglot
from sqlglot import exp, parse_one


def _clean(identifier: str | None) -> str:
    """Lower-case identifier and strip any double quotes."""
    try:
        return str(identifier).strip('"').lower()
    except Exception:
        return ""


def rewrite_sql(sql: str, columns_privacy: List[Dict[str, str]]) -> str:
    # ---------------------------------------------------------------- privacy map
    privacy: Dict[str, Dict[str, bool]] = defaultdict(dict)
    for rule in columns_privacy:
        privacy[_clean(rule["table"])][_clean(rule["column"])] = bool(
            rule.get("encryption_key")
        )

    root = parse_one(sql)

    # ---------------------------------------------------------------- outer-query scan
    # Determine if the *top-level* SELECT list contains a plain "*". We need to ignore
    # the "*" that might appear inside function calls such as COUNT(*).
    outer_has_star = any(
        star.this is None  # plain `*`, not `users.*`
        and isinstance(
            star.parent, exp.Select
        )  # star is a direct child of the outer SELECT
        and star.parent is root  # ensure it belongs to the outer-most SELECT
        for star in root.find_all(exp.Star)
    )

    # columns written as  table.column   in the OUTER select
    referenced_qualified: Dict[str, set[str]] = defaultdict(set)
    # columns written with *no* table prefix in the OUTER select
    referenced_unqualified: set[str] = set()

    for col in root.find_all(exp.Column, bfs=False):
        if col.table:
            referenced_qualified[_clean(col.table)].add(_clean(col.name))
        else:
            referenced_unqualified.add(_clean(col.name))

    # ------------------------------------------------------------- sub-query builder
    def build_subquery(table_node: exp.Table) -> exp.Expression | None:
        tbl_clean = _clean(table_node.this)
        encrypt_cols = [c for c, need in privacy.get(tbl_clean, {}).items() if need]
        if not encrypt_cols:
            return None  # nothing to rewrite for this table

        alias_sql = table_node.alias_or_name or table_node.this
        alias_clean = _clean(str(alias_sql))

        # -------- columns to keep unchanged
        if outer_has_star:
            # Outer SELECT used *, so a simple * here is fine.
            passthrough = ["*"]
        else:
            # When there is no star in the outer query we need to keep every explicitly
            # referenced column that is NOT being encrypted. Qualified references are
            # unambiguous, but unqualified ones should be attributed to the most
            # plausible table.  The heuristic used here is:
            #   • If the column is encrypted for exactly one table, attribute it to that
            #     table.
            #   • Otherwise attribute it to the first table in the query (the usual SQL
            #     resolution order).
            #   • In every other case (multiple candidate tables), leave it out so as not # noqa
            #     to introduce accidental duplicates.

            # Build a deterministic table ordering (using their *clean* name) – this is
            # computed once and cached via closure the first time the function executes.
            nonlocal table_sequence, outer_aliases  # defined later

            passthrough_candidates: set[str] = referenced_qualified.get(
                alias_clean, set()
            ) | referenced_qualified.get(tbl_clean, set())

            # --- handle unqualified columns -----------------------------------------
            for col in referenced_unqualified:
                # Which table(s) explicitly encrypt this column?
                encrypt_tables = [t for t, rules in privacy.items() if col in rules]

                if encrypt_tables:
                    # Keep the column if the current table is the one being encrypted
                    if tbl_clean in encrypt_tables or alias_clean in encrypt_tables:
                        passthrough_candidates.add(col)
                    else:
                        # Another table encrypts this column. If there is only one
                        # table in the entire query, we can safely attribute the
                        # unqualified reference to it.
                        if len(table_sequence) == 1:
                            passthrough_candidates.add(col)
                else:
                    # No explicit encryption rule – default to the first table only
                    if table_sequence and tbl_clean == table_sequence[0]:
                        passthrough_candidates.add(col)

            passthrough = [
                col
                for col in passthrough_candidates
                if col not in encrypt_cols and col not in outer_aliases
            ]

        # -------- encrypted overrides
        overrides = [f"'ENCRYPT:'||{c} AS {c}" for c in encrypt_cols]

        select_list = passthrough + overrides
        inner_sql = f"SELECT {', '.join(select_list)} FROM {table_node.sql()}"
        return sqlglot.parse_one(f"({inner_sql}) AS {alias_sql}")

    # ----------------------------- gather helper metadata -----------------------------
    # Outer SELECT aliases (e.g., "COUNT(*) AS count") should not be propagated down
    # to inner sub-queries because they do not exist in the base tables.
    outer_aliases: set[str] = set()
    for expr in root.args.get("expressions", []):
        if isinstance(expr, exp.Alias) and expr.alias:
            outer_aliases.add(_clean(expr.alias))

    # ---------------------------------- collect table sequence for unqualified resolution # noqa
    table_sequence: list[str] = []
    for _tbl in root.find_all(exp.Table):
        table_sequence.append(_clean(_tbl.this))

    # ---------------------------------- mutate tree
    for tbl in list(root.find_all(exp.Table)):
        sub = build_subquery(tbl)
        if sub is not None:
            tbl.replace(sub)

    return root.sql()
