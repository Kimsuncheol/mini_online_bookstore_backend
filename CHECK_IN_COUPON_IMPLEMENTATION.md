# Check-In and Coupon System Implementation

## Overview
This document summarizes the implementation of the Check-In and Coupon systems for the Mini Online Bookstore Backend API.

## Files Created

### Models (`app/models/`)

#### 1. `check_in.py`
Pydantic models for check-in functionality:
- **CheckInRecord**: Single daily check-in record
- **CheckInStats**: User's check-in statistics (streaks, totals)
- **CheckInBase/Create/Update**: Base models for CRUD operations
- **CheckIn**: Complete check-in document with metadata
- **CheckInResponse**: Response model for check-in operations
- **CheckInProfile**: Comprehensive user check-in profile with stats and records

#### 2. `coupon.py`
Pydantic models for coupon management:
- **CouponCreate**: Model for creating new coupons
- **CouponUpdate**: Model for updating coupons
- **CouponBase/Coupon**: Base and complete coupon models
- **CouponSummary**: Summary model for coupon listings
- **CouponIssueRecord**: Track coupon issue records for streak milestones
- **CouponResponse**: Generic coupon response model

### Services (`app/services/`)

#### 1. `check_in_service.py`
Business logic for check-in operations:
- **CheckInService** class with methods:
  - `create_or_update_check_in()`: Handle daily check-ins with streak calculation
  - `get_check_in_stats()`: Retrieve user statistics
  - `get_user_check_in_profile()`: Get comprehensive profile with records
  - `get_check_in_records()`: Fetch historical check-in records
  - `reset_daily_flags()`: Reset daily flags for all users (scheduled task)
  - Helper methods for streak calculation and coupon milestone detection

#### 2. `coupon_service.py`
Business logic for coupon operations:
- **CouponService** class with methods:
  - **CRUD Operations**: Create, read, update, delete coupons
  - **Usage Operations**: Mark coupons as used with expiration validation
  - **Issue Operations**: Mark coupons as issued to users
  - **Issue Records**: Track milestone-based coupon issuance
  - Helper methods for document conversion and validation

### Routers (`app/routers/`)

#### 1. `check_in.py`
API endpoints for check-in functionality:
- `POST /api/check-in/check-in`: Check-in a user for today
- `GET /api/check-in/stats/{user_email}`: Get check-in statistics
- `GET /api/check-in/profile/{user_id}`: Get complete check-in profile
- `GET /api/check-in/records/{user_email}`: Get check-in records (with configurable days)
- `POST /api/check-in/reset-daily-flags`: Reset daily flags for all users

#### 2. `coupon.py`
API endpoints for coupon management:
- **CRUD Endpoints**:
  - `POST /api/coupons`: Create coupon
  - `GET /api/coupons`: Get user's coupons (with active_only filter)
  - `GET /api/coupons/{coupon_id}`: Get specific coupon
  - `PATCH /api/coupons/{coupon_id}`: Update coupon
  - `DELETE /api/coupons/{coupon_id}`: Delete coupon

- **Usage Endpoints**:
  - `POST /api/coupons/{coupon_id}/use`: Mark coupon as used
  - `POST /api/coupons/{coupon_id}/issue`: Mark coupon as issued

- **Issue Record Endpoints**:
  - `POST /api/coupons/issue-records`: Create coupon issue record for milestone
  - `GET /api/coupons/issue-records/{user_email}`: Get issue records for user

### Configuration

#### Updated `main.py`
- Added imports for check_in and coupon routers
- Registered both routers with the FastAPI application

## API Features

### Check-In System
- **Daily Check-in Tracking**: Records user check-ins with date tracking
- **Streak Management**: Automatically calculates and maintains:
  - Current streak (consecutive check-in days)
  - Longest streak (personal record)
  - Total check-in count
- **Milestone Detection**: Identifies coupon earning milestones (7, 14, 30 days)
- **Historical Records**: Stores daily check-in records in a subcollection
- **Scheduled Reset**: Supports resetting daily flags via scheduled tasks

### Coupon System
- **Coupon Creation**: Support for manual, promotional, and check-in source coupons
- **Coupon Tracking**: Monitor coupon usage and expiration status
- **Expiration Validation**: Validates coupon expiration dates on usage
- **Ownership Verification**: Ensures users can only access their own coupons
- **Milestone Tracking**: Records which users have earned coupons at specific streak milestones
- **Active Coupon Filtering**: Can retrieve only active (unused, non-expired) coupons

## Database Structure

### Firestore Collections

#### `check_ins` (Document per user email)
```
{
  "user_id": string,
  "user_name": string,
  "current_streak": number,
  "longest_streak": number,
  "total_check_ins": number,
  "last_check_in_date": string (YYYY-MM-DD),
  "checked_in_today": boolean,
  "created_at": timestamp,
  "updated_at": timestamp
}
```

#### `check_ins/{user_email}/check_in_records` (Document per date)
```
{
  "date": string (YYYY-MM-DD),
  "checked_in": boolean,
  "timestamp": timestamp
}
```

#### `coupons` (Collection)
```
{
  "code": string,
  "user_id": string,
  "user_email": string,
  "discount_value": number,
  "source": "check_in" | "promotion" | "manual",
  "description": string,
  "used": boolean,
  "used_date": string (YYYY-MM-DD),
  "issued": boolean,
  "issued_date": string (YYYY-MM-DD),
  "expiration_date": string (YYYY-MM-DD),
  "created_at": timestamp,
  "updated_at": timestamp
}
```

#### `coupon_issue_records` (Collection)
```
{
  "user_id": string,
  "user_email": string,
  "streak_days": number (7, 14, 30, etc),
  "coupon_value": number,
  "coupon_id": string (nullable),
  "issued": boolean,
  "issued_at": timestamp (nullable),
  "created_at": timestamp
}
```

## Error Handling

All endpoints implement proper error handling:
- **400 Bad Request**: Invalid input data or missing required fields
- **404 Not Found**: Resource not found or user unauthorized
- **500 Internal Server Error**: Database or service errors with descriptive messages

## Integration Notes

1. **Firebase Integration**: Uses existing `get_firestore_client()` from firebase_config
2. **Pydantic Models**: Full type validation and serialization support
3. **CORS Enabled**: Endpoints are accessible from the frontend
4. **API Documentation**: FastAPI automatically generates OpenAPI documentation

## Usage Examples

### Check-In a User
```bash
POST /api/check-in/check-in?user_id=123&user_email=user@example.com&user_name=John
```

### Get User Coupons
```bash
GET /api/coupons?user_email=user@example.com&active_only=true
```

### Use a Coupon
```bash
POST /api/coupons/{coupon_id}/use?user_email=user@example.com
```

### Create Coupon Issue Record
```bash
POST /api/coupons/issue-records?user_id=123&user_email=user@example.com&streak_days=7&coupon_value=2.0
```

## Testing

All Python files have been verified for syntax correctness:
```bash
python3 -m py_compile app/models/check_in.py
python3 -m py_compile app/models/coupon.py
python3 -m py_compile app/services/check_in_service.py
python3 -m py_compile app/services/coupon_service.py
python3 -m py_compile app/routers/check_in.py
python3 -m py_compile app/routers/coupon.py
python3 -m py_compile main.py
```

All files compile successfully without syntax errors.
