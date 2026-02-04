# 🚀 TERMINFINDER REFACTORING ROADMAP

## 📊 CURRENT STATE ANALYSIS

### ✅ ALREADY IMPLEMENTED
1. **Practice (Tenant) Model EXISTS**
   - ✅ UUID primary key
   - ✅ VAT number (unique tenant ID)
   - ✅ Address, contacts, verification
   - ✅ Extended info (gallery, services, team, equipment)
   - ✅ doctor.practice_id FK (nullable)
   - ✅ Practice relationship with doctors

2. **Chatbot EXISTS** 
   - ✅ Non-medical scope in system prompt
   - ✅ Practice-specific instructions
   - ⚠️ BUT: uses OpenAI, stores history

3. **Multi-route structure**
   - ✅ Separate blueprints: auth, patient, doctor, practice, chat, admin
   - ✅ API endpoints exist
   - ⚠️ BUT: mixed Jinja + API logic

### ❌ MISSING / NEEDS WORK
1. **No async/background tasks** - все IO операции блокують запити
2. **Jinja mixed with API** - не готово до SPA
3. **Chatbot unsafe** - зберігає історію, немає жорстких обмежень
4. **Practice isolation weak** - query без practice_id filter
5. **No event system** - notifications синхронні

---

## 🎯 IMPLEMENTATION PHASES

### PHASE 1: ASYNC FOUNDATION (Week 1-2)
**Priority: HIGH | Risk: LOW | Impact: HIGH**

#### 1.1 Setup Background Workers
```bash
pip install rq redis
```

**Files to create:**
```
app/
├── workers/
│   ├── __init__.py
│   ├── notification_tasks.py
│   ├── calendar_tasks.py
│   └── chatbot_tasks.py
├── events/
│   ├── __init__.py
│   └── event_names.py
```

**Tasks to extract:**
- Email notifications (alert_service.py)
- Calendar sync (google_calendar_service, outlook_calendar_service)
- Chatbot message processing

**Implementation steps:**
1. ✅ Install RQ + Redis
2. ✅ Create worker files
3. ✅ Move email sending to tasks
4. ✅ Move calendar sync to tasks
5. ✅ Update routes to enqueue tasks
6. ✅ Add worker startup script

**Success criteria:**
- No blocking IO in Flask request handlers
- Tasks retryable on failure
- Worker process runs separately

---

### PHASE 2: PRACTICE (TENANT) ISOLATION (Week 2-3)
**Priority: HIGH | Risk: MEDIUM | Impact: HIGH**

#### 2.1 Enforce Practice Scope Everywhere

**Critical changes:**

1. **Doctor registration** - MUST set practice_id
   ```python
   # app/routes/auth.py - NEVER allow doctor without practice
   practice_id = db.Column(..., nullable=FALSE)  # Change from nullable=True
   ```

2. **Query filters** - Add practice_id EVERYWHERE
   ```python
   # BAD
   doctors = Doctor.query.all()
   
   # GOOD
   doctors = Doctor.query.filter_by(practice_id=current_practice_id).all()
   ```

3. **API middleware** - Extract practice_id from JWT
   ```python
   @jwt_required()
   def get_doctors():
       practice_id = get_current_practice_id()  # From JWT claims
       doctors = Doctor.query.filter_by(practice_id=practice_id).all()
   ```

**Files to audit:**
- ✅ app/routes/doctor.py
- ✅ app/routes/practice.py
- ✅ app/routes/patient.py (search must filter by practice)
- ✅ app/routes/booking.py

**Success criteria:**
- NO query without practice filter
- JWT contains practice_id claim
- Practice separation tested

---

### PHASE 3: CHATBOT GDPR-SAFE (Week 3)
**Priority: CRITICAL | Risk: HIGH | Impact: LEGAL**

#### 3.1 Remove Personal Data from Chatbot

**Current issues:**
- ❌ Stores chat history → GDPR violation
- ❌ Uses OpenAI → data leaves EU
- ❌ No hard scope enforcement

**Required changes:**

1. **Remove history storage**
   ```python
   # NO persistent chat history
   # Use session-only anonymous UUID
   session_id = str(uuid.uuid4())  # Temporary, no DB
   ```

2. **Hard scope guard**
   ```python
   ALLOWED_INTENTS = [
       'platform_usage',
       'booking_help',
       'practice_info',
       'directions'
   ]
   
   FORBIDDEN_KEYWORDS = [
       'diagnose', 'behandlung', 'medikament', 
       'symptom', 'schmerz', 'therapie'
   ]
   ```

