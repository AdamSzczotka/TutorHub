# Phase 12 - Sprint 12.2: Documentation

## Tasks 148-152: Complete System Documentation

> **Duration**: Week 16 (Second half of Phase 12)
> **Goal**: Comprehensive documentation for API, users, deployment, and disaster recovery
> **Dependencies**: All phases completed (Tasks 0-147)

---

## 📋 SPRINT OVERVIEW

| Task ID | Description                             | Priority | Estimated Time | Dependencies    |
| ------- | --------------------------------------- | -------- | -------------- | --------------- |
| 148     | API documentation (tRPC procedures)     | Critical | 6h             | All features    |
| 149     | User manuals (Admin/Tutor/Student)      | Critical | 8h             | All UI complete |
| 150     | Deployment & operations guide           | Critical | 5h             | Infrastructure  |
| 151     | Database schema documentation           | High     | 4h             | Schema final    |
| 152     | Disaster recovery & rollback procedures | High     | 5h             | Deployment      |

**Total Estimated Time**: 28 hours

---

## 🎯 DETAILED TASK BREAKDOWN

### Task 148: API Documentation (tRPC Procedures)

**Files**: `docs/api/`, `docs/api/procedures/`, `docs/api/authentication.md`
**Reference**: DevelopmentRoadmap.md task 148

#### API Documentation Structure:

````markdown
<!-- docs/api/README.md -->

# Na Piątkę - API Documentation

## Overview

This system uses tRPC v11.4.3 for type-safe API communication between the Next.js frontend and backend.

**Base URL**: `/api/trpc`
**Authentication**: JWT sessions via NextAuth.js v5

## Available Routers

- [Authentication](./authentication.md) - Login, logout, session management
- [User Management](./procedures/userManagement.md) - CRUD operations for users
- [Events](./procedures/events.md) - Lesson scheduling and management
- [Attendance](./procedures/attendance.md) - Attendance tracking
- [Cancellations](./procedures/cancellations.md) - Lesson cancellation workflow
- [Invoices](./procedures/invoicing.md) - Billing and invoicing
- [Messages](./procedures/messages.md) - Internal messaging
- [Notifications](./procedures/notifications.md) - System notifications

## Authentication Flow

All API calls require authentication except for the login endpoint.

### Session Structure

```typescript
{
  user: {
    id: string;
    email: string;
    name: string;
    surname: string;
    role: 'ADMIN' | 'TUTOR' | 'STUDENT';
  }
  expires: string;
}
```
````

### Authorization Levels

- **Public Procedures**: No authentication required
- **Protected Procedures**: Authenticated user required
- **Admin Procedures**: ADMIN role required
- **Tutor Procedures**: TUTOR or ADMIN role required
- **Student Procedures**: STUDENT, TUTOR, or ADMIN role required

## Error Codes

| Code                  | Description                          |
| --------------------- | ------------------------------------ |
| UNAUTHORIZED          | Not authenticated                    |
| FORBIDDEN             | Insufficient permissions             |
| BAD_REQUEST           | Invalid input data                   |
| NOT_FOUND             | Resource not found                   |
| CONFLICT              | Resource conflict (e.g., scheduling) |
| INTERNAL_SERVER_ERROR | Server error                         |

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Login**: 5 requests per minute per IP
- **Admin operations**: 200 requests per minute

## Examples

### Using tRPC Client (React)

```typescript
import { api } from '~/utils/api';

function MyComponent() {
  // Query
  const { data, isLoading } = api.event.getAll.useQuery();

  // Mutation
  const createEvent = api.event.create.useMutation({
    onSuccess: () => {
      console.log('Event created!');
    },
  });

  return (
    <button onClick={() => createEvent.mutate({ title: 'New Event' })}>
      Create Event
    </button>
  );
}
```

### Direct HTTP Call

```bash
POST /api/trpc/event.create
Content-Type: application/json
Authorization: Bearer <session-token>

{
  "title": "Matematyka - funkcje",
  "subjectId": "uuid",
  "tutorId": "uuid",
  "startTime": "2025-09-15T14:00:00Z",
  "endTime": "2025-09-15T15:00:00Z",
  "studentIds": ["uuid1", "uuid2"]
}
```

````

#### Event Router Documentation:

```markdown
<!-- docs/api/procedures/events.md -->
# Events API

## Procedures

### `event.getAll`

Fetch all events with optional filters.

**Type**: Query
**Auth**: Protected
**Input**:

```typescript
{
  startDate?: Date;
  endDate?: Date;
  tutorId?: string;
  studentId?: string;
  roomId?: string;
  status?: "SCHEDULED" | "ONGOING" | "COMPLETED" | "CANCELLED";
}
````

**Output**:

```typescript
Array<{
  id: string;
  title: string;
  description?: string;
  startTime: Date;
  endTime: Date;
  status: EventStatus;
  isGroupLesson: boolean;
  maxParticipants?: number;
  subject: {
    id: string;
    name: string;
  };
  level: {
    id: string;
    name: string;
  };
  tutor: {
    id: string;
    name: string;
    surname: string;
  };
  room?: {
    id: string;
    name: string;
  };
  eventStudents: Array<{
    studentId: string;
    attendanceStatus?: string;
  }>;
}>;
```

**Example**:

```typescript
const { data: events } = api.event.getAll.useQuery({
  startDate: new Date('2025-09-01'),
  endDate: new Date('2025-09-30'),
  tutorId: 'tutor-uuid',
});
```

---

### `event.create`

Create a new event (lesson).

**Type**: Mutation
**Auth**: Admin or Tutor
**Input**:

```typescript
{
  title: string; // min 1, max 100 chars
  description?: string;
  subjectId: string; // UUID
  levelId: string; // UUID
  tutorId: string; // UUID
  roomId?: string; // UUID
  startTime: Date;
  endTime: Date; // must be after startTime
  isGroupLesson: boolean;
  maxParticipants?: number; // 1-20, required if isGroupLesson
  studentIds: string[]; // at least 1 student
  color?: string; // hex color (#RRGGBB)
}
```

**Output**:

```typescript
{
  id: string;
  title: string;
  // ... full event object
}
```

**Errors**:

- `BAD_REQUEST`: Invalid input (validation errors)
- `CONFLICT`: Scheduling conflict (tutor/room already booked)
- `FORBIDDEN`: Room capacity exceeded

**Example**:

```typescript
const createEvent = api.event.create.useMutation({
  onSuccess: (event) => {
    console.log('Created event:', event.id);
  },
  onError: (error) => {
    console.error('Failed to create event:', error.message);
  },
});

createEvent.mutate({
  title: 'Matematyka - funkcje kwadratowe',
  subjectId: 'math-subject-id',
  levelId: 'level-5-id',
  tutorId: 'tutor-id',
  roomId: 'room-a-id',
  startTime: new Date('2025-09-15T14:00:00'),
  endTime: new Date('2025-09-15T15:00:00'),
  isGroupLesson: false,
  studentIds: ['student-id-1'],
});
```

