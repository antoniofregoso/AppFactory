## Insights

Each KPI, gauge, and chart must have a unique and stable `id` within the dashboard. The `id` allows updating an element without re-rendering the others; it should not change when the language, period, value, or visual position changes.

```json
{
    "period":"today|weekly|monthly|yearly|annual",
    "kpis":[
        {
            "id":"profit_margin",
            "name":{"en":"Profit margin", "es":"Margen de beneficio"},
            "value":25.5,
            "unit":{"en":"Percent", "es":"Porcentaje"},
            "trend":"up"
        }
    ],
    "gauges":[
        {
            "id":"operational_efficiency",
            "name":{"en":"Operational Efficiency", "es":"Eficiencia Operativa"},
            "value":78,
            "unit":"%",
            "max":100,
            "thresholds":{"green":80, "yellow":60, "red":0}
        }
    ],
    "graphics":[
        {
            "id":"monthly_sales",
            "type":"line",
            "title":{"en":"Monthly sales", "es":"Ventas mensuales"},
            "data":[10, 15, 21],
            "categories":{"en":["Jan", "Feb", "Mar"], "es":["Ene", "Feb", "Mar"]}
        }
    ]
}
```

### Virtual insight model

`system.insight` is the declarative container for named dashboards. It is a
virtual model: it exists in `system_models.json` and PostgreSQL metadata so that
`SystemModelSchema` can reference it, but it has no business ORM class, record
table, fields, or CRUD operations. It is read-only and excluded from search.

Insight schemas belong to `system.insight` instead of the business model that
supplies their values. This allows one dashboard to combine reusable components
from users, sales, tasks, or other authorized providers without pretending that
the dashboard itself belongs to one of those objects.

```json
{
  "name": "system.insight",
  "label": {
    "es_MX": "Paneles de información",
    "en_US": "Insights"
  },
  "search": false,
  "readonly": true,
  "group_by": false,
  "group_by_values": [],
  "tags": [],
  "fields": []
}
```

### Named insight schemas

Each dashboard is stored in `system_model_schemas.json` with a stable `name`,
`use: "insight"`, and `model: "system.insight"`. The schema selects reusable
component IDs and controls their order and layout; it does not contain calculated
values.

```json
{
  "name": "userLogs",
  "use": "insight",
  "view": {
    "period": "today",
    "layout": {
      "graphics": 2
    },
    "kpis": [
      "kpiUsersOnline",
      "kpiUsersAverageSessionTime",
      "kpiUsersActiveUsers",
      "kpiRecurringUsers"
    ],
    "gauges": [],
    "graphics": [
      "graphicUsersPerHour",
      "graphicUsersMAU"
    ]
  },
  "model": "system.insight"
}
```

The URL name is only a frontend selector:

```text
/dashboard/configuration/insights?v=userLogs
```

It is not an authorization mechanism. The frontend resolves it through a closed
allowlist, and the backend independently requires a matching registered
generator, authentication, administrator access, and company scope. Unknown
names are rejected.

The canonical GraphQL request is:

```graphql
query NamedInsight($period: String = "today") {
  systemModelView(
    model: "system.insight"
    use: insight
    name: "userLogs"
    period: $period
  ) {
    model
    records
  }
}
```

For an insight response, `model.schema` contains the hydrated dashboard and
`records` is empty. The backend replaces every configured component ID with its
complete generated object while preserving collection order.

### Adding a named dashboard

1. Add the schema under `system.insight` in `system_model_schemas.json`.
2. Use stable `kpi`, `gauge`, and `graphic` IDs that have trusted outputs.
3. Register the named generator in the backend; never load a callable from JSON.
4. Apply authorization and company scope inside every data provider.
5. Add the frontend route name to the closed insight allowlist.
6. Add a migration for databases that already exist.
7. Test schema hydration, unauthorized access, route rejection, period refresh,
   and rendering.

### Component generation rules

KPIs, gauges, and graphics are reusable named components. Dashboard schemas
reference their stable IDs and define only selection, order, period, and layout.
The backend resolves those IDs through a trusted generator and returns complete
component objects with authorized, real values.

#### Periods

- The supported periods are `today`, `weekly`, `monthly`, `yearly`, and
  `annual`.
- The default period is `today`.
- Components must be recalculated when the user changes the period.
- Period boundaries must be resolved in the configured application time zone.
- A component must return `0` or an empty data series when no records match; it
  must never substitute demonstration values.

#### Naming

Component IDs use a type prefix followed by a stable PascalCase name:

- KPI: `kpi<Name>`, for example `kpiUsersOnline`.
- Gauge: `gauge<Name>`, for example `gaugeOperationalEfficiency`.
- Graphic: `graphic<Name>`, for example `graphicUsersPerHour`.

IDs must be unique within their catalog, must not depend on language or period,
and must not change when the component is reused by another dashboard.

#### KPI format

Every KPI must contain `id`, localized `name`, calculated `value`, localized
`unit`, and `trend`. Both localized fields use an object with `en` and `es`
values. The supported trend values are `up` and `down`.

