# Sankey

```json
 {
      "id": "balance_sheet_sankey",
      "type": "sankey",
      "title": {
          "en": "Balance Sheet",
          "es": "Balance General"
      },
      "data": {
        "nodes":[],
         "edges": []
      },
      "language": "es",
      "options": {}

  }
```

## i18n

```json
{
  "language": "es"
}
```

```json
{ "id": "efectivo_entrante", "title": "Efectivo Entrante Total", "title_en": "Total Cash Inflow" }
```

## Cash Flow

```json
        {
            "id": "cash_flow_sankey",
            "type": "sankey",
            "title": {
                "en": "Cash Flow",
                "es": "Flujo de efectivo"
            },
            "data": {
    "nodes": [
        { "id": "ingresos_ventas", "title": "Ingresos por Ventas", "title_en": "Sales Revenue" },
        { "id": "otros_ingresos", "title": "Otros Ingresos", "title_en": "Other Income" },
        { "id": "prestamos", "title": "Préstamos Recibidos", "title_en": "Loans Received" },
        
        { "id": "efectivo_entrante", "title": "Efectivo Entrante Total", "title_en": "Total Cash Inflow" },
        
        { "id": "costo_ventas", "title": "Costo de Ventas", "title_en": "Cost of Goods Sold" },
        { "id": "sueldos", "title": "Sueldos y Salarios", "title_en": "Salaries and Wages" },
        { "id": "alquiler_utilidades", "title": "Alquiler y Utilidades", "title_en": "Rent and Utilities" },
        { "id": "marketing_admin", "title": "Marketing y Gastos Administrativos", "title_en": "Marketing & Admin Expenses" },
        { "id": "impuestos", "title": "Impuestos", "title_en": "Taxes" },
        { "id": "capex", "title": "Inversiones en Activos (CapEx)", "title_en": "Capital Expenditures (CapEx)" },
        { "id": "pago_deuda", "title": "Pago de Deuda", "title_en": "Debt Payments" },
        { "id": "dividendos", "title": "Dividendos", "title_en": "Dividends" },
        
        { "id": "efectivo_neto", "title": "Efectivo Neto Final", "title_en": "Net Cash Position" }
    ],
    "edges": [
    { "source": "ingresos_ventas", "target": "efectivo_entrante", "value": 850000 },
    { "source": "otros_ingresos", "target": "efectivo_entrante", "value": 45000 },
    { "source": "prestamos", "target": "efectivo_entrante", "value": 120000 },
    
    { "source": "efectivo_entrante", "target": "costo_ventas", "value": 420000 },
    { "source": "efectivo_entrante", "target": "sueldos", "value": 210000 },
    { "source": "efectivo_entrante", "target": "alquiler_utilidades", "value": 85000 },
    { "source": "efectivo_entrante", "target": "marketing_admin", "value": 65000 },
    { "source": "efectivo_entrante", "target": "impuestos", "value": 95000 },
    { "source": "efectivo_entrante", "target": "capex", "value": 110000 },
    { "source": "efectivo_entrante", "target": "pago_deuda", "value": 45000 },
    { "source": "efectivo_entrante", "target": "dividendos", "value": 35000 },
    
    { "source": "efectivo_entrante", "target": "efectivo_neto", "value": 105000 }
    ],
    "options": {  
    "order": [
        [["ingresos_ventas", "otros_ingresos", "prestamos"]],
        [["efectivo_entrante"]],
        [["costo_ventas", "sueldos", "alquiler_utilidades", "marketing_admin", "impuestos", "capex", "pago_deuda", "dividendos"]],
        [["efectivo_neto"]]
            ]
        }
        }   
                }
```

![Cash Flow](./images/cash_flow.png)

## Income Statement