---

### `event.update`

Update an existing event.

**Type**: Mutation
**Auth**: Admin or event's Tutor
**Input**:

```typescript
{
  id: string; // UUID
  title?: string;
  description?: string;
  startTime?: Date;
  endTime?: Date;
  roomId?: string;
  color?: string;
  // Cannot change: subjectId, levelId, tutorId
}
```

**Output**: Updated event object

**Example**:

```typescript
const updateEvent = api.event.update.useMutation();

updateEvent.mutate({
  id: 'event-id',
  startTime: new Date('2025-09-15T15:00:00'),
  endTime: new Date('2025-09-15T16:00:00'),
});
```

---

### `event.delete`

Delete an event (soft delete).

**Type**: Mutation
**Auth**: Admin only
**Input**:

```typescript
{
  id: string; // UUID
}
```

**Output**: `{ success: boolean }`

---

### `event.checkConflicts`

Check for scheduling conflicts before creating/updating events.

**Type**: Query
**Auth**: Protected
**Input**:

```typescript
{
  eventId?: string; // Exclude this event from conflict check
  tutorId: string;
  roomId?: string;
  startTime: Date;
  endTime: Date;
}
```

**Output**: Array of conflicting events

**Example**:

```typescript
const { data: conflicts } = api.event.checkConflicts.useQuery({
  tutorId: 'tutor-id',
  roomId: 'room-id',
  startTime: new Date('2025-09-15T14:00:00'),
  endTime: new Date('2025-09-15T15:00:00'),
});

if (conflicts.length > 0) {
  console.log('Conflicts detected:', conflicts);
}
```

---

### `event.getStudentSchedule`

Get a student's personal schedule.

**Type**: Query
**Auth**: Student (own schedule) or Admin/Tutor
**Input**:

```typescript
{
  studentId: string;
  startDate?: Date;
  endDate?: Date;
}
```

**Output**: Array of events for the student

---

### `event.getTutorSchedule`

Get a tutor's teaching schedule.

**Type**: Query
**Auth**: Tutor (own schedule) or Admin
**Input**:

```typescript
{
  tutorId: string;
  startDate?: Date;
  endDate?: Date;
}
```

**Output**: Array of events for the tutor

````

#### Complete API Procedure Templates:

Create similar documentation files for:

- `docs/api/procedures/userManagement.md`
- `docs/api/procedures/attendance.md`
- `docs/api/procedures/cancellations.md`
- `docs/api/procedures/invoicing.md`
- `docs/api/procedures/messages.md`
- `docs/api/procedures/notifications.md`

**Validation**:

- All API endpoints documented
- Examples provided for each procedure
- Error codes clearly defined
- Input/output types specified

---

### Task 149: User Manuals (Admin/Tutor/Student)

**Files**: `docs/user-guides/`, `docs/user-guides/admin/`, `docs/user-guides/tutor/`, `docs/user-guides/student/`
**Reference**: DevelopmentRoadmap.md task 149

#### Admin User Guide:

```markdown
<!-- docs/user-guides/admin/README.md -->
# Admin User Guide - Na Piątkę

## Overview

This guide covers all administrative functions in the Na Piątkę tutoring management system.

**Target Audience**: System administrators
**Access Level**: Full system access

## Table of Contents

1. [Getting Started](#getting-started)
2. [User Management](#user-management)
3. [Lesson Scheduling](#lesson-scheduling)
4. [Attendance Management](#attendance-management)
5. [Cancellation Approval](#cancellation-approval)
6. [Invoicing](#invoicing)
7. [Reports & Analytics](#reports-analytics)
8. [System Settings](#system-settings)

---

## Getting Started

### First Login

1. Navigate to `https://napiatke.pl/auth/login`
2. Enter your admin credentials
3. Click "Zaloguj się"
4. You'll be redirected to the admin dashboard

**Default Admin Account**:
- Email: admin@napiatke.pl
- Password: (provided separately)

**Security Notes**:
- Change your password immediately after first login
- Enable 2FA if available
- Never share your admin credentials

### Dashboard Overview

The admin dashboard displays:

- **Total Users**: Current count of active users
- **Today's Lessons**: Scheduled lessons for today
- **Pending Cancellations**: Awaiting your approval
- **Monthly Revenue**: Current month's invoicing status
- **Recent Activity**: Latest system events

![Admin Dashboard Screenshot](../screenshots/admin-dashboard.png)

---

## User Management

### Creating a New User

**Direct user creation** is the ONLY way to add users (no public registration).

#### Creating a Student

1. Navigate to **Users** → **Add User**
2. Select role: **Student**
3. Fill in required fields:
   - Email (must be unique)
   - First Name
   - Last Name
   - Class (1-8, liceum)
4. Fill in parent information:
   - Parent Name
   - Parent Email (for invoices)
   - Parent Phone
5. Click **Create User**
6. **IMPORTANT**: Copy the temporary password shown in the modal
7. Send credentials to student/parent via email

**What Happens Next**:
- User receives welcome email with temporary password
- First login forces password change
- Student must complete profile (emergency contacts)

#### Creating a Tutor

1. Navigate to **Users** → **Add User**
2. Select role: **Tutor**
3. Fill in required fields:
   - Email
   - First Name
   - Last Name
   - Bio (experience description)
   - Years of Experience
   - Hourly Rate (PLN)
4. Select subjects and levels the tutor can teach
5. Click **Create User**
6. Copy temporary password and send to tutor

**First Login for Tutors**:
- Change password
- Complete profile (photo, detailed bio)
- Set availability hours

### Managing Existing Users

#### Viewing All Users

1. Navigate to **Users** → **All Users**
2. Use filters:
   - Role (Admin/Tutor/Student)
   - Active/Inactive
   - Search by name or email

#### Editing User Information

1. Click on user in the list
2. Click **Edit** button
3. Modify allowed fields:
   - Contact information
   - Profile details
   - Role-specific data
4. Click **Save Changes**

**Note**: Cannot change email after creation

#### Deactivating a User

1. Open user details
2. Click **Deactivate Account**
3. Confirm action
4. User can no longer log in
5. Historical data is preserved

**Reactivating**: Use the same process and click **Activate Account**

#### Resetting User Password

1. Open user details
2. Click **Reset Password**
3. New temporary password is generated
4. Copy password and send to user
5. User must change password on next login

**Use Cases**:
- User forgot password
- Suspected account compromise
- User reports login issues

### User Data Export (RODO Compliance)

1. Open user details
2. Click **Export User Data**
3. Select format (JSON/PDF)
4. Download includes:
   - Personal information
   - Activity history
   - Attendance records
   - Invoices
   - Messages

**Legal Requirement**: Must fulfill data export requests within 30 days

---

## Lesson Scheduling

### Calendar Overview

The admin calendar provides a complete view of all scheduled lessons.

