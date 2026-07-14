import { gql } from 'graphql-request';

import { requestAuthenticated } from './session.js';

const ME_QUERY = gql`
  query Me {
    me {
      uuid
      name
      email
      avatarUrl
      isAdmin
    }
  }
`;

/** Fetches the authenticated user's profile (name, email, avatar) using the current session token. */
export async function fetchCurrentUser(fetchImpl = globalThis.fetch) {
    const data = await requestAuthenticated(ME_QUERY, undefined, fetchImpl);
    return data.me;
}
