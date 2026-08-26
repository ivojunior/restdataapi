export interface PaginatedResponse<T> {
  skip: number
  limit: number
  items: T[]
}