**Views Available**:
- Day View: Hour-by-hour schedule
- Week View: 7-day overview
- Month View: Monthly planning
- Resource View: By room or tutor

### Creating a New Lesson

#### Method 1: Click on Calendar

1. Open **Calendar**
2. Click on empty time slot
3. Event creation modal opens
4. Fill in details:
   - Title (e.g., "Matematyka - funkcje")
   - Subject
   - Level (class)
   - Tutor
   - Room (optional for online lessons)
   - Start/End time
   - Group lesson? (checkbox)
   - Max participants (if group)
5. Select students:
   - Click "Select Students"
   - Check student names
   - For group lessons, respect max participants
6. Click **Create Event**

**System Validation**:
- Checks for tutor conflicts
- Checks for room conflicts
- Validates room capacity
- Ensures students have no overlapping lessons

#### Method 2: Bulk Import

For scheduling multiple lessons:

1. Navigate to **Calendar** → **Bulk Import**
2. Download CSV template
3. Fill in lesson details
4. Upload CSV
5. Review and confirm

### Editing Lessons

#### Drag & Drop

1. Click and hold event on calendar
2. Drag to new time slot
3. Release mouse
4. Conflict check runs automatically
5. If no conflicts, lesson is moved
6. All participants receive notifications

#### Edit Modal

1. Click on event
2. Click **Edit**
3. Modify details
4. Click **Save Changes**

**Note**: Changing tutor/subject requires admin approval

### Recurring Lessons

For weekly lessons:

1. Create lesson as normal
2. Check **Recurring Event**
3. Select pattern:
   - Daily
   - Weekly (most common)
   - Monthly
4. Set end date or number of occurrences
5. Click **Create Recurring**

**System Creates**:
- Individual events for each occurrence
- Students automatically assigned to all
- Invoicing calculated for all occurrences

### Cancelling Lessons

**Admin-Initiated Cancellation**:

1. Click on event
2. Click **Cancel Lesson**
3. Select reason:
   - Tutor unavailable
   - Room unavailable
   - School holiday
   - Other (specify)
4. Choose action:
   - Cancel and reschedule
   - Cancel permanently
5. Click **Confirm Cancellation**

**What Happens**:
- Event marked as CANCELLED
- Students notified via email
- Tutor notified
- Invoice adjusted automatically
- If rescheduling, students added to makeup queue

---

## Cancellation Approval

Students can request lesson cancellations (24h minimum notice). Admin must approve/reject.

### Viewing Pending Requests

1. Navigate to **Cancellations** → **Pending Requests**
2. List shows:
   - Student name
   - Lesson details
   - Request date
   - Cancellation reason
   - Days until lesson

### Approving a Cancellation

1. Click on request
2. Review details:
   - Student's reason
   - Lesson information
   - Student's cancellation history
3. Add admin comment (optional but recommended)
4. Click **Approve**

**What Happens**:
- Lesson cancelled
- Student notified
- Added to makeup lessons queue
- 30-day countdown starts
- Invoice adjusted

**Admin Comment Examples**:
- "Approved - medical certificate provided"
- "Approved - family emergency"
- "Approved - school conflict"

### Rejecting a Cancellation

1. Click on request
2. Add reason for rejection (required)
3. Click **Reject**

**What Happens**:
- Request marked as rejected
- Student notified with your reason
- Lesson remains scheduled
- Student still expected to attend

**Common Rejection Reasons**:
- Requested too late (<24h notice)
- Exceeded monthly cancellation limit
- Invalid reason
- Already rescheduled this lesson

### Makeup Lesson Management

#### Viewing Makeup Queue

1. Navigate to **Cancellations** → **Makeup Lessons**
2. Filter by:
   - Student
   - Subject
   - Days remaining (expiration)
   - Status

#### Extending Expiration

If student needs more than 30 days:

1. Click on makeup lesson
2. Click **Extend Deadline**
3. Add days (e.g., 7, 14, 30)
4. Add reason for extension
5. Click **Confirm**

**Limits**: Maximum 60 days total

#### Manual Rescheduling

If student requests your help:

1. Click on makeup lesson
2. Click **Reschedule**
3. Find available slot in calendar
4. Ensure tutor and room available
5. Click **Schedule**

---

## Invoicing

Automated monthly invoicing runs on the 25th of each month.

### Monthly Invoice Generation

**Automatic Process**:
1. System collects next month's scheduled lessons per student
2. Calculates: hours × tutor's hourly rate
3. Adds 23% VAT
4. Generates sequential invoice number (FV/2025/09/001)
5. Creates PDF
6. Emails to parent

**Manual Generation** (if needed):

1. Navigate to **Invoicing** → **Generate Invoice**
2. Select student
3. Select month/year
4. Review lessons included
5. Click **Generate**

### Viewing Invoices

1. Navigate to **Invoicing** → **All Invoices**
2. Filter by:
   - Student
   - Month/Year
   - Payment status
   - Due date

### Invoice Corrections

For cancelled lessons:

1. Open invoice
2. Click **Create Correction Note**
3. Select lessons to remove
4. System calculates credit amount
5. Click **Generate Correction**

**Note**: Original invoice preserved for audit trail

### Payment Tracking

#### Marking as Paid

1. Open invoice
2. Click **Mark as Paid**
3. Enter:
   - Payment date
   - Payment method (bank transfer, cash, etc.)
   - Transaction reference
4. Click **Confirm**

#### Overdue Management

System automatically sends reminders:
- 3 days after due date
- 7 days after due date
- 14 days after due date

**Manual Reminder**:

1. Open overdue invoice
2. Click **Send Reminder**
3. Email sent to parent

---

## Reports & Analytics

### Dashboard Statistics

Real-time widgets:
- Total users by role
- Active lessons this week
- Revenue this month
- Attendance rate

### Attendance Reports

1. Navigate to **Reports** → **Attendance**
2. Select date range
3. Filter by:
   - Student
   - Tutor
   - Subject
   - Class level
4. Click **Generate Report**

**Export Options**: CSV, Excel, PDF

### Revenue Reports

1. Navigate to **Reports** → **Revenue**
2. Select month/year or custom range
3. View breakdown by:
   - Subject
   - Tutor
   - Student
   - Class level
4. Export as needed

### User Activity Logs

For audit purposes:

1. Navigate to **System** → **Audit Logs**
2. Filter by:
   - User
   - Action type (create, update, delete)
   - Date range
3. View detailed activity

**Logs Include**:
- User creation
- Password resets
- Role changes
- Invoice generation
- Lesson cancellations

---

## System Settings

### Subjects & Levels

#### Adding a Subject

1. Navigate to **Settings** → **Subjects**
2. Click **Add Subject**
3. Enter:
   - Subject name (Polish)
   - Icon (optional)
   - Color code
4. Click **Save**

#### Managing Subject-Level Relationships

