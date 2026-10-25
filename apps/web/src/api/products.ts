import { apiClient } from './client'

export interface Product {
  id: string
  name: string
  description: string | null
  /** 金额由后端按字符串序列化，避免浮点精度问题 */
  price: string
  stock: number
  status: string
  created_at: string
}

export interface ProductPage {
  items: Product[]
  total: number
  page: number
  page_size: number
}

export async function getProducts(page = 1, pageSize = 20): Promise<ProductPage> {
  const { data } = await apiClient.get<ProductPage>('/products', {
    params: { page, page_size: pageSize },
  })
  return data
}
