# Auction E-Commerce System - Complete Testing Guide

## Quick Start

**Server Setup:**
```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload
```

**Base URL:** `http://127.0.0.1:8000/api/v1`

---

## Postman Collection Setup

### Create Variables
1. Right-click collection → **Edit** → **Variables** tab
2. Add these variables:
   - `access_token` (leave empty)
   - `category_id` (leave empty)
   - `item_id` (leave empty)
   - `auction_id` (leave empty)
3. Click **Save**

### Authentication Setup
Each request that needs auth should have:
- **Header**: `Authorization: Bearer {{access_token}}`

---

## Complete Testing Workflow

### Phase 1: User Setup

#### 1.1 Create Seller Account
```
POST http://127.0.0.1:8000/api/v1/auth/signup
```
**Request Body:**
```json
{
  "username": "seller1",
  "email": "seller1@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Seller"
}
```
**Action:** Save `access_token` → `{{access_token}}`

#### 1.2 Create Bidder Account
```
POST http://127.0.0.1:8000/api/v1/auth/signup
```
**Request Body:**
```json
{
  "username": "bidder1",
  "email": "bidder1@example.com",
  "password": "password123",
  "first_name": "Jane",
  "last_name": "Bidder"
}
```
**Action:** Save bidder's `access_token` (switch to this later for bidding)

---

### Phase 2: Catalogue Setup

#### 2.1 Create Category
```
POST http://127.0.0.1:8000/api/v1/catalogue/categories
Header: Authorization: Bearer {{access_token}}
```
**Request Body:**
```json
{
  "name": "Electronics",
  "description": "Electronic items and devices"
}
```
**Action:** Save `category_id` → `{{category_id}}`

#### 2.2 Create Catalogue Item
```
POST http://127.0.0.1:8000/api/v1/catalogue/items
Header: Authorization: Bearer {{access_token}}
```
**Request Body:**
```json
{
  "title": "Vintage Camera",
  "description": "A beautiful vintage camera in excellent condition",
  "category_id": "{{category_id}}",
  "keywords": "camera vintage photography",
  "base_price": "100.00",
  "shipping_price_normal": "10.00",
  "shipping_price_expedited": "25.00",
  "shipping_time_days": 5
}
```
**Action:** Save `item_id` → `{{item_id}}`

---

### Phase 3: Auction Setup

#### 3.1 Create Auction
```
POST http://127.0.0.1:8000/api/v1/auction
Header: Authorization: Bearer {{access_token}}
```
**Request Body:**
```json
{
  "item_id": "{{item_id}}",
  "auction_type": "FORWARD",
  "starting_price": "50.00",
  "min_increment": "5.00",
  "start_time": "2025-11-02T10:00:00Z",
  "end_time": "2025-11-09T10:00:00Z"
}
```
**Action:** Save `auction_id` → `{{auction_id}}`

**Note:** Adjust `start_time` and `end_time` for future dates.

---

### Phase 4: UC2 Testing - Browse Catalogue

#### 4.1 UC2.1: Search Auctions
```
POST http://127.0.0.1:8000/api/v1/auction/search
```
**Request Body:**
```json
{
  "keyword": "camera",
  "skip": 0,
  "limit": 20
}
```
**Expected Response:**
- Array of `items` matching keyword
- Each item shows: title, current_bidding_price, status, remaining_time_seconds
- `total_count` and `has_more` for pagination

**Test Variations:**
```json
// With category filter
{
  "keyword": "camera",
  "category_id": "{{category_id}}",
  "status": "ACTIVE",
  "skip": 0,
  "limit": 20
}

// With price range
{
  "keyword": "camera",
  "min_price": "40.00",
  "max_price": "200.00",
  "skip": 0,
  "limit": 20
}
```

#### 4.2 UC2.2: Display Auction Details
```
GET http://127.0.0.1:8000/api/v1/auction/items/{{item_id}}
```
**Expected Response:**
- Full item details
- Current bidding price
- Auction type (FORWARD)
- Remaining time (if ACTIVE)
- Seller name and info
- Category info
- Current highest bidder
- Item images