1. Open subject
2. Click **Manage Levels**
3. Check applicable levels:
   - Klasa 1-8
   - Liceum
4. Click **Save**

### Rooms Management

1. Navigate to **Settings** → **Rooms**
2. Click **Add Room**
3. Enter:
   - Room name
   - Location (address or "Online")
   - Capacity (max students)
   - Equipment (JSON: projector, whiteboard, etc.)
4. Click **Save**

### Email Templates

Customize automated emails:

1. Navigate to **Settings** → **Email Templates**
2. Select template type:
   - Welcome Email
   - Password Reset
   - Lesson Reminder
   - Cancellation Notification
   - Invoice Email
3. Edit HTML template
4. Use variables: `{{userName}}`, `{{lessonDate}}`, etc.
5. Click **Save**

### System Configuration

1. Navigate to **Settings** → **System**
2. Configure:
   - Business hours (calendar defaults)
   - Cancellation policy (24h minimum)
   - Invoice due date (days after generation)
   - Late payment fee
   - Email sender name/address
3. Click **Save Changes**

---

## Troubleshooting

### User Can't Log In

1. Verify account is active
2. Check email address spelling
3. Reset password
4. Check browser cookies/cache
5. Try different browser

### Lesson Won't Schedule

1. Check for conflicts (tutor/room)
2. Verify room capacity
3. Ensure time makes sense (end > start)
4. Check student availability

### Invoice Not Generated

1. Verify student has scheduled lessons next month
2. Check tutor hourly rate is set
3. Review error logs in System → Logs
4. Manually generate if needed

### Email Not Sending

1. Check RESEND_API_KEY in env variables
2. Verify email template exists
3. Check spam folder
4. Review email queue in System → Email Queue

---

## Support & Feedback

For technical issues or feature requests:
- Email: support@napiatke.pl
- Documentation: https://docs.napiatke.pl
- Issue Tracker: GitHub Issues
````

#### Tutor User Guide:

```markdown
<!-- docs/user-guides/tutor/README.md -->

# Tutor User Guide - Na Piątkę

## Overview

Welcome to Na Piątkę! This guide will help you manage your lessons, track student attendance, and communicate with students and parents.

## Getting Started

### First Login

Your admin has created your account and sent you credentials.

1. Check your email for welcome message
2. Click login link or go to https://napiatke.pl/auth/login
3. Enter your email and temporary password
4. You'll be prompted to change your password
5. Complete your profile

### Profile Setup

#### Personal Information

1. Navigate to **Profile**
2. Upload profile photo (recommended)
3. Update bio (this is shown to students/parents)
4. Add education background
5. List certifications or achievements

#### Subjects & Levels

1. Go to **Profile** → **Teaching**
2. Select subjects you teach
3. For each subject, select levels:
   - Elementary (Klasa 1-4)
   - Middle School (Klasa 5-8)
   - High School (Liceum)

#### Hourly Rate

Your hourly rate is set by admin. If you believe it should be adjusted, contact your administrator.

#### Availability

Set your general availability:

1. Go to **Profile** → **Availability**
2. For each day of week, set:
   - Available times
   - Break times
   - Blackout periods

**Note**: This is for planning purposes. Admin can still schedule you outside these times.

---

## Dashboard

Your dashboard shows:

- **Today's Lessons**: Upcoming lessons with quick actions
- **This Week**: Weekly schedule overview
- **Students**: Your current students
- **Attendance**: Quick marking for recent lessons
- **Earnings**: Current month earnings summary

---

## Lesson Schedule

### Viewing Your Schedule

1. Navigate to **My Calendar**
2. Switch views:
   - **Day**: Detailed hourly view
   - **Week**: 7-day overview
   - **Month**: Monthly planning

### Lesson Details

Click on any lesson to view:

- Subject and level
- Student name(s) and contact
- Room location
- Lesson notes
- Student progress notes

### Requesting Time Off

If you need to cancel lessons:

1. Navigate to **Calendar**
2. Click on lesson(s) to cancel
3. Click **Request Cancellation**
4. Provide reason
5. Admin will be notified

**Note**: Admin must approve all cancellations. Students will be notified and rescheduled.

---

## Attendance Management

### Marking Attendance

#### During/After Lesson

1. Go to **Dashboard** or **My Lessons**
2. Click on completed lesson
3. For each student, mark:

   - ✅ Present
   - ❌ Absent
   - ⏰ Late (specify minutes)
   - ℹ️ Excused

4. Add optional notes (e.g., "Arrived 10 min late")
5. Click **Save Attendance**

#### Quick Mark (Multiple Students)

For group lessons:

1. Click on lesson
2. Click **Quick Mark**
3. Options:
   - Mark all present
   - Mark all absent
   - Individual marking
4. Click **Save**

### Adding Lesson Notes

After marking attendance, add notes about:

- Topics covered
- Student understanding level
- Homework assigned
- Areas needing improvement
- Positive achievements

**These notes are visible to students and parents.**

---

## Student Management

### My Students

View all your current students:

1. Navigate to **Students**
2. See list with:
   - Student name
   - Class level
   - Subjects you teach them
   - Attendance rate
   - Last lesson date

### Student Progress

Track individual student progress:

1. Click on student name
2. View tabs:
   - **Overview**: Summary stats
   - **Attendance**: Full history
   - **Notes**: Your lesson notes
   - **Contact**: Parent information

### Communication

#### Messaging Students/Parents

1. Open student profile
2. Click **Send Message**
3. Choose recipient:
   - Student
   - Parent
   - Both
4. Write message
5. Click **Send**

**Note**: All messages are logged and visible to admin.

#### Scheduling Parent Meetings

1. Open student profile
2. Click **Schedule Meeting**
3. Propose time slots (3 options)
4. Parent selects preferred time
5. Meeting confirmed

---

## Earnings & Payments

### Viewing Earnings

1. Navigate to **Earnings**
2. View breakdown by:
   - Current month
   - Previous months
   - Per student
   - Per subject

### Monthly Summary

Around 25th of each month:

- View upcoming month's scheduled lessons
- See projected earnings
- Download summary PDF

**Note**: Actual payment schedule is determined by your contract with the school.

---

## Tips for Success

### Best Practices

1. **Mark attendance promptly** (within 24h of lesson)
2. **Add detailed notes** after each lesson
3. **Respond to messages** within 24 hours
4. **Keep profile updated** with current photo and bio
5. **Report issues immediately** to admin

### Common Issues

**Student didn't show up**:

- Mark as absent
- Add note explaining
- Admin may reach out to parent

**Technical problem during lesson**:

- Note the issue in lesson notes
- If lesson was disrupted significantly, contact admin for potential makeup

**Scheduling conflict**:

- Contact admin immediately
- Do not reschedule on your own
- Provide alternative times

---

## Mobile Access

Access Na Piątkę on mobile:

1. Open https://napiatke.pl in mobile browser
2. Log in normally
3. For quick access:
   - iOS: Add to Home Screen
   - Android: Add to Home Screen

**Mobile Features**:

- View schedule
- Mark attendance
- Send messages
- View student info

---

## Support

Need help?

- Email: support@napiatke.pl
- Admin contact: admin@napiatke.pl
- User guide: https://docs.napiatke.pl/tutor
```

