#!/usr/bin/env bash

export PATH=$PYTHON_PATH_:$PATH
# Don't use the patching during the installs.
export DBT_PRQL_DISABLE=1
export DBT_PRQL_LOG_LEVEL=10
cd ${test_dbt_project}
pip install ../../dbt-prql
dbt clean
dbt deps
cd ~/workspace/dbt-prql/
echo "🟢"
