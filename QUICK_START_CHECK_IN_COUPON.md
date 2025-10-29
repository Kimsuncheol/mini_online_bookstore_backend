# Quick Start Guide: Check-In and Coupon System

## Implementation Complete ✓

All backend API endpoints for check-in and coupon management have been successfully implemented.

## New Endpoints Summary

### Check-In Endpoints

1. **Check-In User**
   - `POST /api/check-in/check-in`
   - Params: `user_id`, `user_email`, `user_name`
   - Response: Statistics and earned coupons

2. **Get Check-In Stats**
   - `GET /api/check-in/stats/{user_email}`
   - Response: Current streak, longest streak, total check-ins

3. **Get User Profile**
   - `GET /api/check-in/profile/{user_id}`
   - Params: `user_email`, `user_name`
   - Response: Complete profile with stats and records

4. **Get Check-In Records**
   - `GET /api/check-in/records/{user_email}`
   - Params: `days` (optional, default 90)
   - Response: Historical daily records

5. **Reset Daily Flags** (Admin/Scheduled)
   - `POST /api/check-in/reset-daily-flags`
   - Response: Updated user count

### Coupon Endpoints

1. **Create Coupon**
   - `POST /api/coupons`
   - Params: `user_id`, `user_email`
   - Body: `code`, `discount_value`, `source`, `description`, `expiration_date`

2. **Get User Coupons**
   - `GET /api/coupons`
   - Params: `user_email`, `active_only` (optional)
   - Response: List of coupons with count

3. **Get Specific Coupon**
   - `GET /api/coupons/{coupon_id}`
   - Params: `user_email`

4. **Update Coupon**
   - `PATCH /api/coupons/{coupon_id}`
   - Params: `user_email`
   - Body: Fields to update

5. **Delete Coupon**
   - `DELETE /api/coupons/{coupon_id}`
   - Params: `user_email`

6. **Use Coupon**
   - `POST /api/coupons/{coupon_id}/use`
   - Params: `user_email`
   - Validates expiration and usage status

7. **Issue Coupon**
   - `POST /api/coupons/{coupon_id}/issue`
   - Params: `user_id`, `user_email`

8. **Create Issue Record** (For Milestones)
   - `POST /api/coupons/issue-records`
   - Params: `user_id`, `user_email`, `streak_days`, `coupon_value`

9. **Get Issue Records**
   - `GET /api/coupons/issue-records/{user_email}`
   - Response: All milestone records for user

## Key Features

### Streak Logic
- **Day 1**: Current streak = 1
- **Consecutive**: Streak continues if check-in on consecutive day
- **Broken**: Resets to 1 if gap in check-ins
- **Milestones**: Coupons earned at 7, 14, and 30 day streaks
  - 7 days → $2.00 coupon
  - 14 days → $4.00 coupon
  - 30 days → $10.00 coupon

### Coupon Features
- Sources: `check_in`, `promotion`, `manual`
- Status tracking: `used`, `issued`, `expired`
- Ownership verification (user-specific)
- Expiration date validation
- Automatic filtering for active coupons

## File Structure

```
app/
├── models/
│   ├── check_in.py          (New)
│   └── coupon.py            (New)
├── services/
│   ├── check_in_service.py  (New)
│   └── coupon_service.py    (New)
└── routers/
    ├── check_in.py          (New)
    └── coupon.py            (New)

main.py (Updated)
CHECK_IN_COUPON_IMPLEMENTATION.md (New)
QUICK_START_CHECK_IN_COUPON.md (New - This file)
```

## Testing with cURL

```bash
# Check-in a user
curl -X POST "http://localhost:8000/api/check-in/check-in?user_id=123&user_email=test@example.com&user_name=John"

# Get check-in stats
curl "http://localhost:8000/api/check-in/stats/test@example.com"

# Create a coupon
curl -X POST "http://localhost:8000/api/coupons?user_id=123&user_email=test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"code":"SUMMER2024","discount_value":10.0,"source":"manual","description":"Summer promotion"}'

# Get user coupons
curl "http://localhost:8000/api/coupons?user_email=test@example.com&active_only=true"

# Use a coupon
curl -X POST "http://localhost:8000/api/coupons/{coupon_id}/use?user_email=test@example.com"
```

## Database Collections

The system automatically creates these Firestore collections:

1. **check_ins**: User check-in records (document per email)
   - Subcollection: `check_in_records` (document per date)

2. **coupons**: All coupons (documents per coupon)

3. **coupon_issue_records**: Milestone tracking (documents per milestone)

## Error Handling

- **400**: Invalid input or missing required fields
- **404**: Resource not found or unauthorized access
- **500**: Database errors with descriptive messages

## Integration Notes

✓ Firebase Firestore integration  
✓ Pydantic validation  
✓ CORS enabled  
✓ OpenAPI documentation auto-generated  
✓ Error handling implemented  
✓ Type hints throughout  

## Next Steps

1. Test endpoints with your frontend
2. Implement a scheduled task for `/api/check-in/reset-daily-flags` (daily at 00:00)
3. Configure coupon/check-in UI components in your React frontend
4. Monitor Firestore for data integrity

