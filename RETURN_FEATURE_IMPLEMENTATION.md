# Return & Refund Feature - Enhanced Implementation Summary

## Overview
Comprehensive return and refund system cho eCommerce platform with Stripe integration, including evidence upload và proper verification workflow.

## Enhanced Business Logic Flow

### 1. PENDING Orders
```
User clicks "Cancel Order"
→ Status: CANCELLED
→ No refund (chưa thanh toán)
→ No stock rollback (chưa deduct)
```

### 2. CONFIRMED Orders  
```
User clicks "Cancel & Refund"
→ Auto create Stripe refund (100% full refund)
→ Status: REFUND_PENDING
→ Webhook receives charge.refunded
→ Status: REFUNDED
→ Stock rollback automatically
```

### 3. PROCESSING Orders
```
User clicks "Cancel"
→ Error: "Order is being processed. Contact support."
→ Admin intervention required
```

### 4. SHIPPED Orders
```
User clicks "Cancel"
→ Error: "Cannot cancel shipped orders. Wait for delivery to request return."
```

### 5. DELIVERED Orders - Enhanced Flow (NEW!)
```
User clicks "Request Return" (within 7 days)
→ Status: RETURN_REQUESTED
→ User provides reason

Admin reviews request
→ Admin approves:
   → Status: RETURN_APPROVED
   → Display return instructions + warehouse address
   → NO REFUND YET (wait for product to be returned)

User uploads evidence:
→ Upload photos (max 5) of product condition
→ Upload video (optional)
→ Add description of product state
→ Enter tracking number (optional)
→ Click "Confirm Shipped"
→ Status: RETURN_SHIPPING
→ Set return_shipped_at timestamp

Admin receives package:
→ Admin clicks "Mark as Received"
→ Status: RETURN_RECEIVED
→ Set return_received_at timestamp
→ Admin performs QC check (compare with user's uploaded evidence)

Admin QC decision:
→ If PASS:
   → Admin clicks "Confirm Refund"
   → Create Stripe refund (subtotal only, NO shipping fee)
   → Status: REFUND_PENDING
   → Webhook confirms: REFUNDED
   → Stock rollback
→ If FAIL:
   → Admin clicks "Reject QC" with reason
   → Status: RETURN_REJECTED
   → Product shipped back to customer
   → No refund issued

Admin rejects return request (before approval):
→ Status: DELIVERED (reverted)
→ User notified with rejection reason
```

## Database Changes

### OrderStatus Enum
```python
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURN_REQUESTED = "return_requested"    # User requested return
    RETURN_APPROVED = "return_approved"      # Admin approved, waiting for user to ship
    RETURN_SHIPPING = "return_shipping"      # NEW: User confirmed shipped with evidence
    RETURN_RECEIVED = "return_received"      # NEW: Admin received product, QC pending
    RETURN_REJECTED = "return_rejected"      # NEW: QC failed or admin rejected
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"
```

### New Columns - Evidence Tracking
```sql
-- Existing
ALTER TABLE orders ADD COLUMN return_requested_at TIMESTAMP WITH TIME ZONE;

-- NEW: Evidence and tracking
ALTER TABLE orders ADD COLUMN return_evidence_photos JSON;
ALTER TABLE orders ADD COLUMN return_evidence_video VARCHAR(500);
ALTER TABLE orders ADD COLUMN return_evidence_description TEXT;
ALTER TABLE orders ADD COLUMN return_shipping_provider VARCHAR(100);
ALTER TABLE orders ADD COLUMN return_tracking_number VARCHAR(100);
ALTER TABLE orders ADD COLUMN return_shipped_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE orders ADD COLUMN return_received_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE orders ADD COLUMN qc_notes TEXT;
```
**Migration:** `[NEW]_add_return_evidence_fields.py`

## Backend Implementation

### RefundService Methods

#### 1. request_return()
```python
RefundService.request_return(order_id, user_id, reason)
```
- Validates: Order exists, user owns it, status = DELIVERED
- Checks: 7-day return window from `updated_at`
- Updates: status → RETURN_REQUESTED, sets `return_requested_at`
- Returns: OrderResponse

