# Data Format


## Views

### Business objects


```json
{
    "model":{
        "name":"",
        "label":{
            "es":"",
            "en":""
        },
        "groupBy":"field",
        "field":[],
        "tags": [],
        "schema":[]
    },
    "records":[]
}
```
## Model

### Declarative search

Set `search` to `true` on a model to include it in the global search. Fields are
included only when they declare an enabled `search` object.

```json
{
    "name": "system.task",
    "search": true,
    "fields": [
        {
            "name": "title",
            "type": "string",
            "search": {
                "enabled": true,
                "text": true,
                "result": "title",
                "weight": "A"
            }
        }
    ]
}
```

- `enabled`: permits the field to participate in search.
- `text`: includes the field in textual matching.
- `result`: accepts `title`, `subtitle`, or `snippet` for result rendering.
- `weight`: accepts `A`, `B`, `C`, or `D` to describe relevance priority.

`type: html` fields may declare `text: true` too. Their markup is stripped
(both when indexed and when displayed) before matching or ranking, so results
never leak raw tags — see "Full Text Search" in
[AI_SEARCH_DESIGN.md](./AI_SEARCH_DESIGN.md) for how.

Models and fields without this configuration remain private from global search.
The complete natural-language search design is documented in
[AI_SEARCH_DESIGN.md](./AI_SEARCH_DESIGN.md).

### Name

### Label

### groupBy

### fierld


### tags

### schema

## Records

## Insights

Insights are named schemas attached to the virtual `system.insight` model. The
declarative source stores component IDs; the GraphQL response replaces them with
complete KPI, gauge, and graphic objects generated from authorized data.

```json
{
    "period": "today",
    "kpis": [],
    "gauges": [],
    "graphics": []
}
```

See [Insights Format](./INSIGHTS_FORMAT.md) for virtual-model registration,
named schema rules, component formats, GraphQL loading, and security.
