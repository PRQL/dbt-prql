# dbt-prql

dbt-prql allows writing PRQL in dbt models.

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

...and then dbt will compile the `source` and `ref`s to the full SQL query.

## What it does

While `dbt-prql` is installed, when dbt compiles models to SQL queries:

- Any text in a dbt model between `{% prql %}` and `{% endprql %}` tags will be
  compiled from PRQL to SQL.
- In an effort to support this use-case, the PRQL complier passes through any
  text in a PRQL query that's surrounded by `{{...}}`  without modification,
  which allows us to pass Jinja expressions through to dbt.
- dbt will then compile the resulting model to SQL, like it always does.

## Installation

```sh
pip install dbt-prql
```

## Current state

Currently this in an early state. But it's enthusiastically supported — if there
are any problems, please open an issue.

Note that we need to release a new `pyprql` version for this to pass jinja
expressions through, which we'll do in the next couple of days.

## Is this magic?

It's much worse.

Unfortunately, it's not possible to add behavior to dbt beyond the database
adapters (e.g. `dbt-bigquery`) or jinja-only plugins (e.g. `dbt-utils`). So this
library hacks the python import system to monkeypatch dbt's jinja environment
with an additional jinja extension, which avoids the need for any changes to
dbt.

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

Open to ideas; at the moment it's fairly feature-complete. If dbt allowed for
external plugins, we'd enthusiastically move to that. We'd also love to have
this work on `.prql` files without the `{% prql %}` tags; with the current
approach would require quite invasive monkeypatching.
