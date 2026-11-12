{# Month name in Spanish ('noviembre') -> month number. Returns NULL when the text is not a month. #}
{% macro spanish_month_number(col) %}
case lower(ltrim(rtrim({{ col }})))
    {%- for name, number in [('enero', 1), ('febrero', 2), ('marzo', 3), ('abril', 4), ('mayo', 5), ('junio', 6),
                             ('julio', 7), ('agosto', 8), ('septiembre', 9), ('setiembre', 9), ('octubre', 10),
                             ('noviembre', 11), ('diciembre', 12)] %}
    when '{{ name }}' then {{ number }}
    {%- endfor %}
end
{% endmacro %}
