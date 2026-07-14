import { ClientError, gql, GraphQLClient } from 'graphql-request';

const GRAPHQL_ENDPOINT = new URL(
    import.meta.env.VITE_GRAPHQL_ENDPOINT ?? '/graphql',
    globalThis.location?.origin ?? 'http://localhost',
).toString();
const REFRESH_CSRF_COOKIE_NAME = import.meta.env.VITE_REFRESH_CSRF_COOKIE_NAME ?? 'refresh_csrf';

const LOGIN_MUTATION = gql`
  mutation Login($login: LoginInput!) {
    login(login: $login) {
      email
      token
      accessToken
    }
  }
`;

const REFRESH_SESSION_MUTATION = gql`
  mutation RefreshSession {
    refreshSession(refresh: {}) {
      email
      token
      accessToken
    }
  }
`;

const LOGOUT_MUTATION = gql`
  mutation Logout {
    logout(logout: {})
  }
`;

export class AuthenticationError extends Error {
    constructor(message, code = 'AUTHENTICATION_FAILED', options) {
        super(message, options);
        this.name = 'AuthenticationError';
        this.code = code;
    }
}

function isCredentialError(error) {
    return error.response.errors?.some(({ message = '', extensions = {} }) => (
        extensions.error_code === 'AUTHENTICATION_ERROR'
        || /invalid (?:credentials|email or password)/i.test(message)
    ));
}

function readCookie(name) {
    const cookies = globalThis.document?.cookie ?? '';
    return cookies
        .split(';')
        .map((cookie) => cookie.trim())
        .find((cookie) => cookie.startsWith(`${name}=`))
        ?.slice(name.length + 1) ?? '';
}

function csrfHeaders() {
    const csrfToken = readCookie(REFRESH_CSRF_COOKIE_NAME);
    return csrfToken ? { 'X-CSRF-Token': decodeURIComponent(csrfToken) } : {};
}

export async function authenticate(email, password, fetchImpl = globalThis.fetch) {
    const client = new GraphQLClient(GRAPHQL_ENDPOINT, {
        credentials: 'include',
        fetch: fetchImpl,
    });

    try {
        const data = await client.request(LOGIN_MUTATION, {
            login: { email, password },
        });

        if (!data.login?.token && !data.login?.accessToken) {
            throw new AuthenticationError('Invalid email or password');
        }

        return data.login;
    } catch (error) {
        if (error instanceof AuthenticationError) throw error;
        if (error instanceof ClientError && isCredentialError(error)) {
            throw new AuthenticationError('Invalid email or password');
        }
        if (error instanceof ClientError) {
            throw new AuthenticationError(
                'Authentication service unavailable',
                'SERVICE_UNAVAILABLE',
                { cause: error },
            );
        }
        throw new AuthenticationError(
            'Unable to reach the authentication service',
            'NETWORK_ERROR',
            { cause: error },
        );
    }
}

export async function refreshSession(fetchImpl = globalThis.fetch) {
    const client = new GraphQLClient(GRAPHQL_ENDPOINT, {
        credentials: 'include',
        fetch: fetchImpl,
        headers: csrfHeaders,
    });

    try {
        const data = await client.request(REFRESH_SESSION_MUTATION);

        if (!data.refreshSession?.token && !data.refreshSession?.accessToken) {
            throw new AuthenticationError('Invalid refresh token');
        }

        return data.refreshSession;
    } catch (error) {
        if (error instanceof AuthenticationError) throw error;
        if (error instanceof ClientError) {
            throw new AuthenticationError(
                'Session refresh failed',
                'SESSION_REFRESH_FAILED',
                { cause: error },
            );
        }
        throw new AuthenticationError(
            'Unable to reach the authentication service',
            'NETWORK_ERROR',
            { cause: error },
        );
    }
}

export async function logout(fetchImpl = globalThis.fetch) {
    const client = new GraphQLClient(GRAPHQL_ENDPOINT, {
        credentials: 'include',
        fetch: fetchImpl,
        headers: csrfHeaders,
    });

    try {
        const data = await client.request(LOGOUT_MUTATION);
        return Boolean(data.logout);
    } catch (error) {
        if (error instanceof ClientError) return false;
        throw error;
    }
}
