{% macro geography_key(province, city, postal_code) -%}
convert(char(32), hashbytes('MD5', lower(concat({{ province }}, '|', coalesce({{ city }}, ''), '|', coalesce({{ postal_code }}, '')))), 2)
{%- endmacro %}
