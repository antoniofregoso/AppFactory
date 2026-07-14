# Session Renewal

The backend uses short-lived access tokens and rotating refresh tokens.

## Configuration

```env
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_ABSOLUTE_EXPIRE_DAYS=30
```

- `ACCESS_TOKEN_EXPIRE_MINUTES`: lifetime of the JWT sent in the `Authorization` header.
- `REFRESH_TOKEN_EXPIRE_DAYS`: inactivity window for a refresh token.
- `SESSION_ABSOLUTE_EXPIRE_DAYS`: maximum total lifetime of a session, even if refresh tokens keep rotating.

## Login

The `login` mutation returns:

```graphql
mutation Login($login: LoginInput!) {
  login(login: $login) {
    email
    token
    accessToken
    refreshToken
  }
}
```

`token` is kept as a backwards-compatible alias for `accessToken`.

On login, the backend stores only an HMAC-SHA256 hash of the refresh token in
PostgreSQL. The raw refresh token is returned once to the client and is never
stored in plain text.

## Stored Session Data

Refresh token state is stored in `user_sessions`:

- `user_id`: owner of the session.
- `refresh_token_hash`: HMAC-SHA256 hash of the refresh token.
- `expires_at`: inactivity expiration for the current refresh token.
- `absolute_expires_at`: hard session expiration; this value is preserved across rotations.
- `revoked_at`: set when the refresh token is revoked or rotated.

## Refresh

Use `refreshSession` with the current refresh token:

```graphql
mutation RefreshSession($refresh: RefreshSessionInput!) {
  refreshSession(refresh: $refresh) {
    email
    token
    accessToken
    refreshToken
  }
}
```

The backend validates that the stored session is:

- not revoked,
- not past `expires_at`,
- not past `absolute_expires_at`,
- owned by an active user.

If valid, the used refresh token is revoked and a new access/refresh token pair
is issued. The new refresh token gets a new hash, but keeps the original
`absolute_expires_at` so the session cannot be extended forever.

## Reuse Detection

If a refresh token hash exists but is already revoked, the backend treats it as
refresh token reuse. It revokes all active sessions for that user and rejects the
request.

## Logout And Revocation

Logout revokes the session tied to the provided refresh token:

```graphql
mutation Logout($logout: LogoutInput!) {
  logout(logout: $logout)
}
```

The backend also revokes all active sessions for a user when:

- the user's password is changed,
- the user is disabled.

## Frontend Storage

Currently, both access and refresh tokens are kept in frontend memory. The TODO
roadmap still includes moving the refresh token to an `HttpOnly`, `Secure`,
`SameSite` cookie and keeping only the access token in memory.
