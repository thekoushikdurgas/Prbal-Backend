
## **Verification System Architecture Overview**

The verification system is built around a comprehensive model-driven architecture with multiple endpoints for different user roles and stages of the verification process.

## **Core Components**

### **1. Data Model (`Verification` in models.py)**

```python
# Key fields and structure:
- verification_type: identity, address, professional, educational, etc.
- document_type: national_id, passport, drivers_license, etc.
- status: unverified → pending → in_progress → verified/rejected/expired
- document storage: document_url, document_back_url
- admin tracking: verified_by, verification_notes
- timestamps: created_at, verified_at, expires_at
```

### **2. User Roles & Permissions**

- **Regular Users**: Can create, view, and cancel their own verifications (`IsVerificationOwner`)
- **Admins**: Can view all verifications and update status (`IsVerificationAdmin`)

## **Complete Verification Flow**

### **Phase 1: Verification Initiation**

**Endpoint**: `POST /users/verify/` (`UserVerificationView`)

**Process**:

1. **User submits verification request** with:
   - `verification_type` (identity, address, professional, etc.)
   - `document_type` (passport, national_id, utility_bill, etc.)
   - `document_link` or `document_back_link` (URLs, base64, files)
   - `document_number` (optional reference)

2. **File Processing** (using `DocumentImageProcessor` from utils.py):

   ```python
   # Handles multiple input formats:
   - URLs → Downloads and validates
   - Base64 data → Decodes and processes
   - Local file paths → Reads and converts
   - Cloud storage references → Processes (placeholder)
   - Direct file uploads → Validates and optimizes
   ```

3. **Validation**:
   - Checks for duplicate pending verifications
   - Validates file formats and sizes
   - Ensures required fields are present

4. **Database Creation**:
   - Creates `Verification` record with status = 'pending'
   - Stores processed documents securely
   - Generates unique UUID for tracking

5. **Notifications** (optional):
   - Notifies user about successful submission
   - Alerts admins about new verification requests

### **Phase 2: Verification Management**

**Base Endpoint**: `/users/verifications/` (`VerificationViewSet`)

#### **User Actions**

**A. List Own Verifications**

- `GET /users/verifications/`
- Uses `VerificationListSerializer`
- Filtered by authenticated user only

**B. View Detailed Verification**

- `GET /users/verifications/{id}/`
- Uses `VerificationDetailSerializer`
- Shows complete verification details

**C. Update Verification** (limited fields)

- `PUT/PATCH /users/verifications/{id}/`
- Uses `VerificationUpdateSerializer`
- Can only update if status is 'pending'

**D. Cancel Verification**

- `POST /users/verifications/{id}/cancel/`
- Changes status to 'cancelled'
- Only allowed for pending/in_progress verifications

#### **Admin Actions**

**A. Mark In Progress**

- `POST /users/verifications/{id}/mark_in_progress/`
- Status: pending → in_progress
- Can add verification notes

**B. Mark Verified**

- `POST /users/verifications/{id}/mark_verified/`
- Status: in_progress → verified
- Sets verification timestamp and expiry
- Updates user's verification status

**C. Mark Rejected**

- `POST /users/verifications/{id}/mark_rejected/`
- Status: any → rejected
- Requires rejection reason
- Preserves admin notes

**D. Status Summary**

- `GET /users/verifications/status_summary/`
- Admin-only dashboard view
- Shows counts by status and type

### **Phase 3: File Processing Architecture**

The system uses a sophisticated file processing pipeline:

```python
# DocumentImageProcessor workflow:
1. Input Detection:
   - URLs (http/https)
   - Base64 data (with/without data URI)
   - Local file paths
   - Cloud storage references
   - Direct file objects

2. Processing:
   - Downloads/decodes/reads file
   - Validates content type and size
   - Generates secure filename
   - Optimizes images (resize, compress)

3. Storage:
   - Saves to Django FileField
   - Uses secure upload paths
   - Maintains metadata
```

### **Phase 4: Status State Machine**

```python
# Verification Status Flow:
unverified → pending → in_progress → verified ✓
                ↓         ↓
              rejected   cancelled
                ↓
             expired (after expiry_days)
```

## **Key Features**

### **1. Multi-format Document Support**

- Direct file uploads
- URL-based document links
- Base64 encoded documents
- Cloud storage references (extensible)

### **2. Security Features**

- Secure file upload paths with UUIDs
- Content type validation
- File size limits
- User isolation (can't see others' verifications)

### **3. Admin Control**

- Comprehensive status management
- Detailed audit trail
- Bulk status summaries
- Notes and rejection reasons

### **4. Error Handling**

- Standardized response format using `StandardizedResponseHelper`
- Comprehensive logging at debug/info/warning/error levels
- Graceful failure handling for file processing

### **5. Extensibility**

- Multiple verification types supported
- Multiple document types per verification type
- JSON metadata field for additional data
- External integration support via `external_reference_id`

## **Database Relationships**

```python
User (1) ←→ (Many) Verification
User (1) ←→ (Many) Verification (as verified_by admin)

# Constraints:
- Unique together: (user, verification_type, document_type)
- Prevents duplicate verifications of same type
```

## **API Response Format**

All endpoints use standardized responses:

```python
{
    "message": "Success/Error message",
    "data": { ... },
    "time": "ISO timestamp",
    "statusCode": 200/400/500
}
```

This architecture provides a robust, secure, and scalable verification system that can handle various document types, multiple input formats, and comprehensive admin controls while maintaining clear separation of concerns between user and admin functionalities.
