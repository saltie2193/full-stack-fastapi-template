import {
  type QueryClient,
  type QueryKey,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { type ApiError, type UserPublic, UsersService } from "../client"

type UseCurrentUserOptions = {
  queryKey?: QueryKey
  enabled?: boolean
}

export function useCurrentUser(
  options?: UseCurrentUserOptions,
  queryClient?: QueryClient,
) {
  const _queryClient = queryClient ?? useQueryClient()
  const queryKey = options?.queryKey || ["users", "current"]
  const { data: user, ...query } = useQuery<UserPublic, ApiError>(
    {
      queryKey,
      queryFn: UsersService.readUserMe,
      enabled: options?.enabled,
      retry: (retryCount, error) => {
        // don't retry if we received 401 unauthorized as response
        return error.status === 401 ? false : retryCount <= 3
      },
    },
    _queryClient,
  )

  async function invalidate() {
    return _queryClient.invalidateQueries({ queryKey })
  }

  function remove() {
      return _queryClient.removeQueries({queryKey})
  }

  return { ...query, queryKey, user, invalidate, remove }
}
