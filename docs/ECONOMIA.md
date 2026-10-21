# Economía y balance

## Números

- Saldo en **pesos enteros, int64**: sin errores de redondeo acumulados. Las
  fracciones (precios con centavos, multiplicadores) se acumulan en un `carry` por
  negocio y se acreditan al llegar a $1.
- **Tope de seguridad: $1e18** (`balance.max_money`). `earn()` satura, los costos que
  superan el rango se consideran inalcanzables. Con el contenido actual una partida
  normal queda varios órdenes por debajo (la distribuidora a nivel 100 es el techo).
- Si en el futuro el contenido necesita más de 1e18: migrar `Economy` a un número
  mantisa+exponente, subir `Migrations.CURRENT_VERSION` y convertir los strings del
  guardado. La lógica nunca lee textos de la UI (`Fmt` es sólo presentación).
- Formato: `$950`, `$12,5 mil`, `$3,4 M`, `$2,1 mil M`, `$7 B` (billón), `mil B`, `T`.
  Los saldos redondean hacia abajo y los precios hacia arriba.

## Fórmulas (todas parametrizadas en `data/`)

- Clientes por ciclo = nivel × (1 + mejoras de unidades).
- Ciclo = ciclo_base / (hitos × (1 + mejoras + empleados) × eventos), mínimo 0,1 s.
  Hitos: nivel 25 x2, 50 x2, 75 x1,5, 100 x2 (el 10 y el 50/100 suman puestos de empleado).
- Precio = base × (1 + mejoras + empleados + directores) × zona × eventos × prestigio × turbo × inflación.
- Costo de mercadería = base × max(0,5; 1 − proveedores) × eventos × inflación.
- Capacidad de stock = clientes × participación × max(25 ciclos; 40 s) × (1 + mejoras).
- Costo de nivel = base × crecimiento^(nivel−1) × (1 − contactos). Crecimiento 1,15 (puesto) a 1,10.
- Desbloqueos: kiosco $2.000, luego ×20 por negocio. Ganancia por nivel ×5 por negocio.
- Sueldos y contrataciones escalan con la "escala" del negocio (ganancia/s a nivel 10).
- Patrimonio = efectivo + 50 % de lo invertido por negocio + stock a costo + 50 % de zonas.

## Simulación automatizada (tests/progression/test_balance.gd)

Bot "jugador razonable" (mantiene apretado VENDER, repone, ahorra para contratar y abrir
negocios, compra lo de mejor retorno). Resultado de 4 h simuladas:

| Hito | Tiempo del bot |
|---|---|
| Primera mejora / primer empleado | 45 s / 1 min 14 s |
| Kiosco / puesto de comida / lavadero | 1:31 / 2:19 / 4:08 |
| Almacén / cafetería | 9 min / 30 min |
| Etapa 5 (prestigio disponible) | 1 h 20 min |
| Restaurante | 1 h 58 min |

Un jugador humano va más lento (estimado ×2–3). El test verifica ventanas mínimas y
máximas para detectar regresiones en ambos sentidos.

### Problemas que encontró la simulación (y se corrigieron)

1. **Atasco permanente**: gastar todo en niveles con stock en cero dejaba sin forma de
   volver a vender. Ahora la reposición parcial acepta cualquier monto y, si el puesto
   queda en $0 y sin mercadería, el mayorista fía stock.
2. **Crecimiento explosivo** (etapa 5 en 3 min): crecimiento de costo 1,07 y hitos ×24.
3. **Cascada de recompensas**: premios "X segundos de ingreso" en misiones se
   alimentaban entre sí (cobrar → comprar → completar otra misión). Misiones, desafíos y
   logros ahora pagan montos fijos; lo proporcional queda para lo diario.
4. **Turbos apilables** hasta x3: ahora no se apilan (uno nuevo extiende la duración).

## Inflación ficticia (opcional)

Desactivada por defecto (Ajustes → Inflación ficticia). Cada 10 min se anuncia con 60 s
de aviso una suba de 8 % en mercadería; los precios acompañan 90 s después; índice
máximo ×4. Costos de niveles/mejoras no cambian, así el dinero ahorrado no pierde valor.
Se probó en `test_inflation_optional_and_bounded`. Para dejarla activa por defecto:
`SettingsData.DEFAULTS["inflation"] = true`.
