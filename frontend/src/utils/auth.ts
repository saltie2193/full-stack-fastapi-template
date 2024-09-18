export type AuthState = string | null

/**
 * Get auth state from localStorage.
 *
 * @returns Auth state from localStorage.
 */
export function getLocalAuthState(): AuthState {
  return localStorage.getItem("authState")
}

/**
 * Update auth state in localStorage.
 *
 * If `newState` is `null`, auth state will be removed from localStorage.
 *
 * @param newState - New auth state
 */
export function updateLocalAuthState(newState: AuthState) {
  if (newState === null) {
    localStorage.removeItem("authState")
  } else {
    localStorage.setItem("authState", newState)
  }
}

/**
 * Get authentication token from localStorage.
 */
export function getAuthToken(): string | null {
  return getLocalAuthState()
}

/**
 * Check if the current user is logged in.
 */
export function isLoggedIn(): boolean {
  return getAuthToken() != null
}