#### 2. approve_return() - MODIFIED
```python
RefundService.approve_return(order_id)
```
- Validates: status = RETURN_REQUESTED
- Updates: status → RETURN_APPROVED
- **REMOVED:** Auto create refund (wait for product return)
- Returns: Success message with return instructions

#### 3. user_confirm_shipped() - NEW
```python
RefundService.user_confirm_shipped(
    order_id, 
    user_id,
    evidence_photos: List[str],
    evidence_video: Optional[str],
    description: str,
    shipping_provider: Optional[str],
    tracking_number: Optional[str]
)
```
- Validates: status = RETURN_APPROVED, user owns order
- Stores: Evidence photos/video URLs, description
- Updates: status → RETURN_SHIPPING, sets `return_shipped_at`
- Returns: OrderResponse with evidence

#### 4. admin_confirm_received() - NEW
```python
RefundService.admin_confirm_received(order_id, qc_notes: Optional[str])
```
- Validates: status = RETURN_SHIPPING
- Updates: status → RETURN_RECEIVED, sets `return_received_at`
- Stores: QC notes
- Returns: OrderResponse

#### 5. admin_confirm_refund() - NEW
```python
RefundService.admin_confirm_refund(
    order_id,
    refund_amount: Optional[float]  # Can adjust if partial damage
)
```
- Validates: status = RETURN_RECEIVED
- Creates: Stripe refund (partial: subtotal only)
- Updates: status → REFUND_PENDING
- Returns: Refund details

#### 6. reject_return()
```python
RefundService.reject_return(order_id, rejection_reason)
```
- Validates: status = RETURN_REQUESTED
- Reverts: status → DELIVERED
- Clears: `return_requested_at`
- Records: rejection reason in `refund_reason`

#### 7. reject_qc() - NEW
```python
RefundService.reject_qc(order_id, reason)
```
- Validates: status = RETURN_RECEIVED
- Updates: status → RETURN_REJECTED
- Records: QC rejection reason
- Triggers: Notification to arrange return shipment to customer

### API Endpoints

#### User Endpoints
```
POST /orders/{order_id}/cancel
- PENDING → CANCELLED
- CONFIRMED → REFUND_PENDING (auto refund)
- DELIVERED → RETURN_REQUESTED (if within 7 days)

POST /orders/{order_id}/return/ship
Body: {
  "evidence_photos": ["url1", "url2"],  // Max 5, required
  "evidence_video": "url",              // Optional
  "description": "Product in good condition...",  // Required
  "shipping_provider": "ViettelPost",   // Optional
  "tracking_number": "VTP123456"        // Optional
}
- Validates: status = RETURN_APPROVED
- Updates: RETURN_APPROVED → RETURN_SHIPPING
- Returns: OrderResponse with evidence
```

#### Admin Endpoints
```
GET /admin/orders/returns/pending
- List all RETURN_REQUESTED orders
- Pagination support

POST /admin/orders/{order_id}/returns/approve
- Approve return request
- RETURN_REQUESTED → RETURN_APPROVED
- NO auto refund (wait for product)

POST /admin/orders/{order_id}/returns/reject?rejection_reason=...
- Reject return request
- RETURN_REQUESTED → DELIVERED

POST /admin/orders/{order_id}/return/receive
Body: {
  "qc_notes": "Product condition matches photos, approved"
}
- Admin confirms product received
- RETURN_SHIPPING → RETURN_RECEIVED

POST /admin/orders/{order_id}/return/refund
Body: {
  "refund_amount": 15.99  // Optional: can adjust for partial damage
}
- Admin confirms refund after QC
- RETURN_RECEIVED → REFUND_PENDING
- Creates Stripe refund (subtotal only, NO shipping)

POST /admin/orders/{order_id}/return/reject-qc
Body: {
  "reason": "Product damaged by customer, not as shown in photos"
}
- Admin rejects QC
- RETURN_RECEIVED → RETURN_REJECTED
```

