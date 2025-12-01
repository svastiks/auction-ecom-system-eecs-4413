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

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
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
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Try to parse as JSON anyway, might be JSON without proper content-type
        const text = await response.text();
        if (text) {
          try {
            data = JSON.parse(text);
          } catch {
            // Not JSON, use text as message
            data = { detail: text || `HTTP ${response.status} Error` };
          }
        }
      }
    } catch (parseError) {
      // If parsing fails, create a basic error object
      data = { detail: `HTTP ${response.status} Error` };
    }

    if (!response.ok) {
      // Handle FastAPI validation errors which return arrays
      let errorMessage: string;
      if (Array.isArray(data?.detail)) {
        // FastAPI validation errors are arrays of error objects
        errorMessage = data.detail
          .map((e: any) => {
            if (typeof e === 'string') return e;
            if (e?.msg) return e.msg;
            if (e?.message) return e.message;
            // Format validation error: "Field: message"
            const field = Array.isArray(e?.loc) && e.loc.length > 1 
              ? e.loc.slice(1).join('.') 
              : 'Field';
            return `${field}: ${e?.msg || e?.message || 'Invalid value'}`;
          })
          .join(', ') || `HTTP ${response.status} Error`;
      } else {
        errorMessage = data?.detail || data?.message || `HTTP ${response.status} Error`;
      }
      
      throw new ApiError(
        response.status,
        errorMessage,
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
  getMe: async () => {
    const user = await apiRequest<any>('/users/me');
    // Transform to ensure id field exists (map user_id to id)
    return {
      ...user,
      id: user.user_id || user.id,
    } as User;
  },
  
  updateMe: (data: Partial<User>) =>
    apiRequest<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // Addresses
  getAddresses: async () => {
    const response = await apiRequest<{ addresses: any[], total: number }>('/users/me/addresses');
    // Backend returns { addresses: [...], total: ... }, extract and transform
    const addresses = Array.isArray(response.addresses) ? response.addresses : [];
    return addresses.map((addr: any) => ({
      ...addr,
      id: addr.address_id || addr.id, // Map address_id to id
    })) as Address[];
  },
  
  createAddress: async (data: AddressInput) => {
    const response = await apiRequest<{ message: string, address: Address }>('/users/me/addresses', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    // Backend returns { message, address }, extract the address
    const address = response.address || response as any;
    return {
      ...address,
      id: address.address_id || address.id,
    } as Address;
  },
  
  updateAddress: async (id: string | number, data: Partial<AddressInput>) => {
    const response = await apiRequest<{ message: string, address: Address }>(`/users/me/addresses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    // Backend returns { message, address }, extract the address
    const address = response.address || response as any;
    return {
      ...address,
      id: address.address_id || address.id || id.toString(),
    } as Address;
  },
  
  deleteAddress: (id: string | number) =>
    apiRequest(`/users/me/addresses/${id}`, { method: 'DELETE' }),

  // Catalogue
  getCategories: async () => {
    const categories = await apiRequest<Category[]>('/catalogue/categories');
    // Transform to ensure id field exists (map category_id to id)
    return Array.isArray(categories) ? categories.map((cat: any) => ({
      ...cat,
      id: cat.category_id || cat.id,
    })) : [];
  },
  
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
  
  getItem: async (id: string | number) => {
    const item = await apiRequest<Item>(`/catalogue/items/${id}`);
    // Transform to ensure id field exists
    return {
      ...item,
      id: (item as any).item_id || item.id,
    } as Item;
  },
  
  createItem: async (data: ItemInput) => {
    const item = await apiRequest<Item>('/catalogue/items', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    // Transform to ensure id field exists
    return {
      ...item,
      id: (item as any).item_id || item.id,
    } as Item;
  },
  
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
  createAuction: async (data: AuctionInput) => {
    const auction = await apiRequest<Auction>('/auction', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    // Transform to ensure id field exists
    return {
      ...auction,
      id: (auction as any).auction_id || auction.id,
    } as Auction;
  },
  
  searchAuctions: (keyword: string) =>
    apiRequest<any>('/auction/search', {
      method: 'POST',
      body: JSON.stringify({
        keyword,
        skip: 0,
        limit: 100
      }),
    }),
  
  getItemAuctions: async (itemId: string | number) => {
    const response = await apiRequest<Auction[]>(`/auction/items/${itemId}`);
    // Transform auctions to ensure id field exists
    return Array.isArray(response) ? response.map((auction: any) => ({
      ...auction,
      id: auction.auction_id || auction.id,
      item_id: auction.item_id || itemId.toString(),
    })) : [];
  },
  
  getAuction: async (id: string | number) => {
    const auction = await apiRequest<Auction>(`/auction/${id}`);
    // Transform to ensure id field exists and handle numeric fields
    return {
      ...auction,
      id: (auction as any).auction_id || auction.id,
      min_increment: Number(auction.min_increment) || 100, // Ensure it's a number, default to $1.00
      starting_price: Number(auction.starting_price) || 0,
      current_highest_bid: auction.current_highest_bid ? Number(auction.current_highest_bid) : undefined,
    } as Auction;
  },
  
  placeBid: async (auction_id: string | number, amount: number) => {
    const bid = await apiRequest<Bid>('/auction/bid', {
      method: 'POST',
      body: JSON.stringify({ auction_id, amount }),
    });
    // Transform to ensure id field exists
    return {
      ...bid,
      id: (bid as any).bid_id || bid.id,
      created_at: (bid as any).placed_at || bid.created_at,
    } as Bid;
  },
  
  getAuctionBids: async (auctionId: string | number) => {
    const bids = await apiRequest<Bid[]>(`/auction/${auctionId}/bids`);
    // Transform bids to ensure id field exists and preserve bidder info
    return Array.isArray(bids) ? bids.map((bid: any) => ({
      ...bid,
      id: bid.bid_id || bid.id,
      auction_id: bid.auction_id || auctionId.toString(),
      created_at: bid.placed_at || bid.created_at,
      bidder: bid.bidder || bid.user, // Preserve bidder info from backend
      bidder_id: bid.bidder_id || bid.user_id, // Map bidder_id
    })) : [];
  },
  
  getAuctionStatus: (auctionId: string | number) =>
    apiRequest<{ status: string }>(`/auction/${auctionId}/status`),
  
  endAuction: (auctionId: string | number) =>
    apiRequest(`/auction/${auctionId}/end`, { method: 'POST' }),

  // Orders
  getMyOrders: async () => {
    const orders = await apiRequest<Order[]>('/orders');
    // Transform to ensure id field exists
    return Array.isArray(orders) ? orders.map((order: any) => ({
      ...order,
      id: order.order_id || order.id,
    })) : [];
  },
  
  createOrder: async (data: OrderInput) => {
    const order = await apiRequest<Order>('/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    // Transform to ensure id field exists
    return {
      ...order,
      id: (order as any).order_id || order.id,
    } as Order;
  },
  
  getOrder: async (id: string | number) => {
    const order = await apiRequest<Order>(`/orders/${id}`);
    // Transform to ensure id field exists
    return {
      ...order,
      id: (order as any).order_id || order.id,
    } as Order;
  },
  
  updateShippingMethod: (orderId: number, shipping_method: string) =>
    apiRequest(`/orders/${orderId}/shipping-method`, {
      method: 'PUT',
      body: JSON.stringify({ shipping_method }),
    }),
  
  payOrder: (orderId: string | number, payment: PaymentInput) =>
    apiRequest(`/orders/${orderId}/pay`, {
      method: 'POST',
      body: JSON.stringify(payment),
    }),
  
  getShipment: (orderId: string | number) =>
    apiRequest<Shipment>(`/orders/${orderId}/shipment`),

  getMyBids: async () => {
    const response = await apiRequest<{ bids: any[], total: number, page: number, page_size: number, total_pages: number }>('/users/me/bids');
    // Backend returns { bids: [...], total: ... }, extract and transform
    const bids = Array.isArray(response.bids) ? response.bids : [];
    return bids.map((bid: any) => ({
      ...bid,
      id: bid.bid_id || bid.id, // Map bid_id to id
      auction_id: bid.auction_id || bid.id, // Ensure auction_id exists
      amount: bid.last_bid_amount || bid.amount, // Use last_bid_amount from MyBidItem
      created_at: bid.placed_at || bid.created_at, // Map placed_at to created_at
    })) as Bid[];
  },
};

// Types
export interface SignupRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  password: string;
  address?: AddressInput;
}

export interface AuthResponse {
  token?: string;
  access_token?: string;
  user?: User;
}

export interface User {
  id: string; // UUID from backend (user_id)
  user_id?: string; // Backend field
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
}

export interface Address {
  id: string; // UUID from backend (address_id)
  address_id?: string; // Backend field
  user_id?: string;
  street_line1: string;
  street_line2?: string;
  city: string;
  state_region?: string;
  postal_code: string;
  country: string;
  phone?: string;
  is_default_shipping: boolean;
  created_at?: string;
  updated_at?: string;
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
  id: string; // UUID from backend (category_id)
  category_id?: string; // Backend field
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
  id: string; // UUID from backend (item_id)
  item_id?: string; // Backend field
  title: string;
  description: string;
  category_id: string; // UUID
  keywords?: string;
  base_price: number;
  shipping_price_normal: number;
  shipping_price_expedited: number;
  shipping_time_days: number;
  is_active: boolean;
  auction_id?: string; // UUID from backend
  seller_id?: string; // UUID of the seller
  images: ItemImage[];
  category?: Category;
}

export interface ItemInput {
  title: string;
  description: string;
  category_id: string | null; // UUID from backend, can be null
  keywords?: string;
  base_price: number;
  shipping_price_normal: number;
  shipping_price_expedited: number;
  shipping_time_days: number;
  is_active: boolean;
  images: ImageInput[];
}

export interface Auction {
  id: string; // UUID from backend (auction_id)
  auction_id?: string; // Backend field
  auction_type: string;
  starting_price: number;
  min_increment: number;
  start_time: string;
  end_time: string;
  status: string;
  item_id: string; // UUID
  item?: Item;
  current_highest_bid?: number;
  highest_bidder_id?: string; // UUID
  winning_bid_id?: string; // UUID
  winning_bidder_id?: string; // UUID
  winning_bidder?: { // Backend returns winning bidder info
    user_id: string;
    first_name?: string;
    last_name?: string;
  };
  has_order?: boolean;
  order_id?: string; // UUID
}

export interface AuctionInput {
  auction_type: string;
  starting_price: number;
  min_increment: number;
  start_time: string;
  end_time: string;
  status: string;
  item_id: string; // UUID, not number
}

export interface Bid {
  id: string; // UUID from backend (bid_id)
  bid_id?: string; // Backend field
  auction_id: string; // UUID
  item_id?: string; // UUID (from MyBidItem)
  item_title?: string; // From MyBidItem
  last_bid_amount?: number; // From MyBidItem
  current_highest_bid?: number; // From MyBidItem
  placed_at?: string; // Backend field name
  created_at?: string; // Alias for placed_at
  time_left_seconds?: number | null;
  status?: string; // LEADING, OUTBID, ENDED, WON
  auction_status?: string;
  auction_end_time?: string;
  amount: number;
  user_id?: string; // UUID
  bidder_id?: string; // UUID (backend field name)
  user?: User; // Legacy field, may not be present
  bidder?: { // Backend returns bidder with first_name and last_name
    user_id: string;
    first_name?: string;
    last_name?: string;
  };
}

export interface Order {
  id: string; // UUID
  order_id?: string; // Backend field
  buyer_id?: string; // UUID
  auction_id: string; // UUID
  item_id?: string; // UUID
  shipping_method: string;
  shipping_address_id: string; // UUID
  winning_bid_amount?: number;
  shipping_cost?: number;
  total_amount?: number;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface OrderInput {
  shipping_method: string;
  shipping_address_id: string; // UUID
  auction_id: string; // UUID
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