This fulfills UC2.3 item selection display.

#### 4.3 UC2.3: Get Full Auction Info
```
GET http://127.0.0.1:8000/api/v1/auction/{{auction_id}}
```
**Expected Response:**
- All auction details
- Complete bid history
- Winner information
- Current highest bid

---

### Phase 5: UC3 Testing - Bidding

**⚠️ Switch to bidder token for these tests!**

#### 5.1 UC3: Place a Bid
```
POST http://127.0.0.1:8000/api/v1/auction/bid
Header: Authorization: Bearer {{bidder_token}}
```
**Request Body:**
```json
{
  "auction_id": "{{auction_id}}",
  "amount": "60.00"
}
```
**Expected Response:**
- `bid_id` - Unique bid ID
- `is_winning_bid: true` - Confirms this is now highest
- `current_highest_bid: "60.00"`
- `message: "Bid placed successfully"`

**Validation Tests:**
1. **Test minimum increment:** Try `"amount": "54.99"` → Should fail (current + increment = 55.00)
2. **Test own item:** Switch back to seller token → Should fail with "Cannot bid on own item"
3. **Test inactive auction:** Create ended auction → Should fail with "auction has ended"

#### 5.2 View All Bids
```
GET http://127.0.0.1:8000/api/v1/auction/{{auction_id}}/bids
```
**Expected Response:**
- Array of bids ordered by amount (highest first)
- Each bid shows: amount, bidder info, placed_at time

#### 5.3 Check Auction Status
```
GET http://127.0.0.1:8000/api/v1/auction/{{auction_id}}/status
```
**Expected Response:**
- Current `status` (ACTIVE, ENDED, etc.)
- `remaining_time_seconds` if active
- `can_pay: true` if auction ended with bids
- Winner information if ended

#### 5.4 Place Higher Bid
```
POST http://127.0.0.1:8000/api/v1/auction/bid
Header: Authorization: Bearer {{bidder_token}}
```
**Request Body:**
```json
{
  "auction_id": "{{auction_id}}",
  "amount": "70.00"
}
```

#### 5.5 Verify Bid Update
```
GET http://127.0.0.1:8000/api/v1/auction/{{auction_id}}/status
```
**Expected:** Highest bid now $70.00

---

### Phase 6: Error Testing

#### 6.1 Test Bid Too Low
```
POST http://127.0.0.1:8000/api/v1/auction/bid
Header: Authorization: Bearer {{bidder_token}}
```
**Request Body:**
```json
{
  "auction_id": "{{auction_id}}",
  "amount": "10.00"
}
```
**Expected:** `400 Bad Request - Bid must be at least $XX.XX`

#### 6.2 Test Bid on Own Item
```
POST http://127.0.0.1:8000/api/v1/auction/bid
Header: Authorization: Bearer {{seller_token}}
```
**Expected:** `400 Bad Request - Cannot bid on own item`

#### 6.3 Test Bid on Ended Auction
Create an auction with past end_time, then bid:
```
POST http://127.0.0.1:8000/api/v1/auction/bid
Header: Authorization: Bearer {{bidder_token}}
```
**Expected:** `400 Bad Request - Auction has ended`

#### 6.4 Test Search with No Results
```
POST http://127.0.0.1:8000/api/v1/auction/search
```
**Request Body:**
```json
{
  "keyword": "nonexistentitem12345",
  "skip": 0,
  "limit": 20
}
```
**Expected:** `{"items": [], "total_count": 0, "has_more": false}`

---

## Complete Test Scenario

### Happy Path
1. ✅ Login as seller → Get token
2. ✅ Create category → Get category_id
3. ✅ Create item → Get item_id
4. ✅ Create auction → Get auction_id
5. ✅ Search for item → Verify it appears
6. ✅ Get auction details → Verify all info
7. ✅ Login as bidder → Get bidder token
8. ✅ Place first bid → Verify success
9. ✅ Check bids → Verify bid appears
10. ✅ Place higher bid → Verify update
11. ✅ Get status → Verify latest bid
12. ✅ Check error cases → All fail correctly

