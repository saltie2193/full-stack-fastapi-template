import {
  type PlaceholderDataFunction,
  type QueryKey,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { type ItemsPublic, ItemsService } from "../client"
import { itemKeys } from "../queries/items.ts"

type QueryOptions =
  | { limit: number; page: number; skip?: never }
  | { limit: number; page?: never; skip: number }

/**
 * Get query parameters for querying all items.
 *
 * @remarks
 * Expects either `skip` or `page` to be set.
 * `limit` is always required.
 *
 * Uses `page` to calculate `skip`. If provided, `skip` takes precedence over `page`.
 *
 * @param limit Number of items per query
 * @param skip Items to skip
 * @param page Page to show
 */
function getItemsQueryParams({ limit, page, skip }: QueryOptions): {
  limit: number
  skip: number
} {
  return { skip: skip ?? (page - 1) * limit, limit }
}

type UseItemsOptions = {
  queryKey?: QueryKey
  placeholderData:
    | ItemsPublic
    | PlaceholderDataFunction<ItemsPublic, Error, ItemsPublic, QueryKey>
  queryOptions: QueryOptions
}

/**
 *
 * @remarks
 * If not provided `queryKey` will be generated from `options`.
 *
 * @param queryKey `QuerKey` used for the performed query.
 * @param queryOptions
 * @param queryOptions.page Shown page, used to calculate skipped items. Will be ignored if `skip` is provided.
 * @param queryOptions.limit Items shown per page
 * @param queryOptions.skip Items to skip. Overrides automatic calculation based on `page`.
 * @param placeholderData Optional placeholder data, returned until the request completes.
 */
export function useItems({
  queryKey: _queryKey,
  queryOptions,
  placeholderData,
}: UseItemsOptions) {
  const queryClient = useQueryClient()
  const queryParams = getItemsQueryParams(queryOptions)
  const queryKey = _queryKey ?? itemKeys.query(queryParams)

  /**
   * Fetch all items.
   * Parameters default to values provided to `useItems` hook returning this functon.
   *
   *
   * @param queryKey `QueryKey` used for the query.
   * @param queryOptions Options the request parameters are generated from.
   * @param placeholderData Optional placeholder data, returned until the request completes.
   */
  function fetchItems({
    queryKey: __queryKey = queryKey,
    queryOptions: __queryOptions = queryOptions,
    placeholderData: __placeholderData = placeholderData,
  }) {
    const { data: items, ...query } = useQuery({
      placeholderData: __placeholderData,
      queryFn: () => ItemsService.readItems(__queryOptions),
      queryKey: __queryKey,
    })
    return { items, ...query }
  }

  /**
   * Prefetch items for given page.
   *
   * @param page Page number
   * @param limit Items shown per page
   */
  async function prefetchItems({
    page,
    limit,
  }: { page: number; limit: number }) {
    const _queryParams = getItemsQueryParams({ page, limit })
    return queryClient.prefetchQuery({
      queryKey: itemKeys.query(_queryParams),
      queryFn: () => ItemsService.readItems(_queryParams),
    })
  }

  return { ...fetchItems({}), prefetchItems }
}