#### Student User Guide:

```markdown
<!-- docs/user-guides/student/README.md -->

# Student User Guide - Na Piątkę

## Welcome!

This guide will help you use the Na Piątkę system to view your schedule, request lesson cancellations, and track your progress.

## Getting Started

### First Login

Your school admin created your account. Check your email for login credentials.

1. Go to https://napiatke.pl/auth/login
2. Enter your email and temporary password
3. Create a new password (must be strong!)
4. Complete your profile

### Profile Setup

1. Go to **My Profile**
2. Add profile photo (optional)
3. **Important**: Complete parent contact information
   - Parent name
   - Parent email (for invoices)
   - Parent phone number
4. Emergency contact (required)

---

## Dashboard

Your dashboard shows:

- **Today's Lessons**: What's happening today
- **Upcoming This Week**: Your schedule
- **Attendance**: Your attendance rate
- **Progress**: Subjects and tutors
- **Makeup Lessons**: Lessons you need to reschedule

---

## My Calendar

### Viewing Your Schedule

1. Click **Calendar** in menu
2. See all your scheduled lessons
3. Switch views:
   - Week (recommended)
   - Month
   - List

### Lesson Details

Click on any lesson to see:

- Subject and topic
- Tutor name
- Room location (or "Online")
- Time and duration
- Other students (if group lesson)

---

## Requesting Cancellations

Sometimes you need to cancel a lesson (illness, school event, etc.).

### How to Request

1. Click on upcoming lesson
2. Click **Request Cancellation**
3. Select reason:
   - Illness
   - School event
   - Family emergency
   - Other (explain)
4. Add details
5. Click **Submit Request**

**Important Rules**:

- ⏰ Must request at least 24 hours before lesson
- 📝 Admin must approve your request
- ⚠️ Limited cancellations per month (usually 2)

### What Happens Next

1. Admin reviews your request
2. You receive email notification:
   - ✅ Approved: Lesson cancelled, added to makeup queue
   - ❌ Rejected: Lesson stays scheduled, see reason
3. If approved, you have 30 days to reschedule

### Checking Request Status

1. Go to **My Cancellations**
2. See all requests:
   - Pending (waiting for admin)
   - Approved (lesson cancelled)
   - Rejected (still scheduled)

---

## Makeup Lessons

When a lesson is cancelled (by you or tutor), it goes to your makeup queue.

### Viewing Makeup Lessons

1. Go to **Makeup Lessons**
2. See all lessons you need to reschedule
3. Each shows:
   - Subject
   - Original tutor
   - Days remaining (30-day limit)
   - Status

### Rescheduling

1. Click on makeup lesson
2. Click **Reschedule**
3. View tutor's available slots
4. Click on time slot
5. Confirm

**Auto-matched**:

- Same tutor
- Same subject/level
- Available room

### Expiration

⚠️ Makeup lessons expire after 30 days

- Warning at 7 days remaining
- Can't reschedule after expiration
- Ask admin for extension if needed

---

## Attendance

### Viewing Your Attendance

1. Go to **My Attendance**
2. See full history:
   - ✅ Present
   - ❌ Absent
   - ⏰ Late
   - ℹ️ Excused
3. Filter by:
   - Subject
   - Tutor
   - Date range

### Attendance Rate

Your overall attendance percentage is shown on dashboard.

**Good attendance** (>90%):

- Shows commitment
- Better learning outcomes
- Priority for popular tutors

**Low attendance** (<80%):

- Admin may contact parents
- May affect future scheduling

---

## Progress & Notes

### Tutor Notes

After each lesson, your tutor adds notes about:

- What you learned
- How you're doing
- Areas to improve
- Homework assigned

**To view**:

1. Go to **My Progress**
2. Click on subject
3. See all lesson notes

### Subjects Overview

See all subjects you're taking:

- Tutor name
- Lessons completed
- Attendance rate
- Recent notes

---

## Messages

### Reading Messages

1. Click bell icon 🔔 (top right)
2. See notifications:
   - New lesson scheduled
   - Lesson cancelled
   - Message from tutor
   - Invoice reminder

### Sending Messages

1. Go to **Messages**
2. Click **New Message**
3. Select recipient (tutor or admin)
4. Write message
5. Click **Send**

**Response Time**: Expect response within 24-48 hours

---

## Parent Access

Your parents can access your account to:

- View schedule
- See attendance
- Read tutor notes
- Pay invoices

**Sharing Access**:

1. Go to **Settings** → **Parent Access**
2. Click **Enable Parent Access**
3. Parent can log in with your email
4. (Or use separate parent login if set up by admin)

---

## Mobile App

Use Na Piątkę on your phone:

1. Open browser and go to https://napiatke.pl
2. Log in normally
3. **Add to Home Screen**:
   - iPhone: Tap share icon → "Add to Home Screen"
   - Android: Tap menu → "Add to Home Screen"

Now you have a quick-access icon like an app!

---

## Tips for Students

### 📚 Study Tips

1. Check calendar every Sunday for the week ahead
2. Review tutor notes after each lesson
3. Do homework before next session
4. Ask questions in messages if confused

### ⏰ Attendance Tips

1. Set reminders 30 min before lessons
2. If you'll be late, message tutor
3. If you must cancel, do it early (24h+)
4. Reschedule makeup lessons quickly

### 📊 Track Progress

1. Check attendance rate monthly
2. Read tutor notes to identify patterns
3. Focus on areas tutors highlight
4. Celebrate improvements!

---

## Troubleshooting

### Can't Log In

1. Check email spelling
2. Try "Forgot Password"
3. Check spam folder for reset email
4. Contact admin if still stuck

### Don't See a Lesson

1. Check calendar view (might be outside date range)
2. Ask tutor if lesson was scheduled
3. Contact admin to verify

### Can't Request Cancellation

Possible reasons:

- Less than 24h before lesson
- Already used monthly limit
- Lesson already started
- Contact admin for emergency situations

---

## Need Help?

- **Email**: support@napiatke.pl
- **Admin**: admin@napiatke.pl
- **This Guide**: https://docs.napiatke.pl/student
- **Video Tutorials**: https://docs.napiatke.pl/videos

Happy learning! 📖✨
```

**Validation**:

- All three user guides complete
- Screenshots included
- Step-by-step instructions clear
- Common issues addressed

---

### Task 150: Deployment & Operations Guide

**Files**: `docs/deployment/`, `docs/operations/`
**Reference**: DevelopmentRoadmap.md task 150

#### Deployment Guide:

````markdown
<!-- docs/deployment/README.md -->

# Deployment Guide - Na Piątkę