```json
{
  "id": "kpiUsersOnline",
  "name": {
    "en": "Online Users",
    "es": "Usuarios en línea"
  },
  "value": 0,
  "unit": { "en": "Users", "es": "Usuarios" },
  "trend": "up"
}
```

The numeric value in documentation examples describes the response type only.
Production values must be calculated from authorized domain records.

#### Gauge format

Every gauge must contain `id`, localized `name`, calculated `value`, `unit`,
`max`, and its display `thresholds`. Thresholds are presentation metadata;
only the value is calculated for each request.

```json
{
  "id": "gaugeOperationalEfficiency",
  "name": {
    "en": "Operational Efficiency",
    "es": "Eficiencia operativa"
  },
  "value": 0,
  "unit": "%",
  "max": 100,
  "thresholds": {
    "green": 80,
    "yellow": 60,
    "red": 0
  }
}
```

#### Graphic format

Every graphic must contain `id`, `type`, localized `title`, and data compatible
with that type. Optional properties such as `mode`, `categories`, `series`, and
`labels` must follow the corresponding visualization reference.

The user-activity heat map uses `graphicUsersPerHour`, seven localized weekday
rows, and 24 localized hour points per row. Each `y` value is calculated from
real user activity for the selected period.

The monthly active-user bar chart uses `graphicUsersMAU`, `type: "bar"`, and
`mode: "vertical"`. Its values and localized month categories are ordered
chronologically and cover the months included in the selected period.

#### User activity definitions

- `kpiUsersOnline`: distinct users with a current, non-stale online session.
- `kpiUsersAverageSessionTime`: average session duration in minutes during the
  selected period.
- `kpiUsersActiveUsers`: distinct users active during the selected period.
- `kpiRecurringUsers`: users with at least two sessions during the selected
  period.
- `graphicUsersPerHour`: distinct active users grouped by weekday and hour.
- `graphicUsersMAU`: distinct monthly active users.

The four user-activity KPIs localize their units as follows:

| KPI                              | English unit | Spanish unit |
| -------------------------------- | ------------ | ------------ |
| `kpiUsersOnline`                 | Users        | Usuarios     |
| `kpiUsersAverageSessionTime`     | Minutes      | Minutos      |
| `kpiUsersActiveUsers`            | Users        | Usuarios     |
| `kpiRecurringUsers`              | Users        | Usuarios     |

#### Data and security

- Values are generated in the backend and exposed through authenticated GraphQL
  queries.
- Authorization and company scope must be applied before aggregation.
- Declarative JSON must not contain arbitrary SQL, importable Python paths,
  secrets, or production metric values.
- The frontend may select and render components, but it must never be trusted to
  authorize an insight or calculate protected aggregates.
- Sample JSON values are examples only and must not be used as application data.

### Reactive updates

Insights data resides in `appSignal.value.insights` and is modified via `dashboardActions`. Actions accept either a partial object or a function that receives the current value.

The initial load uses `setInsights` with the full configuration sent by the backend. Subsequent refreshes use `refreshInsights`: the payload contains only data by `id` and retains the dashboard configuration (layout, names, types, units, maximums, and thresholds).

```js
dashboardActions.setInsights(initialDashboardConfig);

dashboardActions.refreshInsights({
    period: 'monthly',
    kpis: [{ id: 'profit_margin', value: 28.4, trend: 'up' }],
    gauges: [{ id: 'operational_efficiency', value: 81 }],
    graphics: [{ id: 'monthly_sales', data: [12, 18, 25] }],
});
```

You can also refresh a single indicator:

```js
import { dashboardActions } from '../store/actions';

dashboardActions.updateKpi('profit_margin', {
    value: 28.4,
    trend: 'up',
});

dashboardActions.updateGauge('operational_efficiency', (gauge) => ({
    value: gauge.value + 1,
}));

dashboardActions.updateGraphic('monthly_sales', {
    data: [12, 18, 25],
});

dashboardActions.setInsightPeriod('monthly');
```

The generic form is also available:

```js
dashboardActions.updateInsight('graphics', 'monthly_sales', {
    data: [12, 18, 25],
});
```

The patch is superficial: nested properties like `title`, `categories`,
`thresholds`, and `data` must be sent in full when modified. If the IDs
and their order are maintained, only the modified items are updated. Adding,
removing, or reordering items triggers a full Insights render.

#### Update Financial Statements (Sankey)

To update a financial statement, the entire `data` property is replaced,

including `nodes`, `edges`, and `options`:

```js
dashboardActions.updateGraphic('income_statement_sankey', {
    data: {
        nodes: updatedNodes,
        edges: updatedEdges,
        options: {
            order: updatedOrder,
        },
    },
});
```

When only the amounts in the relationships change, an update function can be used to preserve existing nodes and options and replace only the `edges`.

```js
dashboardActions.updateGraphic('income_statement_sankey', (graphic) => ({
    data: {
        ...graphic.data,
        edges: updatedEdges,
    },
}));
```

Each element of `updatedEdges` must retain the Sankey format:

```js
const updatedEdges = [
    {
        source: 'ingresos_ventas',
        target: 'total_ingresos',
        value: 925000,
    },
];
```
The update recreates only the chart whose `id` was specified; all other KPIs, gauges, and charts remain unchanged.