```json
{
            "id": "income_statement_sankey",
            "type": "sankey",
            "title": {
                "en": "Income Statement",
                "es": "Estado de Resultados"
            }, 
            "data":{
  "nodes": [
    { "id": "ingresos_ventas", "title": "Ingresos por Ventas", "title_en": "Sales Revenue" },
    { "id": "otros_ingresos", "title": "Otros Ingresos", "title_en": "Other Income" },
    
    { "id": "total_ingresos", "title": "Total Ingresos", "title_en": "Total Revenue" },
    
    { "id": "costo_ventas", "title": "Costo de Ventas", "title_en": "Cost of Goods Sold" },
    { "id": "utilidad_bruta", "title": "Utilidad Bruta", "title_en": "Gross Profit" },
    
    { "id": "sueldos", "title": "Sueldos y Salarios", "title_en": "Salaries and Wages" },
    { "id": "alquiler_utilidades", "title": "Alquiler y Utilidades", "title_en": "Rent and Utilities" },
    { "id": "marketing_admin", "title": "Marketing y Gastos Administrativos", "title_en": "Marketing & Admin Expenses" },
    { "id": "depreciacion", "title": "Depreciación y Amortización", "title_en": "Depreciation & Amortization" },
    { "id": "otros_gastos_operativos", "title": "Otros Gastos Operativos", "title_en": "Other Operating Expenses" },
    
    { "id": "total_gastos_operativos", "title": "Total Gastos Operativos", "title_en": "Total Operating Expenses" },
    { "id": "utilidad_operativa", "title": "Utilidad Operativa (EBIT)", "title_en": "Operating Profit (EBIT)" },
    
    { "id": "gastos_financieros", "title": "Gastos Financieros", "title_en": "Financial Expenses" },
    { "id": "otros_gastos_no_operativos", "title": "Otros Gastos No Operativos", "title_en": "Other Non-Operating Expenses" },
    
    { "id": "utilidad_antes_impuestos", "title": "Utilidad Antes de Impuestos", "title_en": "Profit Before Tax" },
    { "id": "impuestos", "title": "Impuestos", "title_en": "Income Tax" },
    
    { "id": "utilidad_neta", "title": "Utilidad Neta", "title_en": "Net Income" }
  ],
  "edges": [
    { "source": "ingresos_ventas", "target": "total_ingresos", "value": 850000 },
    { "source": "otros_ingresos", "target": "total_ingresos", "value": 45000 },
    
    { "source": "total_ingresos", "target": "costo_ventas", "value": 420000 },
    { "source": "total_ingresos", "target": "utilidad_bruta", "value": 475000 },
    
    { "source": "utilidad_bruta", "target": "sueldos", "value": 210000 },
    { "source": "utilidad_bruta", "target": "alquiler_utilidades", "value": 85000 },
    { "source": "utilidad_bruta", "target": "marketing_admin", "value": 65000 },
    { "source": "utilidad_bruta", "target": "depreciacion", "value": 35000 },
    { "source": "utilidad_bruta", "target": "otros_gastos_operativos", "value": 25000 },
    { "source": "utilidad_bruta", "target": "total_gastos_operativos", "value": 420000 },
    { "source": "utilidad_bruta", "target": "utilidad_operativa", "value": 55000 },
    
    { "source": "utilidad_operativa", "target": "gastos_financieros", "value": 28000 },
    { "source": "utilidad_operativa", "target": "otros_gastos_no_operativos", "value": 8000 },
    { "source": "utilidad_operativa", "target": "utilidad_antes_impuestos", "value": 19000 },
    
    { "source": "utilidad_antes_impuestos", "target": "impuestos", "value": 9500 },
    { "source": "utilidad_antes_impuestos", "target": "utilidad_neta", "value": 9500 }
  ],
  "language": "es",
  "options": {
    "order": [
      [["ingresos_ventas", "otros_ingresos"]],
      [["total_ingresos"]],
      [["costo_ventas", "utilidad_bruta"]],
      [["sueldos", "alquiler_utilidades", "marketing_admin", "depreciacion", "otros_gastos_operativos", "total_gastos_operativos", "utilidad_operativa"]],
      [["gastos_financieros", "otros_gastos_no_operativos", "utilidad_antes_impuestos"]],
      [["impuestos", "utilidad_neta"]]
    ]
  }
}
            }

```

![Income Statement](./images/income_statament.png)

### Balance Sheet