## Overview

This guide covers deploying the Na Piątkę tutoring management system to production on Vercel with PostgreSQL.

**Target Environment**: Vercel (Next.js) + Neon/Supabase PostgreSQL
**Prerequisites**: GitHub account, Vercel account, domain name

---

## Pre-Deployment Checklist

### Code Readiness

- [ ] All tests passing (`pnpm test`)
- [ ] Build succeeds (`pnpm build`)
- [ ] No TypeScript errors (`pnpm type-check`)
- [ ] ESLint passing (`pnpm lint`)
- [ ] Code coverage >80%

### Dependencies

- [ ] All package versions locked (package.json)
- [ ] No security vulnerabilities (`pnpm audit`)
- [ ] Production dependencies only in `dependencies`
- [ ] Dev dependencies in `devDependencies`

### Configuration

- [ ] Environment variables documented
- [ ] .env.example file up to date
- [ ] Secrets not in repository
- [ ] Database schema finalized

---

## Environment Setup

### 1. PostgreSQL Database (Neon)

Create production database:

1. Go to https://neon.tech
2. Create new project: "napiatke-production"
3. Region: Choose closest to users (Europe for Poland)
4. Copy connection strings:
   - `DATABASE_URL` (pooled connection)
   - `DIRECT_URL` (direct connection for migrations)

**Example**:

```env
DATABASE_URL="postgresql://user:password@ep-xxx.eu-central-1.aws.neon.tech/napiatke?sslmode=require&pgbouncer=true"
DIRECT_URL="postgresql://user:password@ep-xxx.eu-central-1.aws.neon.tech/napiatke?sslmode=require"
```
````

### 2. Email Service (Resend)

1. Go to https://resend.com
2. Create API key
3. Verify domain for sending:
   - Add DNS records (TXT, MX)
   - Wait for verification

```env
RESEND_API_KEY="re_xxxxxxxxxxxxx"
RESEND_FROM_EMAIL="noreply@napiatke.pl"
```

### 3. Authentication Secrets

Generate secure secrets:

```bash
# AUTH_SECRET (32+ characters)
openssl rand -base64 32

# Store securely
```

```env
AUTH_SECRET="your-generated-secret-here"
AUTH_URL="https://napiatke.pl"
```

### 4. Error Tracking (Sentry)

1. Go to https://sentry.io
2. Create new project: "napiatke"
3. Copy DSN

```env
SENTRY_DSN="https://xxx@xxx.ingest.sentry.io/xxx"
```

---

## Database Migration

### Run Migrations on Production DB

```bash
# Set production DATABASE_URL
export DATABASE_URL="postgresql://..."
export DIRECT_URL="postgresql://..."

# Generate Prisma client
pnpm prisma generate

# Run migrations
pnpm prisma migrate deploy

# Verify schema
pnpm prisma db pull
```

### Seed Initial Data

```bash
# Run seed script
pnpm prisma db seed
```

**Seeds**:

- Admin user (change password immediately!)
- Polish subjects and levels
- Default room (online)

**Important**: Change admin password after first login!

---

## Vercel Deployment

### 1. Connect GitHub Repository

1. Go to https://vercel.com
2. Click "New Project"
3. Import Git Repository
4. Select your GitHub repo: `yourusername/napiatke`
5. Framework: Next.js (auto-detected)

### 2. Configure Build Settings

**Framework Preset**: Next.js
**Build Command**: `pnpm build`
**Output Directory**: `.next` (default)
**Install Command**: `pnpm install`

**Root Directory**: `./` (leave default)

### 3. Environment Variables

Add all environment variables in Vercel dashboard:

```env
# Database
DATABASE_URL=postgresql://...
DIRECT_URL=postgresql://...

# Authentication
AUTH_SECRET=your-secret-here
AUTH_URL=https://your-domain.vercel.app
NEXTAUTH_URL=https://your-domain.vercel.app

# Email
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=noreply@napiatke.pl

# Error Tracking
SENTRY_DSN=https://...

# Optional
NEXT_PUBLIC_APP_URL=https://napiatke.pl
NODE_ENV=production
```

**Important**: Use "Production" environment for all

### 4. Deploy

1. Click **Deploy**
2. Wait for build (usually 2-3 minutes)
3. Check deployment logs for errors
4. Visit deployment URL: `https://napiatke-xxx.vercel.app`

---

## Domain Configuration

### 1. Add Custom Domain

In Vercel project settings:

1. Go to **Settings** → **Domains**
2. Add domain: `napiatke.pl`
3. Add subdomain: `www.napiatke.pl`

### 2. DNS Configuration

Update your domain DNS (e.g., at your registrar):

**For apex domain (napiatke.pl)**:

```
Type: A
Name: @
Value: 76.76.21.21 (Vercel's IP)
```

**For www subdomain**:

```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

**Wait for DNS propagation** (up to 48h, usually minutes)

### 3. SSL Certificate

Vercel automatically provisions SSL via Let's Encrypt.

**Verify**:

- Visit https://napiatke.pl
- Check for padlock icon
- Certificate should be valid

---

## Post-Deployment Verification

### 1. Smoke Tests

Run critical path tests:

```bash
# From local machine
pnpm test:e2e --config playwright.config.prod.ts
```

**Manual Tests**:

- [ ] Homepage loads
- [ ] Login works (test user)
- [ ] Admin dashboard loads
- [ ] Calendar displays
- [ ] Create test event
- [ ] Send test message
- [ ] Generate test invoice

### 2. Performance Check

1. Run Lighthouse audit:
   - Open Chrome DevTools
   - Go to Lighthouse tab
   - Run audit on production URL

**Targets**:

- Performance: >90
- Accessibility: >95
- Best Practices: >90
- SEO: >90

2. Check Core Web Vitals:
   - LCP <2.5s
   - FID <100ms
   - CLS <0.1

### 3. Error Monitoring

1. Go to Sentry dashboard
2. Verify events are being received
3. Check for any immediate errors

---

## Rollback Procedure

If deployment has critical issues:

### Immediate Rollback (Vercel)

1. Go to Vercel project → **Deployments**
2. Find last working deployment
3. Click **...** menu → **Promote to Production**
4. Confirm rollback

**Downtime**: <1 minute

### Database Rollback

⚠️ **Only if database schema changed**

1. SSH into database or use GUI
2. Run rollback migration:

```bash
# If using Prisma migrate
pnpm prisma migrate rollback

