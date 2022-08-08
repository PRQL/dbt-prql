{% prql %}
from in_process = {{ source('salesforce', 'in_process') }}
derive expected_sales = probability * value
join {{ source('team', 'team_sales') }} [name]
group name (
  aggregate (sum expected_sales)
)
{% endprql %}