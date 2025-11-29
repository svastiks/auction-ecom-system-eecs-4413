const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = typeof window !== 'undefined' 
    ? localStorage.getItem('accessToken') 
    : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (accessToken && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/signup')) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    }

    if (!response.ok) {
      throw new ApiError(
        response.status,
        data?.message || data?.detail || `HTTP ${response.status}`,
        data
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, 'Network error or server unavailable');
  }
}

export const api = {
  // Auth
  signup: (data: SignupRequest) => 
    apiRequest<AuthResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  login: (username: string, password: string) =>
    apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  
  logout: () =>
    apiRequest('/auth/logout', { method: 'POST' }),
  
  forgotPassword: (email: string) =>
    apiRequest('/auth/password/forgot', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  
  resetPassword: (token: string, new_password: string) =>
    apiRequest('/auth/password/reset', {
      method: 'POST',
      body: JSON.stringify({ token, new_password }),
    }),

  // Users
  getMe: () => apiRequest<User>('/users/me'),
  
  updateMe: (data: Partial<User>) =>
    apiRequest<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // Addresses
  getAddresses: () => apiRequest<Address[]>('/users/me/addresses'),
  
  createAddress: (data: AddressInput) =>
    apiRequest<Address>('/users/me/addresses', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  updateAddress: (id: number, data: Partial<AddressInput>) =>
    apiRequest<Address>(`/users/me/addresses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  deleteAddress: (id: number) =>
    apiRequest(`/users/me/addresses/${id}`, { method: 'DELETE' }),

  // Catalogue
  getCategories: () => apiRequest<Category[]>('/catalogue/categories'),
  
  createCategory: (data: CategoryInput) =>
    apiRequest<Category>('/catalogue/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  updateCategory: (id: number, data: Partial<CategoryInput>) =>
    apiRequest<Category>(`/catalogue/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  deleteCategory: (id: number) =>
    apiRequest(`/catalogue/categories/${id}`, { method: 'DELETE' }),

  getItems: () => apiRequest<Item[]>('/catalogue/items'),
  
  getItem: (id: number) => apiRequest<Item>(`/catalogue/items/${id}`),
  
  createItem: (data: ItemInput) =>
    apiRequest<Item>('/catalogue/items', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  updateItem: (id: number, data: Partial<ItemInput>) =>
    apiRequest<Item>(`/catalogue/items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  deleteItem: (id: number) =>
    apiRequest(`/catalogue/items/${id}`, { method: 'DELETE' }),
  
  addItemImage: (itemId: number, data: ImageInput) =>
    apiRequest(`/catalogue/items/${itemId}/images`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  deleteImage: (imageId: number) =>
    apiRequest(`/catalogue/images/${imageId}`, { method: 'DELETE' }),

  // Auction
  createAuction: (data: AuctionInput) =>
    apiRequest<Auction>('/auction', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  searchAuctions: (keyword: string) =>
    apiRequest<Auction[]>('/auction/search', {
      method: 'POST',
      body: JSON.stringify({ keyword }),
    }),
  
  getItemAuctions: (itemId: number) =>
    apiRequest<Auction[]>(`/auction/items/${itemId}`),
  
  getAuction: (id: number) =>
    apiRequest<Auction>(`/auction/${id}`),
  
  placeBid: (auction_id: number, amount: number) =>
    apiRequest<Bid>('/auction/bid', {
      method: 'POST',
      body: JSON.stringify({ auction_id, amount }),
    }),
  
  getAuctionBids: (auctionId: number) =>
    apiRequest<Bid[]>(`/auction/${auctionId}/bids`),
  
  getAuctionStatus: (auctionId: number) =>
    apiRequest<{ status: string }>(`/auction/${auctionId}/status`),
  
  endAuction: (auctionId: number) =>
    apiRequest(`/auction/${auctionId}/end`, { method: 'POST' }),

  // Orders
  createOrder: (data: OrderInput) =>
    apiRequest<Order>('/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  getOrder: (id: number) =>
    apiRequest<Order>(`/orders/${id}`),
  
  updateShippingMethod: (orderId: number, shipping_method: string) =>
    apiRequest(`/orders/${orderId}/shipping-method`, {
      method: 'PUT',
      body: JSON.stringify({ shipping_method }),
    }),
  
  payOrder: (orderId: number, payment: PaymentInput) =>
    apiRequest(`/orders/${orderId}/pay`, {
      method: 'POST',
      body: JSON.stringify(payment),
    }),
  
  getShipment: (orderId: number) =>
    apiRequest<Shipment>(`/orders/${orderId}/shipment`),

  getMyBids: () => apiRequest<Bid[]>('/users/me/bids'),
};

// Types
export interface SignupRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  password: string;
}

export interface AuthResponse {
  token?: string;
  access_token?: string;
  user?: User;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
}

export interface Address {
  id: number;
  street_line1: string;
  street_line2?: string;
  city: string;
  state_region: string;
  postal_code: string;
  country: string;
  is_default_shipping: boolean;
}

export interface AddressInput {
  street_line1: string;
  street_line2?: string;
  city: string;
  state_region: string;
  postal_code: string;
  country: string;
  is_default_shipping?: boolean;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
}

export interface CategoryInput {
  name: string;
  description?: string;
}

export interface ItemImage {
  id: number;
  url: string;
  position: number;
}

export interface ImageInput {
  url: string;
  position: number;
}

export interface Item {
  id: number;
  title: string;
  description: string;
  category_id: number;
  keywords?: string;
  base_price: number;
  shipping_price_normal: number;
  shipping_price_expedited: number;
  shipping_time_days: number;
  is_active: boolean;
  images: ItemImage[];
  category?: Category;
}

export interface ItemInput {
  title: string;
  description: string;
  category_id: number;
  keywords?: string;
  base_price: number;
  shipping_price_normal: number;
  shipping_price_expedited: number;
  shipping_time_days: number;
  is_active: boolean;
  images: ImageInput[];
}

export interface Auction {
  id: number;
  auction_type: string;
  starting_price: number;
  min_increment: number;
  start_time: string;
  end_time: string;
  status: string;
  item_id: number;
  item?: Item;
  current_highest_bid?: number;
  highest_bidder_id?: number;
}

export interface AuctionInput {
  auction_type: string;
  starting_price: number;
  min_increment: number;
  start_time: string;
  end_time: string;
  status: string;
  item_id: number;
}

export interface Bid {
  id: number;
  auction_id: number;
  user_id: number;
  amount: number;
  created_at: string;
  user?: User;
}

export interface Order {
  id: number;
  user_id: number;
  auction_id: number;
  shipping_method: string;
  shipping_address_id: number;
  total_amount?: number;
  status: string;
  created_at: string;
}

export interface OrderInput {
  shipping_method: string;
  shipping_address_id: number;
  auction_id: number;
}

export interface PaymentInput {
  card_number: string;
  card_holder_name: string;
  expiry_month: number;
  expiry_year: number;
  cvv: string;
}

export interface Shipment {
  order_id: number;
  estimated_delivery_days: number;
  shipped_at?: string;
}