3. **Structured responses**
   ```python
   {
       "type": "info",
       "medical_advice": false,
       "scope": "platform_help",
       "content": "..."
   }
   ```

**Files to change:**
- ✅ app/routes/chat.py
- ✅ app/routes/help_chat.py
- ✅ Remove chat history models/tables

**Success criteria:**
- No personal data stored
- Hard keyword blocking
- Explicit non-medical disclaimer
- EU-only processing (or no LLM)

---

### PHASE 4: API-FIRST ARCHITECTURE (Week 4-5)
**Priority: MEDIUM | Risk: LOW | Impact: HIGH**

#### 4.1 Separate API from Jinja

**New structure:**
```
app/routes/
├── web/           # Jinja views ONLY (render HTML)
│   ├── patient_views.py
│   ├── doctor_views.py
│   └── admin_views.py
├── api/           # JSON-only endpoints
│   ├── patient_api.py
│   ├── doctor_api.py
│   └── booking_api.py
```

**Rules:**
- `web/*` - ONLY renders templates, NO business logic
- `api/*` - ONLY returns JSON, NO redirects, NO HTML

**Implementation:**
1. ✅ Create api/ and web/ directories
2. ✅ Move logic to api/
3. ✅ web/ calls api/ internally
4. ✅ API versioning (/api/v1/)

**Success criteria:**
- Clear separation
- Frontend can call API directly
- SPA-ready

---

### PHASE 5: PRACTICE DETAIL PAGES (Week 5)
**Priority: MEDIUM | Risk: LOW | Impact: UX**

#### 5.1 Practice as First-Class Citizen

**User flow:**
```
Search results → Doctor card → Click Practice name → Practice page
```

**Practice page shows:**
- ✅ Address, contacts
- ✅ All doctors in practice
- ✅ Gallery, services
- ✅ Reviews
- ✅ Directions (map)

**Files to create:**
- ✅ app/routes/web/practice_views.py
- ✅ app/templates/patient/practice_detail.html

**Success criteria:**
- Practice name is clickable
- Practice page loads
- Shows all practice doctors

---

## 📋 PRIORITY ORDER

### ✅ DO FIRST (CRITICAL PATH)
1. **Async workers** - prevents future scaling issues
2. **Practice isolation** - legal/security requirement
3. **Chatbot GDPR-safe** - legal liability

### ⏳ DO SECOND (IMPORTANT)
4. **API-first** - enables future SPA
5. **Practice pages** - UX improvement

---

## 🚧 IMPLEMENTATION CHECKLIST

### Week 1-2: Foundation
- [ ] Install RQ + Redis
- [ ] Create workers structure
- [ ] Move email to tasks
- [ ] Move calendar sync to tasks
- [ ] Test worker deployment

### Week 2-3: Tenant Safety
- [ ] Audit all Doctor queries
- [ ] Add practice_id filters everywhere
- [ ] Update JWT to include practice_id
- [ ] Make practice_id NOT NULL
- [ ] Test multi-practice separation

### Week 3: Chatbot GDPR
- [ ] Remove chat history storage
- [ ] Add hard keyword blocking
- [ ] Remove OpenAI (or EU-only)
- [ ] Add structured disclaimers
- [ ] Legal review

### Week 4-5: API Modernization
- [ ] Create api/ and web/ directories
- [ ] Move business logic to api/
- [ ] Version API (/api/v1/)
- [ ] Document API endpoints
- [ ] Test SPA readiness

### Week 5: Practice UX
- [ ] Create practice detail page
- [ ] Make practice name clickable
- [ ] Add practice search filter
- [ ] Test practice hierarchy

---

## 🔧 TECHNICAL DECISIONS

### Redis vs Celery?
**Choice: RQ + Redis** ✅
- Simpler setup
- Sufficient for current scale
- Easy to migrate to Celery later

### Keep OpenAI chatbot?
**Choice: Remove or EU-only** ⚠️
- Option 1: Remove LLM, use rule-based
- Option 2: Switch to EU-hosted model
- Option 3: Explicit consent + anonymization

### SPA now or later?
**Choice: Later** ✅
- API-first NOW (low risk)
- Keep Jinja for now
- SPA when ready (React/Vue)

---

## 🎯 SUCCESS METRICS

After refactoring:
- ✅ No blocking IO in request handlers
- ✅ Practice data isolation 100%
- ✅ Chatbot legally safe
- ✅ API-first ready for SPA
- ✅ Practice pages live
