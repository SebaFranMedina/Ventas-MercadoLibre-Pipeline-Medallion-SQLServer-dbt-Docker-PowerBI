{# Maps the free-text Mercado Libre order status to a small set of categories.
   `col` must be an expression that is already lower-cased. Order of the WHEN branches matters. #}
{% macro status_category(col) %}
case
    when {{ col }} is null then 'Other'
    when {{ col }} like 'paquete de%' then 'Package header'
    when {{ col }} like '%cancelad%' or {{ col }} like 'cancelaste%' then 'Cancelled'
    when {{ col }} like '%devoluci%rechazada%' then 'Other'
    when {{ col }} like '%no se pudo entregar%' or {{ col }} like '%devolveremos el paquete%'
         or {{ col }} like '%no entregado%' or {{ col }} like 'tu paquete se devolvi%'
         or {{ col }} like 'rechazada por el comprador%' then 'Failed delivery'
    when {{ col }} like '%cambio%' then 'Exchange'
    when {{ col }} like '%devoluci%' or {{ col }} like 'devuelto%' or {{ col }} like '%reembols%'
         or {{ col }} like '%devolvieron%' or {{ col }} like '%producto devuelto%' then 'Returned'
    when {{ col }} like '%reclamo%' or {{ col }} like '%mediaci%' then 'Claim resolved'
    when {{ col }} like 'entregado%' or {{ col }} like 'venta entregada%'
         or {{ col }} like 'venta concretada%' then 'Delivered'
    when {{ col }} like '%en camino%' or {{ col }} like 'en punto de retiro%' then 'In transit'
    when {{ col }} like 'etiqueta%' or {{ col }} like 'listo para%' or {{ col }} like 'procesando%'
         or {{ col }} like '%demorado%' or {{ col }} like 'despacharemos%' or {{ col }} like '%colecta%'
         or {{ col }} like '%reprogramado%' then 'Preparing'
    else 'Other'
end
{% endmacro %}
