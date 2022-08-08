# dbt-prql tests

These are some early integration tests. Currently they're run from the
command-line with `task`:

```
task test
```

Some severe caveats:

- Because of <https://github.com/prql/prql/issues/918>, the postgres tests
  demonstrate that this doesn't currently work with postgres.
- The tests may fail _after_ passing the compilation, depending on whether
  there's a valid Google Cloud auth setup. Unfortunately it doesn't seem
  possible to use standard dbt commands without querying a DB. So we may need to
  work with [dbt's test
  fixtures](https://github.com/dbt-labs/dbt-core/tree/main/tests); at first
  glance they don't seem well-described.
