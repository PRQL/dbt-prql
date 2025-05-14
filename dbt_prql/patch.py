from jinja2.ext import Extension
from jinja2.parser import Parser


class PrqlExtension(Extension):
    tags = {"prql"}

    def parse(self, parser: Parser):
        import logging

        from jinja2 import nodes
        from jinja2.nodes import Const

        logger = logging.getLogger(__name__)

        line_number = next(parser.stream).lineno
        prql_jinja = parser.parse_statements(["name:endprql"], drop_needle=True)
        logger.info(f"Parsing statement:\n{prql_jinja}")
        return nodes.CallBlock(
            self.call_method("_to_sql", [Const("")]), [], [], prql_jinja
        ).set_lineno(line_number)

    def _to_sql(self, args, caller):
        _ = args
        import logging

        import prql_python

        logger = logging.getLogger(__name__)

        prql = caller()
        logger.info(f"Parsing PRQL:\n{prql}")
        sql = prql_python.compile(prql)
        output = f"""
-- SQL created from PRQL. Original PRQL:
{chr(10).join(f'-- {line}' for line in prql.splitlines())}

{sql}
"""
        logger.info(f"Parsed into SQL:\n{sql}")
        return output


def patch_dbt_environment() -> None:
    import os

    if os.environ.get("DBT_PRQL_DISABLE"):
        # See below for why we don't log this.
        return

    import functools
    import logging

    logger = logging.getLogger(__name__)

    try:
        from dbt_common.clients import jinja
    except ImportError:
        # Don't log this as discussed below
        pass

    log_level = os.environ.get("DBT_PRQL_LOG_LEVEL", "")
    if log_level != "":
        logging.basicConfig()
        logger.setLevel(log_level)
        logger.warning(
            f"Setting PRQL log level to {log_level}. Please note that logging anything "
            "from this module can affect the reliability of some libraries which "
            "rely on a clean stderr. This includes dbt-bigquery. If you have any issues, "
            "disable logging by removing the `DBT_PRQL_LOG_LEVEL` env var. I recognize the "
            "absurdity of that statement, but there's not much we can do from here."
        )

    logger.debug("Getting environment function from dbt")
    jinja._get_environment = jinja.get_environment

    def add_prql_extension(func):
        if getattr(func, "status", None) == "patched":
            logger.debug(f"Already patched {func.__qualname__}")
            return func

        @functools.wraps(func)
        def with_prql_extension(*args, **kwargs):
            env = func(*args, **kwargs)
            env.add_extension(PrqlExtension)
            return env

        with_prql_extension.status = "patched"
        logger.info(f"Patched {func.__qualname__}")

        return with_prql_extension

    env_with_prql = add_prql_extension(jinja._get_environment)

    jinja.get_environment = env_with_prql

    if os.environ.get("DBT_PRQL_TEST"):
        test_jinja_parse()


def test_jinja_parse() -> None:
    import logging

    from dbt.clients.jinja import get_environment

    logger = logging.getLogger(__name__)

    template = get_environment().from_string(
        """
    {% prql %}
    from employees
    filter (age | in 5..10)
    {% endprql %}
    """
    )
    logger.info(f"Tested PRQL parsing: {template.render()}")