```json
    {
            "id": "balance_sheet_sankey",
            "type": "sankey",
            "title": {
                "en": "Balance Sheet",
                "es": "Balance General"
            },
            "data": {
  "nodes": [
    { "id": "efectivo", "title": "Efectivo y Equivalentes", "title_en": "Cash and Equivalents" },
    { "id": "cuentas_por_cobrar", "title": "Cuentas por Cobrar", "title_en": "Accounts Receivable" },
    { "id": "inventarios", "title": "Inventarios", "title_en": "Inventories" },
    { "id": "otros_activos_corrientes", "title": "Otros Activos Corrientes", "title_en": "Other Current Assets" },
    
    { "id": "total_activos_corrientes", "title": "Total Activos Corrientes", "title_en": "Total Current Assets" },
    
    { "id": "propiedad_equipo", "title": "Propiedad, Planta y Equipo", "title_en": "Property, Plant & Equipment" },
    { "id": "activos_intangibles", "title": "Activos Intangibles", "title_en": "Intangible Assets" },
    { "id": "otros_activos_no_corrientes", "title": "Otros Activos No Corrientes", "title_en": "Other Non-Current Assets" },
    
    { "id": "total_activos_no_corrientes", "title": "Total Activos No Corrientes", "title_en": "Total Non-Current Assets" },
    { "id": "total_activos", "title": "Total Activos", "title_en": "Total Assets" },
    
    { "id": "cuentas_por_pagar", "title": "Cuentas por Pagar", "title_en": "Accounts Payable" },
    { "id": "prestamos_corto_plazo", "title": "Préstamos a Corto Plazo", "title_en": "Short-term Debt" },
    { "id": "otros_pasivos_corrientes", "title": "Otros Pasivos Corrientes", "title_en": "Other Current Liabilities" },
    
    { "id": "total_pasivos_corrientes", "title": "Total Pasivos Corrientes", "title_en": "Total Current Liabilities" },
    
    { "id": "prestamos_largo_plazo", "title": "Préstamos a Largo Plazo", "title_en": "Long-term Debt" },
    { "id": "otros_pasivos_no_corrientes", "title": "Otros Pasivos No Corrientes", "title_en": "Other Non-Current Liabilities" },
    
    { "id": "total_pasivos_no_corrientes", "title": "Total Pasivos No Corrientes", "title_en": "Total Non-Current Liabilities" },
    { "id": "total_pasivos", "title": "Total Pasivos", "title_en": "Total Liabilities" },
    
    { "id": "capital_social", "title": "Capital Social", "title_en": "Share Capital" },
    { "id": "utilidades_retenidas", "title": "Utilidades Retenidas", "title_en": "Retained Earnings" },
    { "id": "total_patrimonio", "title": "Total Patrimonio Neto", "title_en": "Total Equity" },
    
    { "id": "total_pasivos_patrimonio", "title": "Total Pasivos + Patrimonio", "title_en": "Total Liabilities + Equity" }
  ],
  "edges": [
    { "source": "efectivo", "target": "total_activos_corrientes", "value": 185000 },
    { "source": "cuentas_por_cobrar", "target": "total_activos_corrientes", "value": 245000 },
    { "source": "inventarios", "target": "total_activos_corrientes", "value": 320000 },
    { "source": "otros_activos_corrientes", "target": "total_activos_corrientes", "value": 65000 },
    
    { "source": "total_activos_corrientes", "target": "total_activos", "value": 815000 },
    
    { "source": "propiedad_equipo", "target": "total_activos_no_corrientes", "value": 680000 },
    { "source": "activos_intangibles", "target": "total_activos_no_corrientes", "value": 95000 },
    { "source": "otros_activos_no_corrientes", "target": "total_activos_no_corrientes", "value": 45000 },
    
    { "source": "total_activos_no_corrientes", "target": "total_activos", "value": 820000 },
    
    { "source": "total_activos", "target": "total_pasivos_patrimonio", "value": 1635000 },
    
    { "source": "cuentas_por_pagar", "target": "total_pasivos_corrientes", "value": 185000 },
    { "source": "prestamos_corto_plazo", "target": "total_pasivos_corrientes", "value": 95000 },
    { "source": "otros_pasivos_corrientes", "target": "total_pasivos_corrientes", "value": 65000 },
    
    { "source": "total_pasivos_corrientes", "target": "total_pasivos", "value": 345000 },
    
    { "source": "prestamos_largo_plazo", "target": "total_pasivos_no_corrientes", "value": 420000 },
    { "source": "otros_pasivos_no_corrientes", "target": "total_pasivos_no_corrientes", "value": 85000 },
    
    { "source": "total_pasivos_no_corrientes", "target": "total_pasivos", "value": 505000 },
    
    { "source": "total_pasivos", "target": "total_pasivos_patrimonio", "value": 850000 },
    
    { "source": "capital_social", "target": "total_patrimonio", "value": 500000 },
    { "source": "utilidades_retenidas", "target": "total_patrimonio", "value": 285000 },
    
    { "source": "total_patrimonio", "target": "total_pasivos_patrimonio", "value": 785000 }
  ],
  "language": "es",
  "options": {
    "order": [
      [["efectivo", "cuentas_por_cobrar", "inventarios", "otros_activos_corrientes"]],
      [["total_activos_corrientes"]],
      [["propiedad_equipo", "activos_intangibles", "otros_activos_no_corrientes"]],
      [["total_activos_no_corrientes", "total_activos"]],
      [["cuentas_por_pagar", "prestamos_corto_plazo", "otros_pasivos_corrientes"]],
      [["total_pasivos_corrientes"]],
      [["prestamos_largo_plazo", "otros_pasivos_no_corrientes"]],
      [["total_pasivos_no_corrientes", "total_pasivos"]],
      [["capital_social", "utilidades_retenidas"]],
      [["total_patrimonio"]],
      [["total_pasivos_patrimonio"]]
    ]
  }
}
    }

```

![Balance Sheet](./images/balance_sheet.png)

