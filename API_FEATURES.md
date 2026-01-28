# TerminFinder MVP - API Features Documentation

## 🎯 Overview

This document describes the newly implemented features that provide a professional, Doctolib-like experience.

---

## 📋 Table of Contents

1. [Doctor Search with Slot Counts](#doctor-search)
2. [Booking Cancellation](#cancellation)
3. [Doctor Calendar Management](#calendar-management)
4. [Enhanced Dashboards](#dashboards)
5. [Analytics](#analytics)

---

## 🔍 Doctor Search

### 1. Get Available Doctors with Free Slots Count

**Endpoint:** `GET /api/search/doctors/available`

**Purpose:** Display doctors with their specialty and number of free appointments (2-level display like Doctolib)

**Query Parameters:**
- `speciality` (optional): Filter by specialty
- `city` (optional): Filter by city
- `date_from` (optional): Start date (YYYY-MM-DD), default: today
- `date_to` (optional): End date (YYYY-MM-DD), default: +7 days
- `limit` (optional): Max results, default: 20

**Response Example:**
```json
{
  "doctors": [
    {
      "id": "uuid",
      "first_name": "Anna",
      "last_name": "Müller",
      "full_name": "Anna Müller",
      "speciality": "dermatologe",
      "speciality_display": "Dermatologe",
      "practice": {
        "id": "uuid",
        "name": "Praxis Dr. Müller",
        "city": "Berlin",
        "address": "Hauptstraße 123, 10115 Berlin"
      },
      "free_slots_count": 24,
      "has_available_slots": true
    }
  ],
  "total": 5,
  "filters": {
    "speciality": "dermatologe",
    "city": "Berlin",
    "date_from": "2026-01-28",
    "date_to": "2026-02-04"
  }
}
```

**Use Case:**
```
Level 1 (List View):
  🧑‍⚕️ Dr. Anna Müller
  Speciality: Dermatologe
  Free slots: 24
  [Show Available Times →]

User clicks → Level 2 loads slots
```

---

### 2. Get Doctor's Available Slots

**Endpoint:** `GET /api/search/doctors/{doctor_id}/slots`

**Purpose:** Show specific time slots for a doctor (Level 2 display)

**Query Parameters:**
- `date_from` (optional): Start date (YYYY-MM-DD)
- `date_to` (optional): End date (YYYY-MM-DD)

**Response Example:**
```json
{
  "doctor": {
    "id": "uuid",
    "first_name": "Anna",
    "last_name": "Müller",
    "speciality": "dermatologe",
    "speciality_display": "Dermatologe"
  },
  "slots_by_date": {
    "2026-01-28": [
      {
        "id": "slot-uuid",
        "start_time": "09:00",
        "end_time": "09:30",
        "datetime": "2026-01-28T09:00:00"
      },
      {
        "id": "slot-uuid",
        "start_time": "09:30",
        "end_time": "10:00",
        "datetime": "2026-01-28T09:30:00"
      }
    ],
    "2026-01-29": [...]
  },
  "total_slots": 24,
  "period": {
    "date_from": "2026-01-28",
    "date_to": "2026-02-04"
  }
}
```

---

## ❌ Booking Cancellation

### 1. Cancel Booking

**Endpoint:** `POST /api/bookings/{booking_id}/cancel`

**Authorization:** Required (JWT token)

**Access:**
- Patient: Can cancel own booking (before `cancellable_until` time)
- Doctor: Can cancel any booking on their calendar

**Request Body:**
```json
{
  "reason": "Patient request" // optional
}
```

**Response:**
```json
{
  "message": "Booking cancelled successfully",
  "booking": {
    "id": "uuid",
    "status": "cancelled",
    "cancelled_at": "2026-01-28T10:30:00",
    "cancelled_by": "patient"
  }
}
```

**Business Rules:**
- Patient cancellation: Only before `cancellable_until` deadline
- Doctor cancellation: Anytime
- Slot automatically becomes `available` again
- Status changes to `cancelled`

---

### 2. Get Booking Details

**Endpoint:** `GET /api/bookings/{booking_id}`

**Authorization:** Required

**Response:**
```json
{
  "booking": {
    "id": "uuid",
    "booking_code": "AB12CD34",
    "status": "confirmed",
    "cancellable": true,
    "cancellable_until": "2026-01-28T10:00:00",
    "timeslot": {
      "start_time": "2026-01-30T14:00:00",
      "end_time": "2026-01-30T14:30:00",
      "date": "2026-01-30",
      "time": "14:00"
    },
    "doctor": {
      "id": "uuid",
      "full_name": "Dr. Anna Müller",
      "speciality": "dermatologe",
      "speciality_display": "Dermatologe"
    },
    "practice": {
      "name": "Praxis Dr. Müller",
      "address": "Hauptstraße 123, 10115 Berlin",
      "phone": "+49301234567"
    }
  }
}
```

---

### 3. Get Booking by Code (Public)

**Endpoint:** `GET /api/bookings/by-code/{booking_code}`

**Authorization:** NOT required (for email links)

**Use Case:** Patient receives email with booking code, can view details without login

---

## 📅 Doctor Calendar Management

### 1. Close Day

**Endpoint:** `POST /api/doctors/calendar/close-day`

**Authorization:** Required (Doctor)

**Purpose:** Block all available slots for a specific day (vacation, emergency)

**Request Body:**
```json
{
  "date": "2026-02-15",
  "reason": "Vacation" // optional
}
```

**Response:**
```json
{
  "message": "Day closed successfully",
  "date": "2026-02-15",
  "blocked_slots": 16,
  "booked_slots": 2,
  "warning": "2 slots have existing bookings"
}
```

**Business Logic:**
- Only `available` slots are blocked
- `booked` slots remain unchanged (existing appointments)
- Returns warning if there are existing bookings

---

### 2. Open Day

**Endpoint:** `POST /api/doctors/calendar/open-day`

**Authorization:** Required (Doctor)

**Purpose:** Unblock all blocked slots for a specific day

**Request Body:**
```json
{
  "date": "2026-02-15"
}
```

**Response:**
```json
{
  "message": "Day opened successfully",
  "date": "2026-02-15",
  "unblocked_slots": 16
}
```

---

## 📊 Enhanced Dashboards

### 1. Doctor Dashboard

**Endpoint:** `GET /api/doctors/dashboard`

**Authorization:** Required (Doctor)

**Response:**
```json
{
  "doctor": {
    "id": "uuid",
    "name": "Dr. Anna Müller",
    "speciality": "dermatologe",
    "is_verified": true,
    "has_calendar": true
  },
  "today": {
    "appointments_count": 8,
    "next_appointment": {
      "id": "uuid",
      "patient_name": "Max Mustermann",
      "patient_phone": "+491234567890",
      "time": "14:30",
      "start_time": "2026-01-28T14:30:00",
      "status": "confirmed"
    },
    "appointments": [...]
  },
  "this_week": {
    "total_slots": 160,
    "booked_slots": 120,
    "available_slots": 35,
    "blocked_slots": 5,
    "fill_rate": 75.0
  },
  "calendar": {
    "exists": true,
    "working_hours": {...},
    "slot_duration": 30,
    "buffer_time": 5
  }
}
```

**Dashboard Sections:**

📅 **Today:**
- Total appointments today
- Next appointment (patient name, time)
- List of all today's appointments

📈 **This Week:**
- Total slots
- Booked slots
- Available slots
- Fill rate (%)

⚡ **Quick Actions** (Frontend):
- ➕ Add appointments
- ❌ Close day
- 📧 Send message

---

### 2. Patient Dashboard

**Endpoint:** `GET /api/patient/dashboard`

**Authorization:** Required (Patient)

**Response:**
```json
{
  "patient": {
    "id": "uuid",
    "name": "Max Mustermann",
    "phone": "+491234567890",
    "total_bookings": 5,
    "attended_appointments": 4
  },
  "next_appointment": {
    "id": "uuid",
    "booking_code": "AB12CD34",
    "date": "2026-01-30",
    "time": "14:00",
    "datetime": "2026-01-30T14:00:00",
    "doctor": {
      "id": "uuid",
      "name": "Dr. Anna Müller",
      "speciality": "dermatologe",
      "speciality_display": "Dermatologe"
    },
    "practice": {
      "name": "Praxis Dr. Müller",
      "address": "Hauptstraße 123, 10115 Berlin",
      "phone": "+49301234567",
      "city": "Berlin"
    },
    "cancellable": true,
    "cancellable_until": "2026-01-30T10:00:00"
  },
  "history": [
    {
      "id": "uuid",
      "date": "2026-01-15",
      "time": "10:00",
      "doctor_name": "Dr. Schmidt",
      "speciality": "Allgemeinmedizin",
      "status": "completed"
    }
  ],
  "recommended_doctors": [
    {
      "id": "uuid",
      "name": "Dr. Weber",
      "speciality": "dermatologe",
      "speciality_display": "Dermatologe",
      "free_slots_count": 18,
      "practice": {
        "name": "Praxis Weber",
        "city": "Berlin"
      }
    }
  ]
}
```

**Dashboard Sections:**

📅 **Next Appointment:**
- Doctor, date, time, location
- Cancel/Reschedule buttons

📜 **History:**
- Last 5 appointments
- Status (completed, cancelled)

👨‍⚕️ **Recommended Doctors:**
- Same specialty as last visit
- Doctors with available slots
- Location info

---

## 📈 Analytics

### Doctor Analytics

**Endpoint:** `GET /api/doctors/analytics`

**Authorization:** Required (Doctor)

**Query Parameters:**
- `period`: `week`, `month`, `year` (default: `week`)

**Response:**
```json
{
  "period": {
    "type": "week",
    "start_date": "2026-01-21",
    "end_date": "2026-01-28"
  },
  "slots": {
    "total": 160,
    "booked": 120,
    "available": 35,
    "blocked": 5,
    "fill_rate": 75.0
  },
  "appointments": {
    "total": 120,
    "confirmed": 100,
    "completed": 95,
    "cancelled": 15,
    "no_show": 5,
    "no_show_rate": 5.3,
    "cancellation_rate": 12.5
  },
  "bookings_by_day": {
    "monday": 24,
    "tuesday": 22,
    "wednesday": 20,
    "thursday": 23,
    "friday": 21,
    "saturday": 0,
    "sunday": 0
  }
}
```

**Key Metrics:**

💰 **Fill Rate:** (booked_slots / total_slots) × 100
- Target: > 70%

📊 **No-Show Rate:** (no_show / completed) × 100
- Target: < 10%

❌ **Cancellation Rate:** (cancelled / total) × 100
- Target: < 15%

**Business Value:**
- Identify busy days
- Optimize schedule
- Track attendance
- Spot patterns

---

## 🎯 Frontend Implementation Examples

### Example 1: Doctor Search (2-Level)

```javascript
// Level 1: Show doctors list
fetch('/api/search/doctors/available?speciality=dermatologe&city=Berlin')
  .then(res => res.json())
  .then(data => {
    data.doctors.forEach(doctor => {
      displayDoctor({
        name: doctor.full_name,
        specialty: doctor.speciality_display,
        freeSlotsCount: doctor.free_slots_count,
        onClick: () => showDoctorSlots(doctor.id)
      });
    });
  });

// Level 2: Show specific slots
function showDoctorSlots(doctorId) {
  fetch(`/api/search/doctors/${doctorId}/slots`)
    .then(res => res.json())
    .then(data => {
      Object.entries(data.slots_by_date).forEach(([date, slots]) => {
        displaySlotsForDate(date, slots);
      });
    });
}
```

---

### Example 2: Cancel Booking

```javascript
function cancelBooking(bookingId) {
  if (!confirm('Are you sure you want to cancel?')) return;
  
  fetch(`/api/bookings/${bookingId}/cancel`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      reason: 'Personal reasons'
    })
  })
  .then(res => res.json())
  .then(data => {
    showNotification('Booking cancelled successfully');
    refreshDashboard();
  });
}
```

---

### Example 3: Close Day

```javascript
function closeDay(date) {
  fetch('/api/doctors/calendar/close-day', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ date })
  })
  .then(res => res.json())
  .then(data => {
    if (data.warning) {
      alert(data.warning);
    }
    showNotification(`Blocked ${data.blocked_slots} slots`);
    refreshCalendar();
  });
}
```

---

## ✅ Implementation Checklist

### Backend ✅
- [x] Status system (confirmed, cancelled, completed, no_show)
- [x] Doctor search with slot counts
- [x] 2-level slot display
- [x] Booking cancellation with restrictions
- [x] Close/open day functionality
- [x] Enhanced doctor dashboard
- [x] Enhanced patient dashboard
- [x] Analytics endpoint

### Frontend (TODO)
- [ ] Implement 2-level doctor search UI
- [ ] Add cancel booking button to patient dashboard
- [ ] Add close-day button to doctor calendar
- [ ] Display analytics charts
- [ ] Show recommended doctors
- [ ] Add next appointment widget

### Email Integration (Future)
- [ ] Send .ics calendar file
- [ ] Cancellation confirmation email
- [ ] Reminder email (24h before)
- [ ] No-show tracking email

---

## 🚀 Business Impact

### For Patients
✅ **Cleaner UX:** 2-level display reduces cognitive load
✅ **Transparency:** See available slots count before clicking
✅ **Control:** Easy cancellation and rescheduling
✅ **Recommendations:** Find similar doctors easily

### For Doctors
✅ **Professional Analytics:** Fill rate, no-show rate, cancellation rate
✅ **Flexible Schedule:** Close/open days easily
✅ **Better Overview:** Today's appointments + weekly stats
✅ **Business Insights:** Busy days, attendance patterns

### For Practices
✅ **Competitive Feature:** Matches Doctolib's UX
✅ **Easy to Sell:** Clear value proposition
✅ **Scalable:** Efficient queries, works with many doctors

---

## 📞 Support

For questions or issues, contact: freedoctor@example.com

**Test Account:**
- Email: freedoctor@example.com
- Password: 123456
