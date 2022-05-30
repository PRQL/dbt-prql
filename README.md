# dbt-prql

dbt-prql allows writing PRQL in dbt models, magically compiling the PRQL to SQL,
so dbt can work seamlessly.

## Examples

### Simple example

```elm
{% prql %}
from employees
filter (age | in 20..30)
{% endprql %}
```

...would appear to dbt as:

```sql
SELECT
  employees.*
FROM
  employees
WHERE
  age BETWEEN 20
  AND 30
```

### Less simple example

```elm
{% prql %}
from {{ source('salesforce', 'in_process') }}
derive expected_sales = probability * value
join {{ ref('team', 'team_sales') }} [name]
group name (
    aggregate (expected_sales)
)
{% endprql %}
```

...would appear to dbt as:

```sql
SELECT
  name,
  {{ source('salesforce', 'in_process') }}.probability * {{ source('salesforce', 'in_process') }}.value AS expected_sales
FROM
  {{ source('salesforce', 'in_process') }}
  JOIN {{ ref('team', 'team_sales') }} USING(name)
GROUP BY
  name
```

...and then dbt will compile the `source` and `ref`s to a full SQL query.

## What it does

When dbt compiles models to SQL queries:

- Any text in a dbt model between `{% prql %}` and `{% endprql %}` tags is
  compiled from PRQL to SQL.
- The PRQL complier passes through any text in a PRQL query that's surrounded by
  `{{...}}`  without modification, which allows us to pass Jinja expressions
  through to dbt. (This was added to PRQL specifically for this use-case.)
- dbt will then compile the resulting model to SQL.

There's no config needed in the dbt project; the only action is to install
`dbt-prql`.

## Installation

```sh
pip install dbt-prql
```

## Current state

Currently this is new, but fairly feature-complete. It's enthusiastically
supported — if there are any problems, please open an issue.

Note that we need to release a new `pyprql` version for this plugin to pass
jinja expressions through, which we'll do in the next couple of days.

## How does it work?

It's some dark magic, unfortunately.

dbt doesn't allow adding behavior beyond the database adapters (e.g.
`dbt-bigquery`) or jinja-only plugins (e.g. `dbt-utils`). So this library hacks
the python import system to monkeypatch dbt's jinja environment with an
additional jinja extension, which avoids the need for any changes to dbt.

This approach was discussed with the dbt team
[here](https://github.com/prql/prql/issues/375) and [here](https://github.com/prql/prql/issues/13).

Thanks to
[mtkennerly/poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning)
for the technique.

This isn't stable between dbt versions, since it relies on internal dbt APIs.
The technique is also normatively bad — it runs a few lines of code every time
the python interpreter starts — whose errors could lead to very confusing bugs
beyond the domain of the problem (though in the case of this code, it's small
and well-constructed™).

If there's ever any concern that the library might be causing a problem, just
set an environment variable `DBT_PRQL_DISABLE=1`, and this library won't
monkeypatch anything. It's also fully uninstallable with `pip uninstall
dbt-prql`.

## Roadmap

Open to ideas; at the moment it's fairly feature-complete. If we were
unconstrained in dbt functionality:

- If dbt allowed for external plugins, we'd enthusiastically move to that.
- We'd love to have this work on `.prql` files without the `{% prql %}` tags;
  but with the current approach would require quite invasive monkeypatching.
- If we could add the dialect in automatically (i.e. `prql dialect:snowflake`),
  that would save a line per model.

We may move this code to <https://github.com/prql/PyPrql> or
<https://github.com/prql/prql>. We'd prefer to keep it as its own package given
the hackery above, but there's no need for it to be its own repo.