## Return Policy

### Time Limit
- **7 days** from delivery (`updated_at` timestamp)
- Calculated as: `(datetime.utcnow() - order.updated_at).days`
- Error message: "Return window expired. You can only return orders within 7 days of delivery. This order was delivered X days ago."

### Refund Policy - Enhanced
✅ **CONFIRMED Orders (cancelled before shipping):**
- Refund: 100% (subtotal + shipping fee)
- Automatic refund via Stripe
- Immediate stock rollback

✅ **DELIVERED Orders (return after delivery):**
- Refund: **Subtotal ONLY** (product cost)
- Shipping fee: **NOT refunded** (customer pays return shipping)
- Refund only after admin confirms product received + QC pass
- Stock rollback after refund confirmed

### Eligibility
✅ **Can Request Return:**
- Order status = DELIVERED
- Within 7 days of delivery
- User is order owner

❌ **Cannot Request Return:**
- Order already cancelled/refunded
- More than 7 days since delivery
- Order not yet delivered

### Evidence Requirements - NEW
📸 **User must provide before shipping:**
- **Photos**: 1-5 images of product condition (required)
  - Product packaging (intact/damaged)
  - Product seal/expiry date
  - Overall condition
- **Video**: Optional video walkthrough (max 2 minutes)
- **Description**: Text description of product state (required)
- **Tracking**: Shipping provider + tracking number (optional but recommended)

### Admin QC Process - NEW
🔍 **Admin verification steps:**
1. Review user-uploaded evidence
2. Receive physical product
3. Compare actual condition vs. evidence
4. Decision:
   - **PASS**: Product matches evidence → Approve refund
   - **FAIL**: Product doesn't match (damaged/opened/fake) → Reject with reason

### Admin Approval Required
- All DELIVERED returns need manual approval at 2 stages:
  1. **Initial approval**: Admin reviews return request
  2. **QC approval**: Admin checks product condition after receiving
- Prevents abuse and ensures product quality for resale

## Frontend TODO

### 1. OrderDetailPage Updates
```tsx
// Status labels
case 'return_requested': return 'Return Requested';
case 'return_approved': return 'Return Approved';

// Button logic
canRequestReturn() {
  return order.status === 'delivered' && 
         daysS inceDelivery <= 7;
}

// Display return info
{order.return_requested_at && (
  <Alert severity="info">
    Return requested on {formatDate(order.return_requested_at)}
    Pending admin approval...
  </Alert>
)}
```

### 2. Admin Return Management Page
```tsx
// Page: /admin/returns
- List: All RETURN_REQUESTED orders
- Actions: Approve | Reject buttons
- Display: Return reason, days since delivery
- Filters: Pending, Approved, Rejected
```

## Testing Checklist - Enhanced

### Scenario 1: Happy Path - Full Return Flow
1. Create order → Pay → Status: CONFIRMED
2. Admin: Update status to DELIVERED
3. User: Click "Request Return" with reason → Status: RETURN_REQUESTED
4. Admin: Approve return → Status: RETURN_APPROVED
5. User: Upload 3 photos + video + description + tracking → Click "Confirm Shipped"
6. Verify: Status → RETURN_SHIPPING, return_shipped_at set
7. Admin: Click "Mark as Received" → Status: RETURN_RECEIVED
8. Admin: Compare evidence, click "Confirm Refund" → Status: REFUND_PENDING
9. Webhook: charge.refunded → Status: REFUNDED
10. Verify: Stock rolled back, refund_amount = subtotal (NO shipping fee)

### Scenario 2: QC Rejection
1-7. Same as Scenario 1
8. Admin: Review product, finds damage not shown in photos
9. Admin: Click "Reject QC" with reason → Status: RETURN_REJECTED
10. Verify: No refund created, user notified

### Scenario 3: 7-Day Limit
1. Create order → Admin: DELIVERED
2. Mock `updated_at` to 8 days ago
3. User: Click "Request Return"
4. Verify: Error "Return window expired"

