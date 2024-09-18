export const usersKeys = {
  all: ["users"] as const,
  current: () => [...usersKeys.all, "current"] as const,
  paginated: ({ page }: { page: number }) => [...usersKeys.all, { page }],
}