# Or manually
psql $DATABASE_URL < backups/backup-before-deployment.sql
```

### Notify Users

If rollback needed:

1. Post status on status page
2. Email active users
3. Investigate root cause before next deployment

---

## Monitoring Setup

### 1. Vercel Analytics

Automatically enabled. View in Vercel dashboard:

- Page views
- Unique visitors
- Top pages
- Real-time visitors

### 2. Uptime Monitoring

Use UptimeRobot or similar:

1. Sign up at https://uptimerobot.com
2. Add monitor:
   - Type: HTTPS
   - URL: https://napiatke.pl/api/health
   - Interval: 5 minutes
3. Set alert contacts (email, SMS)

### 3. Log Aggregation

Vercel captures logs automatically. View in:

- Vercel dashboard → **Logs**
- Filter by type (errors, warnings, info)

**For advanced logging**: Consider Datadog or LogRocket

---

## Security Hardening

### 1. Security Headers

Add to `next.config.js`:

```javascript
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};
```

### 2. Rate Limiting

Implement with Upstash Redis:

```bash
pnpm add @upstash/redis @upstash/ratelimit
```

See `lib/rateLimit.ts` for implementation

### 3. IP Whitelist (Admin Panel)

Configure in middleware.ts for `/admin/*` routes

---

## Maintenance Windows

Schedule for low-traffic times:

**Recommended**: Sunday 2-4 AM CET

**Process**:

1. Announce 48h in advance (email, dashboard banner)
2. Enable maintenance mode (see `app/maintenance/page.tsx`)
3. Perform updates
4. Run smoke tests
5. Disable maintenance mode
6. Monitor for 1 hour

---

## Backup Strategy

### Database Backups

**Neon** provides automatic daily backups (retained 7 days).

**Manual Backup** (before major changes):

```bash
pg_dump $DATABASE_URL > backups/backup-$(date +%Y%m%d).sql
```

**Store backups** in AWS S3 or similar

### Code Backups

- GitHub is source of truth
- Vercel stores deployment snapshots
- Tag releases: `git tag v1.0.0`

---

## Troubleshooting

### Build Failures

**Common causes**:

- TypeScript errors
- Missing environment variables
- Dependency conflicts

**Fix**:

1. Check Vercel build logs
2. Run `pnpm build` locally
3. Fix errors
4. Redeploy

### Database Connection Errors

**Check**:

- DATABASE_URL format correct
- Database is accessible (not sleeping on free tier)
- Connection pool not exhausted

**Fix**:

- Use connection pooling (PgBouncer)
- Increase pool size in DATABASE_URL

### 500 Errors

1. Check Sentry for stack traces
2. Review Vercel function logs
3. Verify environment variables

---

## Scaling Considerations

### When to Scale

Monitor these metrics:

- Response time >1s (p95)
- Error rate >1%
- Database CPU >70%
- Concurrent users >1000

### Vercel Scaling

Vercel scales automatically (serverless).

**Limits**:

- Pro plan: 100GB bandwidth/month
- Enterprise: Custom limits

### Database Scaling

**Neon**:

- Upgrade to paid tier for more compute
- Enable autoscaling
- Set min/max compute units

**Alternative**: Migrate to dedicated PostgreSQL (AWS RDS, DO Managed DB)

---

## Support Contacts

- **Vercel Support**: support@vercel.com
- **Neon Support**: support@neon.tech
- **Resend Support**: support@resend.com
- **Sentry Support**: support@sentry.io

---

**Deployment Complete!** 🚀

Next: Monitor for 48 hours, address any issues, then proceed with user onboarding.

````

**Validation**:

- Deployment steps clear and tested
- All environment variables documented
- Rollback procedure defined
- Monitoring setup complete

---

### Task 151: Database Schema Documentation

**Files**: `docs/database/schema.md`, `docs/database/relationships.md`
**Reference**: DevelopmentRoadmap.md task 151

This task is completed via existing `/home/adam-szczotka/Dokumenty/GitHub/NaPiatkeKom/docs/DatabaseArchitecture.md`

**Validation**:

- Schema fully documented
- All tables described
- Relationships visualized
- Indexes listed

---

### Task 152: Disaster Recovery & Rollback Procedures

**Files**: `docs/operations/disaster-recovery.md`, `docs/operations/rollback.md`
**Reference**: DevelopmentRoadmap.md task 152

#### Disaster Recovery Plan:

```markdown
<!-- docs/operations/disaster-recovery.md -->
# Disaster Recovery Plan - Na Piątkę

## Overview

This document outlines procedures for recovering from catastrophic failures.

**RTO (Recovery Time Objective)**: 4 hours
**RPO (Recovery Point Objective)**: 24 hours (daily backups)

---

## Disaster Scenarios

### 1. Complete Database Loss

**Impact**: All data lost, system unusable
**Likelihood**: Very Low
**Severity**: Critical

#### Recovery Steps

1. **Provision new database**:
   ```bash
   # Create new Neon database
   # Or restore from backup
````

2. **Restore from latest backup**:

   ```bash
   # Download latest backup from S3
   aws s3 cp s3://napiatke-backups/latest.sql.gz ./

   # Decompress
   gunzip latest.sql.gz

   # Restore
   psql $NEW_DATABASE_URL < latest.sql
   ```

3. **Update connection strings**:

   - Update DATABASE_URL in Vercel
   - Redeploy application

4. **Verify data integrity**:

   ```bash
   # Run integrity checks
   pnpm prisma db pull
   pnpm prisma validate
   ```

5. **Test critical paths**:
   - Login
   - View calendar
   - Create event
   - Generate invoice

**Estimated Recovery Time**: 2-3 hours

---

### 2. Vercel Platform Outage

**Impact**: Application unavailable
**Likelihood**: Low
**Severity**: High

#### Immediate Actions

1. **Check Vercel status**: https://vercel-status.com
2. **Communicate with users**: Email, status page
3. **If prolonged** (>2 hours): Consider alternate hosting

#### Alternate Deployment (Emergency)

```bash
# Deploy to Railway.app or similar
railway login
railway init
railway up
```

**Estimated Recovery Time**: 1-2 hours

---

### 3. Data Corruption

**Impact**: Incorrect data in database
**Likelihood**: Low
**Severity**: Medium-High

#### Detection

- User reports inconsistencies
- Automated data validation fails
- Admin notices irregularities

#### Recovery Steps

1. **Identify scope**:

   ```sql
   -- Example: Check for orphaned records
   SELECT * FROM event_students
   WHERE event_id NOT IN (SELECT id FROM events);
   ```

2. **Stop writes** (if necessary):

   - Enable maintenance mode
   - Redirect traffic to read-only

3. **Restore affected data**:

   ```sql
   -- Option 1: Restore specific table
   psql $DATABASE_URL < backups/events_table_backup.sql

   -- Option 2: Point-in-time recovery (Neon feature)
   -- Use Neon dashboard to restore to specific timestamp
   ```

4. **Verify fix**:

   - Run data integrity scripts
   - Test affected features

5. **Re-enable writes**

**Estimated Recovery Time**: 1-4 hours

---

### 4. Security Breach

**Impact**: Unauthorized access to system
**Likelihood**: Low
**Severity**: Critical

#### Immediate Actions

1. **Contain**:

   - Disable compromised user accounts
   - Rotate all secrets (AUTH_SECRET, API keys)
   - Enable maintenance mode if needed

2. **Investigate**:

   - Review audit logs
   - Check for data exfiltration
   - Identify attack vector

3. **Notify**:

   - GDPR requires notification within 72 hours
   - Email affected users
   - Report to authorities if required

4. **Remediate**:

   - Patch vulnerability
   - Reset all user passwords
   - Enable 2FA (if not already)

5. **Monitor**:
   - Increased logging
   - Anomaly detection

**Estimated Recovery Time**: Variable (1-7 days)

---

### 5. Accidental Data Deletion

**Impact**: Users or data mistakenly deleted
**Likelihood**: Medium
**Severity**: Medium

#### Recovery Steps

1. **Soft delete check**:

   ```sql
   -- Most tables use soft deletes
   SELECT * FROM users WHERE deleted_at IS NOT NULL;
   ```

2. **Restore if truly deleted**:

   ```sql
   -- From backup
   psql $DATABASE_URL < backups/backup-before-deletion.sql
   ```

3. **Prevent future incidents**:
   - Review permissions
   - Add confirmation dialogs
   - Improve audit logging

**Estimated Recovery Time**: 30 minutes - 2 hours

---

## Backup Strategy

### Automated Backups

**Daily Backups** (Neon built-in):

- Retention: 7 days
- Time: 2 AM CET
- Automatic

**Weekly Full Backups** (Manual script):

```bash
#!/bin/bash
# scripts/backup-weekly.sh

DATE=$(date +%Y%m%d)
BACKUP_FILE="napiatke-backup-$DATE.sql"

# Dump database
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE.gz s3://napiatke-backups/weekly/

# Cleanup local
rm $BACKUP_FILE.gz

# Retain last 4 weeks
# ... cleanup script
```

**Run via cron**:

```cron
0 2 * * 0 /path/to/scripts/backup-weekly.sh
```

### Backup Verification

**Monthly restore test**:

1. Download latest backup
2. Restore to test database
3. Run smoke tests
4. Document results

**Checklist**:

- [ ] Backup file intact (not corrupted)
- [ ] Restore completes without errors
- [ ] Data integrity checks pass
- [ ] Critical queries work

---

## Data Retention Policy

| Data Type       | Retention Period | Deletion Method |
| --------------- | ---------------- | --------------- |
| User accounts   | 7 years          | Soft delete     |
| Lesson records  | 7 years          | Soft delete     |
| Invoices        | 10 years (legal) | Archive         |
| Attendance logs | 7 years          | Soft delete     |
| Messages        | 2 years          | Hard delete     |
| Audit logs      | 3 years          | Archive         |
| Backups         | 4 weeks (weekly) | Auto-delete     |

**GDPR Right to Erasure**:

- User can request data deletion
- Admin approves (verify legal requirements)
- Data anonymized (not deleted entirely due to audit requirements)

---

## Emergency Contacts

| Role             | Name       | Contact              |
| ---------------- | ---------- | -------------------- |
| System Admin     | [Name]     | admin@napiatke.pl    |
| Database Admin   | [Name]     | dba@napiatke.pl      |
| Security Officer | [Name]     | security@napiatke.pl |
| Vercel Support   | -          | support@vercel.com   |
| Neon Support     | -          | support@neon.tech    |
| Legal Counsel    | [Law Firm] | legal@napiatke.pl    |

---

## Communication Templates

### User Notification (Data Breach)

```
Subject: Important Security Notice - Na Piątkę

Dear [User],

We are writing to inform you of a security incident that may have affected your account.

WHAT HAPPENED:
On [date], we detected [brief description]. We immediately took steps to secure the system.

WHAT INFORMATION WAS INVOLVED:
[Specify data types]

WHAT WE ARE DOING:
- System secured
- All passwords reset
- Monitoring increased

WHAT YOU SHOULD DO:
- Change your password immediately
- Enable two-factor authentication
- Monitor for suspicious activity

We sincerely apologize for this incident. Your security is our priority.

Questions? Contact support@napiatke.pl

Na Piątkę Team
```

### Status Page Update (Outage)

```
[DATE] [TIME] - INVESTIGATING
We are aware of an issue affecting access to Na Piątkę. Our team is investigating.

[DATE] [TIME] - IDENTIFIED
The issue has been identified as [cause]. We are working on a fix.

[DATE] [TIME] - MONITORING
A fix has been deployed. We are monitoring the system for stability.

[DATE] [TIME] - RESOLVED
The issue is resolved. All systems operational. We apologize for the disruption.
```

---

## Testing & Drills

### Quarterly DR Drill

**Purpose**: Ensure team can execute recovery procedures

**Schedule**: Every 3 months

**Scenario**: Simulate database corruption

**Steps**:

1. Announce drill (non-production)
2. Execute recovery procedure
3. Time the recovery
4. Document lessons learned
5. Update procedures if needed

**Success Criteria**:

- Recovery time <4 hours (RTO)
- Data integrity maintained
- Team confident in procedures

---

## Continuous Improvement

After each incident:

1. **Post-Mortem Meeting** (within 48 hours)

   - What happened?
   - Timeline of events
   - What went well?
   - What could be improved?

2. **Document Lessons Learned**

   - Update procedures
   - Add to knowledge base

3. **Implement Preventive Measures**

   - Fix root cause
   - Add monitoring/alerts

4. **Share Learnings**
   - Team review
   - Update documentation

---

**Last Updated**: [Date]
**Next Review**: [Date + 6 months]
**Version**: 1.0

```

**Validation**:

- All disaster scenarios covered
- Recovery procedures tested
- Backup strategy implemented
- Communication templates ready

---

## ✅ SPRINT COMPLETION CHECKLIST

### API Documentation

- [ ] All tRPC routers documented
- [ ] Examples provided for each procedure
- [ ] Authentication flow documented
- [ ] Error codes defined

### User Manuals

- [ ] Admin guide complete with screenshots
- [ ] Tutor guide complete and user-friendly
- [ ] Student guide simple and clear
- [ ] Parent access documented

### Deployment Documentation

- [ ] Step-by-step deployment guide
- [ ] Environment setup documented
- [ ] Rollback procedure defined
- [ ] Monitoring setup explained

### Database Documentation

- [ ] Schema fully documented (existing file)
- [ ] Relationships visualized
- [ ] Indexes listed

### Disaster Recovery

- [ ] Recovery procedures for all scenarios
- [ ] Backup strategy implemented
- [ ] Contact lists updated
- [ ] Communication templates ready

---

## 📊 SUCCESS METRICS

- **Completeness**: 100% of system documented
- **Clarity**: Non-technical users can follow guides
- **Accessibility**: All docs in `/docs` directory
- **Maintenance**: Quarterly review scheduled

---

**Sprint Completion**: All 5 tasks completed and validated ✅
**Next Phase**: Phase 13 - Production Deployment (Tasks 153-165)
**Documentation**: Production-ready and comprehensive
```
