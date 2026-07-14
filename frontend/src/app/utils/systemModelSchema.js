/**
 * Unwraps a SystemModel GraphQL response into the flat, declarative "model"
 * shape documented in Doc/VIEWS_FORMAT.md (label, groupBy, status, tags,
 * schema).
 */
export function mapSystemModelToViewModel(systemModel, use = 'default') {
    const schemaEntry = systemModel?.schemas?.find((schema) => schema.use === use);
    if (!schemaEntry) {
        throw new Error(`Model "${systemModel?.name}" has no schema for use "${use}"`);
    }
    return {
        name: systemModel.name,
        ...schemaEntry.view,
    };
}