### Scenario 4: User Abandons Return
1-4. Same as Scenario 1 (status = RETURN_APPROVED)
5. User doesn't upload evidence or ship within 7 days
6. System: Auto-revert to DELIVERED (optional: add cron job)

### Scenario 5: Rejection Before Approval
1. Create order → Admin: DELIVERED
2. User: Request return → RETURN_REQUESTED
3. Admin: Reject with reason
4. Verify: Status reverted to DELIVERED
5. Verify: Rejection reason stored

### Scenario 6: Partial Refund
1-8. Same as Scenario 1 (status = RETURN_RECEIVED)
9. Admin: Notes "slight damage to packaging"
10. Admin: Adjusts refund amount to $12 (original $15.99)
11. Admin: Confirm refund with adjusted amount
12. Verify: Stripe refund = $12.00

## Stock Management

### Automatic Rollback
- Triggered by: `RefundService.handle_refund_succeeded()`
- Calls: `OrderService.rollback_stock_on_cancel(order_id)`
- Increases: `product_size.stock` for each order item
- When: Refund webhook confirms successful

### Manual Rollback (Admin)
- Admin can manually adjust stock via product management
- Independent of refund system

## File Upload Configuration

### Image Upload
- **Service**: Cloudinary (recommended) or AWS S3
- **Max size**: 5MB per image
- **Formats**: JPG, PNG, WEBP
- **Max files**: 5 per order
- **Compression**: Auto-compress to 1920px width
- **Storage path**: `returns/{order_id}/photos/`

### Video Upload
- **Service**: Cloudinary video or Vimeo
- **Max size**: 50MB
- **Formats**: MP4, MOV, AVI
- **Max duration**: 2 minutes
- **Storage path**: `returns/{order_id}/video/`

### Implementation
```python
# Backend endpoint
POST /upload/return-evidence
Body: multipart/form-data
- file: File
- order_id: int
Returns: { "url": "https://..." }

# Frontend
import { uploadToCloudinary } from '@/services/upload';
const photoUrls = await Promise.all(
  files.map(file => uploadToCloudinary(file, 'return-evidence'))
);
```

## Stripe Integration

### Refund Creation
```python
stripe.Refund.create(
    payment_intent=order.payment_intent_id,
    amount=refund_amount_cents,  # Full order amount
    reason="requested_by_customer",
    metadata={"order_id": str(order_id)}
)
```

### Webhook Handling
```python
# Event: charge.refunded
→ RefundService.handle_refund_succeeded(refund_id)
→ Update order: REFUND_PENDING → REFUNDED
→ Set refunded_at timestamp
→ Rollback stock
```

## Error Handling

### Common Errors
```python
# No payment intent
→ "No payment intent found for this order. Cannot process refund."

# Wrong status
→ "Only DELIVERED orders can be returned. Current status: {status}"
→ "Cannot upload evidence. Order status must be RETURN_APPROVED. Current: {status}"
→ "Cannot confirm received. Order status must be RETURN_SHIPPING. Current: {status}"

# Time expired
→ "Return window expired. You can only return orders within 7 days of delivery."

# Already processed
→ "Order is already {status}"

# Not owner
→ "You don't have permission to return this order"

# Evidence validation
→ "At least 1 photo is required"
→ "Maximum 5 photos allowed"
→ "Description is required"
→ "Image file too large. Maximum 5MB per image"
→ "Video file too large. Maximum 50MB"
→ "Video duration exceeds 2 minutes"

# QC errors
→ "Cannot approve refund. Product condition doesn't match evidence."
→ "Refund amount cannot exceed order subtotal"
```

## Files Modified/Created

### Backend - Existing Files Modified
1. `app/models/sqlalchemy/order.py` - Added new status + evidence columns
2. `app/services/refund_service.py` - Enhanced return methods + new endpoints
3. `app/services/order_service.py` - Updated cancel logic
4. `app/routers/order_router.py` - Added new admin + user endpoints
5. `app/schemas/order_schemas.py` - Added evidence fields

