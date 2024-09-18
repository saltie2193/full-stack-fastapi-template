import {
  type QueryClient,
  type QueryKey,
  useQuery,
} from "@tanstack/react-query"
import { type UserPublic, UsersService } from "../client"
import {usersKeys} from "../queries/users.ts";

type UseCurrentUserOptions = {
  queryKey?: QueryKey
  enabled?: boolean
}

export function useCurrentUser(
  props?: UseCurrentUserOptions,
  queryClient?: QueryClient,
) {
  const queryKey = props?.queryKey || usersKeys.current()
  const {
    data: user,
    isLoading,
    isError,
    error,
  } = useQuery<UserPublic, Error>(
    {
      queryKey: queryKey,
      queryFn: UsersService.readUserMe,
      enabled: props?.enabled,
    },
    queryClient,
  )
  return { error, isError, isLoading, queryKey, user }
}
