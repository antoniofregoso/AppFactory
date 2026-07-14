import { ClientError, gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';

const SYSTEM_MODEL_VIEW_QUERY = gql`
  query SystemModelView($model: String!, $use: SystemModelSchemaUse!, $name: String!, $period: String) {
    systemModelView(model: $model, use: $use, name: $name, period: $period) {
      model
      records
    }
  }
`;

const SYSTEM_MODEL_BY_NAME_QUERY = gql`
  query SystemModelByName($name: String!) {
    systemModelByName(name: $name) {
      uuid
      name
    }
  }
`;

const SYSTEM_SEARCH_QUERY = gql`
  query SystemSearch($input: SystemSearchInput!) {
    systemSearch(input: $input) {
      requestId
      status
      interpretedQuery
      needsClarification
      clarificationQuestion
      results {
        model
        modelLabel
        uuid
        title
        subtitle
        snippet
        url
        score
      }
      errors {
        code
        message
        model
        field
      }
    }
  }
`;

const UPDATE_SYSTEM_MODEL_RECORD_MUTATION = gql`
  mutation UpdateSystemModelRecord($model: String!, $recordUuid: UUID!, $values: JSON!) {
    updateSystemModelRecord(model: $model, recordUuid: $recordUuid, values: $values)
  }
`;

const CREATE_SYSTEM_MODEL_RECORD_MUTATION = gql`
  mutation CreateSystemModelRecord($model: String!, $values: JSON!) {
    createSystemModelRecord(model: $model, values: $values)
  }
`;

const DELETE_SYSTEM_MODEL_RECORD_MUTATION = gql`
  mutation DeleteSystemModelRecord($model: String!, $recordUuid: UUID!) {
    deleteSystemModelRecord(model: $model, recordUuid: $recordUuid)
  }
`;

export class SystemModelError extends Error {
    constructor(message, options) {
        super(message, options);
        this.name = 'SystemModelError';
    }
}

/**
 * Fetches the declarative view payload for a model, including metadata,
 * schema, and records.
 */
export async function fetchSystemModelView(
    { model, use = 'view', name = 'default', period = null },
    fetchImpl = globalThis.fetch,
) {
    try {
        const data = await requestAuthenticated(
            SYSTEM_MODEL_VIEW_QUERY,
            { model, use, name, period },
            fetchImpl,
        );
        return data.systemModelView;
    } catch (error) {
        if (error instanceof ClientError && error.response.errors?.length) {
            throw new SystemModelError(`View "${model}/${use}/${name}" was not found`, { cause: error });
        }
        throw new SystemModelError(`Unable to load the view for model "${model}"`, { cause: error });
    }
}

export async function fetchSystemModelByName(name, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        SYSTEM_MODEL_BY_NAME_QUERY,
        { name },
        fetchImpl,
    );
    return data.systemModelByName;
}

export async function searchSystemModels({
    query,
    lang = 'es',
    limit = 20,
    mode = 'AUTO',
    model = null,
    originalQuery = null,
    clarificationAnswer = null,
}, fetchImpl = globalThis.fetch) {
    const input = { query, lang, limit, mode };
    if (model) input.model = model;
    if (originalQuery) input.originalQuery = originalQuery;
    if (clarificationAnswer) input.clarificationAnswer = clarificationAnswer;
    const data = await requestAuthenticated(SYSTEM_SEARCH_QUERY, { input }, fetchImpl);
    return data.systemSearch;
}

export async function updateSystemModelRecord({ model, recordUuid, values }, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        UPDATE_SYSTEM_MODEL_RECORD_MUTATION,
        { model, recordUuid, values },
        fetchImpl,
    );
    return data.updateSystemModelRecord;
}

export async function createSystemModelRecord({ model, values }, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        CREATE_SYSTEM_MODEL_RECORD_MUTATION,
        { model, values },
        fetchImpl,
    );
    return data.createSystemModelRecord;
}

export async function deleteSystemModelRecord({ model, recordUuid }, fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(
        DELETE_SYSTEM_MODEL_RECORD_MUTATION,
        { model, recordUuid },
        fetchImpl,
    );
    return data.deleteSystemModelRecord;
}