### Backend - New Files
6. `app/routers/upload_router.py` - NEW: File upload endpoints
7. `app/services/upload_service.py` - NEW: Cloudinary/S3 integration
8. `alembic/versions/[NEW]_add_return_evidence_fields.py` - NEW: Migration

### Frontend - Existing Files Modified
9. `src/types/Order.ts` - Added evidence fields to IOrder
10. `src/services/Order.ts` - Added new API calls
11. `src/pages/orders/OrderDetailPage.tsx` - Enhanced return UI with evidence upload
12. `src/pages/admin/AdminReturnManagement.tsx` - Added new tabs + evidence display

### Frontend - New Files
13. `src/components/upload/ImageUploadMultiple.tsx` - NEW: Multi-image upload
14. `src/components/upload/VideoUpload.tsx` - NEW: Video upload
15. `src/components/returns/EvidenceGallery.tsx` - NEW: Evidence display component
16. `src/components/returns/QCComparisonView.tsx` - NEW: Side-by-side evidence comparison
17. `src/services/upload.ts` - NEW: Upload utility functions

## Implementation Phases

### Phase 1: Backend Foundation (2-3 hours) ✅ COMPLETED
- [x] Add new status to OrderStatus enum
- [x] Create migration for evidence columns
- [x] Update Order model with new fields
- [x] Modify approve_return() to remove auto-refund
- [x] Add user_confirm_shipped() method
- [x] Add admin_confirm_received() method
- [x] Add admin_confirm_refund() method
- [x] Add reject_qc() method
- [ ] Create upload_router.py with Cloudinary integration (SKIPPED - will mock for now)
- [x] Add new endpoints to order_router.py
- [x] Update schemas with evidence fields

### Phase 2: Frontend Components (2-3 hours) - IN PROGRESS
- [ ] Create ImageUploadMultiple component
- [ ] Create VideoUpload component
- [ ] Create EvidenceGallery component
- [ ] Create QCComparisonView component
- [ ] Setup upload service (Cloudinary SDK)

### Phase 3: Frontend Integration (2 hours)
- [x] Update IOrder interface
- [ ] Add evidence upload UI to OrderDetailPage
- [ ] Add new tabs to AdminReturnManagement
- [ ] Add evidence display in admin view
- [ ] Add QC approval/rejection UI
- [ ] Update status labels and colors

### Phase 4: Testing (1-2 hours)
- [ ] Test happy path (full return flow)
- [ ] Test QC rejection
- [ ] Test evidence validation
- [ ] Test file upload (images + video)
- [ ] Test refund amount calculation
- [ ] Test stock rollback
- [ ] Test 7-day window
- [ ] Test error cases

### Phase 5: Documentation & Deployment
- [ ] Update API documentation
- [ ] Add user guide for returns
- [ ] Add admin guide for QC process
- [ ] Deploy to production
- [ ] Monitor Stripe webhooks

**Total Estimated Time:** 8-12 hours

## Next Steps - Prioritized

1. **HIGH PRIORITY:**
   - ✅ Document enhanced flow (this file)
   - ⏳ Add RETURN_SHIPPING + evidence columns (migration)
   - ⏳ Modify approve_return() logic
   - ⏳ Setup Cloudinary account + upload endpoints

2. **MEDIUM PRIORITY:**
   - ⏳ Build frontend upload components
   - ⏳ Update admin UI with new tabs
   - ⏳ Add user evidence upload flow

3. **LOW PRIORITY (Nice to have):**
   - Auto-revert RETURN_APPROVED after 7 days (cron job)
   - Email notifications at each status change
   - SMS notifications for status updates
   - AI-based photo quality check
   - Integration with shipping APIs for auto-tracking

---

**Implementation Date:** December 12, 2025  
**Developer:** Thang  
**Status:** Planning Complete - Ready for Implementation  
**Next Action:** Start Phase 1 - Backend Foundation
