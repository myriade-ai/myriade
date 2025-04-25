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
        pass


def rewrite_sql(sql: str, columns_privacy: List[Dict[str, str]]) -> str:
    # ---------------------------------------------------------------- privacy map
    privacy: Dict[str, Dict[str, bool]] = defaultdict(dict)
    for rule in columns_privacy:
        privacy[_clean(rule["table"])][_clean(rule["column"])] = bool(
            rule.get("encryption_key")
        )

    root = parse_one(sql)

    # ---------------------------------------------------------------- outer-query scan
    outer_has_star = any(
        isinstance(star, exp.Star) and star.this is None  # plain `*`, not `users.*`
        for star in root.find_all(exp.Star, bfs=False)
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
            # Keep every explicitly referenced column that is NOT being encrypted
            passthrough = [
                col
                for col in (
                    referenced_qualified.get(alias_clean, set())
                    | referenced_qualified.get(tbl_clean, set())
                    | referenced_unqualified
                )
                if col not in encrypt_cols
            ]

        # -------- encrypted overrides
        overrides = [f"'ENCRYPT:'||{c} AS {c}" for c in encrypt_cols]

        # Remove any duplicate that would shadow an override
        passthrough = [c for c in passthrough if _clean(c) not in encrypt_cols]

        select_list = passthrough + overrides
        inner_sql = f"SELECT {', '.join(select_list)} FROM {table_node.sql()}"
        return sqlglot.parse_one(f"({inner_sql}) AS {alias_sql}")

    # ------------------------------------------------------------- mutate tree
    for tbl in list(root.find_all(exp.Table)):
        sub = build_subquery(tbl)
        if sub is not None:
            tbl.replace(sub)

    return root.sql()
