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
  const queryKey = options?.queryKey || ["currentUser"]
  const { data: user, ...query } = useQuery<UserPublic, ApiError>(
    {
      queryKey,
      queryFn: UsersService.readUserMe,
      enabled: options?.enabled,
    },
    _queryClient,
  )
  return { ...query, queryKey, user }
}