### Response Format Checklist

**UC2.1 Search Response:**
```json
{
  "items": [
    {
      "auction_id": "uuid",
      "item_id": "uuid",
      "title": "string",
      "current_bidding_price": "decimal",
      "auction_type": "FORWARD",
      "remaining_time_seconds": integer,
      "status": "ACTIVE",
      "seller_name": "string",
      "category_name": "string"
    }
  ],
  "total_count": integer,
  "has_more": boolean
}
```

**UC2.2 Auction Details Response:**
```json
{
  "auction_id": "uuid",
  "item_id": "uuid",
  "title": "string",
  "description": "string",
  "current_bidding_price": "decimal",
  "auction_type": "FORWARD",
  "remaining_time_seconds": integer,
  "status": "ACTIVE",
  "item_images": ["url1", "url2"],
  "seller_name": "string",
  "category_name": "string",
  "current_highest_bidder_id": "uuid",
  "current_highest_bidder_name": "string"
}
```

**UC3 Bid Response:**
```json
{
  "bid_id": "uuid",
  "auction_id": "uuid",
  "amount": "decimal",
  "placed_at": "timestamp",
  "is_winning_bid": true,
  "current_highest_bid": "decimal",
  "current_highest_bidder_id": "uuid",
  "message": "Bid placed successfully"
}
```

---

## Quick Reference

| Endpoint | Method | Auth | Use Case |
|----------|--------|------|----------|
| `http://127.0.0.1:8000/api/v1/auth/signup` | POST | No | Create accounts |
| `http://127.0.0.1:8000/api/v1/auth/login` | POST | No | Get token |
| `http://127.0.0.1:8000/api/v1/catalogue/categories` | POST | Yes | Setup category |
| `http://127.0.0.1:8000/api/v1/catalogue/items` | POST | Yes | Create item |
| `http://127.0.0.1:8000/api/v1/auction` | POST | Yes | Create auction |
| `http://127.0.0.1:8000/api/v1/auction/search` | POST | No | UC2.1 Search |
| `http://127.0.0.1:8000/api/v1/auction/items/{item_id}` | GET | No | UC2.2 Details |
| `http://127.0.0.1:8000/api/v1/auction/{auction_id}` | GET | No | Full auction info |
| `http://127.0.0.1:8000/api/v1/auction/bid` | POST | Yes | UC3 Place bid |
| `http://127.0.0.1:8000/api/v1/auction/{auction_id}/bids` | GET | No | View bids |
| `http://127.0.0.1:8000/api/v1/auction/{auction_id}/status` | GET | No | Check status |

---

## Troubleshooting

**401 Unauthorized:** Token missing/expired
- Re-login and update `{{access_token}}`

**404 Not Found:** Wrong ID
- Check you copied UUID without `{}`
- Verify ID exists in previous response

**400 Bad Request:** Validation error
- Check request body format
- Verify amounts meet minimum requirements
- Ensure auction is ACTIVE

**500 Internal Server Error:** Server issue
- Check server terminal for errors
- Verify database is running
- Check server logs

---

## Test Completion Checklist

### UC2: Browse Catalogue ✅
- [ ] UC2.1: Search by keyword works
- [ ] UC2.1: Search with category filter works
- [ ] UC2.1: Search with price range works
- [ ] UC2.2: Display shows all required fields
- [ ] UC2.2: Remaining time calculated correctly
- [ ] UC2.3: Item details accessible

### UC3: Bidding ✅
- [ ] UC3: Bid placed successfully
- [ ] UC3: Bid amount validated
- [ ] UC3: Cannot bid on own item
- [ ] UC3: Cannot bid below minimum
- [ ] UC3: Cannot bid on ended auction
- [ ] UC3: Bids ordered correctly
- [ ] UC3: Status updates correctly

### General ✅
- [ ] All endpoints return expected data
- [ ] Error handling works
- [ ] Authentication required where needed
- [ ] UUIDs validated correctly

---

**Ready to test!** Follow phases 1-6 in order, and you'll have fully tested all functionality. 🎯
