import {
  type QueryClient,
  type UndefinedInitialDataOptions,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { useEffect } from "react"
import type { ApiError } from "../client"
import useAuth, { isLoggedIn } from "./useAuth.ts"

/**
 * Wrapper around useQuery, intercepting error replies and performing a logout if a `401 - Unauthorized` is received.
 * @param options
 * @param queryClient
 */
export function useCustomQuery<T>(
  options: UndefinedInitialDataOptions<T, ApiError>,
  queryClient?: QueryClient | undefined,
) {
  const _queryClient = useQueryClient()
  const { logout } = useAuth()
  const { error, ...query } = useQuery<T, ApiError>(
    {
      enabled: isLoggedIn(),
      retry: (retryCount, error) => {
        // don't retry if we receive 401 unauthorized as response
        return error.status === 401 ? false : retryCount <= 3
      },
      ...options,
    },
    queryClient,
  )

  async function invalidate() {
    return _queryClient.invalidateQueries({ queryKey: options.queryKey })
  }

  function remove() {
    return _queryClient.removeQueries({ queryKey: options.queryKey })
  }

  useEffect(() => {
    if (error?.status === 401 && isLoggedIn()) {
      invalidate()
        .then(() => remove())
        .then(logout)
    } else if (error?.status === 401 && !isLoggedIn()) {
      remove()
    }
  }, [error, logout])

  return { error, ...query, invalidate }
}
