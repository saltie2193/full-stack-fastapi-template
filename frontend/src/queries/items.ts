import type { TDataReadItems } from "../client"

export const itemKeys = {
  all: ["items"] as const,
  query: (options: TDataReadItems) => [...itemKeys.all, options],
}
