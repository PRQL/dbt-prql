from __future__ import annotations

import logging
import re
from collections import defaultdict

import prql_python

logger = logging.getLogger(__name__)

word_regex = r"[\w\.\-_]+"
references_regex = rf"\bdbt `?(\w+)\.({word_regex})\.({word_regex})`?"

references_type = dict[str, dict[tuple[str, str], str]]


def compile(prql: str, references: references_type):
    """
    >>> print(compile(
    ...     "from (dbt source.salesforce.in_process) | join (dbt ref.foo.bar) [id]",
    ...     references=dict(
    ...         source={('salesforce', 'in_process'): 'salesforce_schema.in_process_tbl'},
    ...         ref={('foo', 'bar'): 'foo_schema.bar_tbl'}
    ...     )
    ... ))
    SELECT
      "salesforce_schema.in_process_tbl".*,
      "foo_schema.bar_tbl".*,
      id
    FROM
      salesforce_schema.in_process_tbl
      JOIN foo_schema.bar_tbl USING(id)
    """

    # references = list_references(prql)
    prql = _hack_sentinels_of_model(prql)

    sql = prql_python.to_sql(prql)

    # Replace the sentinels with table names. This will be done by dbt-prql
    sql = replace_faux_jinja(sql, references)
    return sql


def list_references(prql):
    """
    List all references (e.g. sources / refs) in a given block.

    We need to decide:

    — What should prqlc return given `dbt source.foo.bar`, so dbt-prql can find the
      references?
        — Should it just fill in something that looks like jinja for expediancy? (We
          don't support jinja though)

    >>> references = list_references("from (dbt source.salesforce.in_process) | join (dbt ref.foo.bar)")
    >>> dict(references)
    {'source': [('salesforce', 'in_process')], 'ref': [('foo', 'bar')]}
    """

    out = defaultdict(list)
    for t, package, model in _hack_references_of_prql_query(prql):
        out[t] += [(package, model)]

    return out


def _hack_references_of_prql_query(prql) -> list[tuple[str, str, str]]:
    """
    List the references in a prql query.

    This would be implemented by prqlc.

    >>> _hack_references_of_prql_query("from (dbt source.salesforce.in_process) | join (dbt ref.foo.bar)")
    [('source', 'salesforce', 'in_process'), ('ref', 'foo', 'bar')]
    """

    return re.findall(references_regex, prql)


def _hack_sentinels_of_model(prql: str) -> str:
    """
    Replace the dbt calls with a jinja-like sentinel.

    This will be done by prqlc...

    >>> _hack_sentinels_of_model("from (dbt source.salesforce.in_process) | join (dbt ref.foo.bar) [id]")
    "from (`{{ source('salesforce', 'in_process') }}`) | join (`{{ ref('foo', 'bar') }}`) [id]"
    """
    return re.sub(references_regex, r"`{{ \1('\2', '\3') }}`", prql)


def replace_faux_jinja(sql: str, references: references_type):
    """
    >>> print(replace_faux_jinja(
    ...     "SELECT * FROM {{ source('salesforce', 'in_process') }}",
    ...     references=dict(source={('salesforce', 'in_process'): 'salesforce_schema.in_process_tbl'})
    ... ))
    SELECT * FROM salesforce_schema.in_process_tbl

    """
    for ref_type, lookups in references.items():
        for (package, table), literal in lookups.items():
            prql_new = sql.replace(
                f"{{{{ {ref_type}('{package}', '{table}') }}}}", literal
            )
            sql = prql_new

    return sql
