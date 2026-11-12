"""Render every dbt model with stubbed Jinja and parse it as T-SQL.

This does NOT run SQL Server; it catches broken Jinja and syntax errors cheaply (also in CI).
"""
import re
from pathlib import Path

import jinja2
import pytest
import sqlglot

DBT = Path(__file__).resolve().parents[1] / "dbt"
VARS = {"atypical_min_orders": 20, "atypical_min_returned_pct": 50}


def _env():
    macros = "\n".join(p.read_text() for p in (DBT / "macros").glob("*.sql")
                       if p.name != "generate_schema_name.sql")
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    ns = env.from_string(macros + "{# #}").make_module({})
    ctx = {
        "config": lambda **k: "",
        "ref": lambda n: f"[db].[x].[{n}]",
        "source": lambda s, t: f"[db].[{s}].[{t}]",
        "var": lambda k: VARS[k],
    }
    ctx.update({k: getattr(ns, k) for k in dir(ns) if not k.startswith("_")})
    return env, ctx


def _render(path: Path) -> str:
    env, ctx = _env()
    return env.from_string(path.read_text()).render(**ctx)


FILES = sorted((DBT / "models").rglob("*.sql")) + sorted((DBT / "tests").glob("*.sql"))


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_model_parses_as_tsql(path):
    sql = _render(path)
    assert "{{" not in sql and "{%" not in sql
    parsed = sqlglot.parse(sql, read="tsql")
    assert parsed and parsed[0] is not None
