# ⚖️ مشروع منصة الاستشارات القانونية

المستشار عصام الهلباوي أون لاين

وثيقة تنفيذية موجهة إلى برنامج إنشاء البرامج «عبقرينو»

---

أولاً: الهدف من المشروع

إنشاء برنامج ويب حقيقي كامل الوظائف لمنصة مكتب محاماة واستشارات قانونية، يعمل على الهاتف والكمبيوتر، ويجمع بين:

1. الصفحة التعريفية للمكتب.
2. حسابات الموكلين.
3. حسابات المحامين وموظفي المكتب.
4. إدارة الموكلين.
5. إدارة القضايا.
6. إدارة المستندات.
7. الشات.
8. الاستشارات المجانية.
9. الاستشارات المدفوعة.
10. المحادثات الصوتية والمرئية.
11. مشاركة الشاشة.
12. إرسال الملفات والصور والتسجيلات.
13. نظام الإشعارات.
14. نظام المواعيد.
15. نظام المدفوعات وإثبات التحويل.
16. المساعد القانوني الذكي.
17. التقارير.
18. لوحة إدارة النظام.
19. نظام الصلاحيات والأمان.
20. قاعدة بيانات حقيقية قابلة للتوسع.

---

ثانياً: قاعدة أساسية في التنفيذ

لا يتم إنشاء البرنامج على هيئة مجموعة شاشات شكلية فقط.

يجب أن تكون كل شاشة مرتبطة بوظائف حقيقية وقاعدة بيانات وواجهات API عند الحاجة.

أي زر في البرنامج يجب أن يكون له:

واجهة المستخدم
        ↓
JavaScript / Frontend Logic
        ↓
API / WebSocket
        ↓
Backend
        ↓
Database
        ↓
نتيجة حقيقية
        ↓
تحديث الواجهة

ولا يجوز إنشاء زر تجريبي من نوع:

alert("تم بنجاح");

إذا كانت الوظيفة يفترض أن تنفذ عملية حقيقية.

---

ثالثاً: التقنية المقترحة

يمكن استخدام:

Frontend:
HTML
CSS
JavaScript

Backend:
Node.js
Express.js

Realtime:
Socket.IO
WebRTC

Database:
SQLite في النسخة الأولى
مع تصميم يسمح بالانتقال إلى PostgreSQL

Authentication:
Session أو JWT

File Storage:
Local Storage في التطوير
مع إمكانية نقل الملفات إلى Cloud Storage لاحقاً

ويجب أن يكون التصميم Modular بحيث يمكن تغيير أي جزء دون إعادة بناء البرنامج بالكامل.

---

رابعاً: هيكل المشروع

يجب إنشاء المشروع بالشكل التالي:

legal-platform/
│
├── server/
│   ├── server.js
│   ├── config/
│   ├── routes/
│   ├── controllers/
│   ├── services/
│   ├── middleware/
│   ├── database/
│   ├── sockets/
│   └── utils/
│
├── public/
│   ├── index.html
│   ├── login.html
│   ├── client.html
│   ├── lawyer.html
│   ├── consultation.html
│   ├── chat.html
│   ├── cases.html
│   ├── documents.html
│   └── admin.html
│
├── public/assets/
│
├── uploads/
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── package.json
├── .env.example
└── README.md

---

خامساً: أنواع المستخدمين

1. زائر

يستطيع:

- مشاهدة الصفحة الرئيسية.
- مشاهدة خدمات المكتب.
- معرفة معلومات التواصل.
- طلب استشارة مجانية.
- الانتقال إلى تسجيل الدخول.

---

2. موكل

يستطيع:

- إنشاء حساب.
- تسجيل الدخول.
- تعديل بياناته.
- مشاهدة قضاياه.
- مشاهدة مستنداته.
- إرسال واستقبال الرسائل.
- طلب استشارة.
- حجز موعد.
- الدخول إلى غرفة الفيديو.
- رفع المستندات.
- متابعة المدفوعات.
- مشاهدة الإشعارات.

---

3. المحامي

يستطيع:

- إدارة الموكلين.
- إدارة القضايا.
- إدارة المستندات.
- إدارة الاستشارات.
- استقبال الرسائل.
- إنشاء غرف فيديو.
- التحكم في الميكروفون والكاميرا.
- مشاركة الشاشة.
- إرسال الملفات.
- مراجعة إثباتات الدفع.
- إعداد التقارير.
- استخدام المساعد الذكي.

---

4. موظف المكتب

صلاحياته تحدد من خلال نظام Permissions.

مثلاً:

CLIENT_VIEW
CLIENT_EDIT
CASE_VIEW
CASE_EDIT
DOCUMENT_UPLOAD
DOCUMENT_DELETE
PAYMENT_REVIEW
REPORT_VIEW

---

5. مدير النظام

يمتلك صلاحيات إدارة:

- المستخدمين.
- الأدوار.
- الصلاحيات.
- الخدمات.
- الأسعار.
- إعدادات النظام.
- السجلات.
- الإشعارات.

---

سادساً: الصفحة الرئيسية

الوظائف

يجب إنشاء:

⚖️ شعار المكتب

المستشار عصام الهلباوي أون لاين

مكتب المحاماة والاستشارات القانونية

الأزرار:

👤 دخول الموكل
⚖️ دخول المكتب
💬 استشارة مجانية
📹 حجز استشارة
ℹ️ عن المكتب
📞 تواصل معنا

---

سابعاً: نظام التسجيل والدخول

تسجيل الموكل

الحقول:

الاسم
رقم الهاتف
البريد الإلكتروني
كلمة المرور
تأكيد كلمة المرور

Backend:

app.post("/api/auth/register", async (req, res) => {
    const { name, phone, email, password } = req.body;

    if (!name || !phone || !password) {
        return res.status(400).json({
            success: false,
            message: "البيانات الأساسية مطلوبة"
        });
    }

    const existing = db.prepare(
        "SELECT id FROM users WHERE phone = ? OR email = ?"
    ).get(phone, email);

    if (existing) {
        return res.status(409).json({
            success: false,
            message: "الحساب موجود بالفعل"
        });
    }

    const passwordHash = await bcrypt.hash(password, 12);

    const result = db.prepare(`
        INSERT INTO users
        (name, phone, email, password_hash, role)
        VALUES (?, ?, ?, ?, 'client')
    `).run(name, phone, email, passwordHash);

    res.json({
        success: true,
        userId: result.lastInsertRowid
    });
});

---

ثامناً: تسجيل الدخول

API:

POST /api/auth/login

الكود:

app.post("/api/auth/login", async (req, res) => {
    const { phone, password } = req.body;

    const user = db.prepare(`
        SELECT *
        FROM users
        WHERE phone = ?
    `).get(phone);

    if (!user) {
        return res.status(401).json({
            success: false,
            message: "بيانات الدخول غير صحيحة"
        });
    }

    const valid = await bcrypt.compare(
        password,
        user.password_hash
    );

    if (!valid) {
        return res.status(401).json({
            success: false,
            message: "بيانات الدخول غير صحيحة"
        });
    }

    req.session.userId = user.id;
    req.session.role = user.role;

    res.json({
        success: true,
        user: {
            id: user.id,
            name: user.name,
            role: user.role
        }
    });
});

---

تاسعاً: لوحة الموكل

بعد الدخول:

مرحباً بك يا [اسم الموكل]

📁 قضاياي
💬 رسائلي
📄 مستنداتي
📹 استشاراتي
📅 مواعيدي
💳 مدفوعاتي
🔔 إشعاراتي
👤 بياناتي

كل زر ينتقل إلى وحدة حقيقية.

---

عاشراً: إدارة الموكلين

جدول:

clients

والواجهة:

بحث عن موكل
+
إضافة موكل
+
قائمة الموكلين

API:

GET    /api/clients
GET    /api/clients/:id
POST   /api/clients
PUT    /api/clients/:id
DELETE /api/clients/:id

مثال:

app.get("/api/clients", requireRole("lawyer", "admin"), (req, res) => {
    const clients = db.prepare(`
        SELECT id, name, phone, email, status, created_at
        FROM users
        WHERE role = 'client'
        ORDER BY created_at DESC
    `).all();

    res.json({
        success: true,
        clients
    });
});

---

الحادي عشر: نظام القضايا

كل قضية مرتبطة بموكل.

جدول:

cases

الحقول:

id
client_id
lawyer_id
case_number
title
case_type
court
status
description
created_at
updated_at

API:

GET    /api/cases
GET    /api/cases/:id
POST   /api/cases
PUT    /api/cases/:id
DELETE /api/cases/:id

---

الثاني عشر: مستندات القضية

جدول:

documents

الحقول:

id
case_id
uploaded_by
original_name
stored_name
mime_type
size
path
created_at

رفع الملف:

app.post(
    "/api/documents/upload",
    requireAuth,
    upload.single("file"),
    (req, res) => {

        if (!req.file) {
            return res.status(400).json({
                success: false,
                message: "لم يتم اختيار ملف"
            });
        }

        const result = db.prepare(`
            INSERT INTO documents
            (case_id, uploaded_by, original_name,
             stored_name, mime_type, size, path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        `).run(
            req.body.caseId,
            req.session.userId,
            req.file.originalname,
            req.file.filename,
            req.file.mimetype,
            req.file.size,
            req.file.path
        );

        res.json({
            success: true,
            documentId: result.lastInsertRowid
        });
    }
);

---

الثالث عشر: الشات

يجب تحويل الشات الحالي إلى WebSocket حقيقي.

Socket.IO:

io.on("connection", (socket) => {

    socket.on("join-chat", ({ conversationId }) => {
        socket.join(`chat:${conversationId}`);
    });

    socket.on("send-message", (message) => {

        io.to(`chat:${message.conversationId}`)
          .emit("new-message", message);
    });

});

لكن يجب أيضاً حفظ الرسالة في قاعدة البيانات:

const result = db.prepare(`
    INSERT INTO messages
    (conversation_id, sender_id, message_type, content)
    VALUES (?, ?, ?, ?)
`).run(
    conversationId,
    senderId,
    "text",
    content
);

---

الرابع عشر: أنواع الرسائل

النظام يجب أن يدعم:

text
image
file
audio
video
system

ويظهر النوع المناسب في الواجهة.

---

الخامس عشر: الاستشارة المجانية

المسار:

استشارة مجانية
       ↓
الاسم
       ↓
إنشاء جلسة
       ↓
فتح الشات
       ↓
إرسال السؤال
       ↓
رد المكتب

ولا يلزم إنشاء حساب كامل لهذه الخدمة إذا تم اعتماد سياسة الشات المفتوح.

---

السادس عشر: الاستشارة المدفوعة

يتم تعريف الخدمات في جدول:

services

مثلاً:

اسم الخدمة
الوصف
السعر
المدة
الحالة

المستخدم يختار:

استشارة قانونية مدفوعة

ثم:

السعر
طريقة الدفع
رفع إثبات الدفع
إرسال الطلب

---

السابع عشر: نظام الدفع اليدوي

لأن النموذج الحالي يعتمد على التحويل وإيصال الدفع، يجب تنفيذ Workflow حقيقي:

الموكل
 ↓
اختيار الخدمة
 ↓
إنشاء Payment
 ↓
رفع الإيصال
 ↓
حالة = pending
 ↓
المحامي/المدير يراجع
 ↓
approved / rejected
 ↓
عند approved
تفعيل الخدمة

مثال:

app.put(
    "/api/payments/:id/review",
    requireRole("lawyer", "admin"),
    (req, res) => {

        const { status } = req.body;

        if (!["approved", "rejected"].includes(status)) {
            return res.status(400).json({
                success: false,
                message: "حالة غير صحيحة"
            });
        }

        db.prepare(`
            UPDATE payments
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        `).run(
            status,
            req.session.userId,
            req.params.id
        );

        res.json({
            success: true
        });
    }
);

---

الثامن عشر: غرفة الفيديو

يجب استخدام WebRTC.

الوظائف:

كاميرا
ميكروفون
مشاركة الشاشة
إنهاء المكالمة
إرسال ملفات
حالة الاتصال

الإشارة Signaling تتم بواسطة Socket.IO.

مثال:

socket.on("webrtc-offer", ({ roomId, offer }) => {
    socket.to(roomId).emit("webrtc-offer", offer);
});

socket.on("webrtc-answer", ({ roomId, answer }) => {
    socket.to(roomId).emit("webrtc-answer", answer);
});

socket.on("webrtc-ice", ({ roomId, candidate }) => {
    socket.to(roomId).emit("webrtc-ice", candidate);
});

والـFrontend:

const peerConnection = new RTCPeerConnection({
    iceServers: [
        {
            urls: "stun:stun.l.google.com:19302"
        }
    ]
});

---

التاسع عشر: التحكم في الجلسة

المحامي هو صاحب صلاحيات الجلسة.

حالات:

waiting
active
paused
ended

ويمكن للمحامي:

فتح الميكروفون
منع الميكروفون
السماح بالكاميرا
إيقاف الكاميرا
إنهاء الجلسة

---

العشرون: المواعيد

جدول:

appointments

البيانات:

client_id
lawyer_id
date
start_time
end_time
type
status
notes

الحالات:

requested
confirmed
cancelled
completed

---

الحادي والعشرون: الإشعارات

جدول:

notifications

ويتم إنشاء إشعار عند:

رسالة جديدة
قبول موعد
رفض موعد
تغيير حالة قضية
رفع مستند
قبول دفع
رفض دفع
بدء جلسة

---

الثاني والعشرون: المساعد الذكي

المساعد الذكي يكون وحدة منفصلة:

🤖 المساعد القانوني

[اكتب طلبك]

🔎 بحث
📄 تحليل مستند
📝 تلخيص
📊 تقرير

Frontend:

async function sendAiRequest() {

    const input = document.getElementById("ai-input");

    const response = await fetch("/api/ai/query", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            prompt: input.value
        })
    });

    const data = await response.json();

    addAiMessage(data.answer);
}

Backend:

app.post(
    "/api/ai/query",
    requireRole("lawyer", "admin"),
    async (req, res) => {

        const { prompt } = req.body;

        if (!prompt?.trim()) {
            return res.status(400).json({
                success: false,
                message: "الطلب فارغ"
            });
        }

        // استدعاء مزود الذكاء الاصطناعي
        // يجب وضع مفتاح API في متغيرات البيئة
        // وليس داخل الكود.

        const answer = await aiService.ask(prompt);

        res.json({
            success: true,
            answer
        });
    }
);

ويجب عدم وضع API Key داخل HTML أو JavaScript الخاص بالمتصفح.

---

الثالث والعشرون: التقارير

يجب إنشاء:

تقرير الموكل
تقرير القضية
تقرير الاستشارات
تقرير المدفوعات
تقرير الجلسات
تقرير المستندات

وتوفير:

عرض
طباعة
PDF
CSV / Excel

---

الرابع والعشرون: قاعدة البيانات

الجداول الأساسية:

users
roles
permissions
role_permissions

clients
lawyers

cases
case_notes
case_documents

conversations
conversation_members
messages

consultations
appointments
video_sessions

services
payments
payment_receipts

notifications

ai_requests

audit_logs

---

الخامس والعشرون: العلاقات الأساسية

users
  │
  ├── clients
  │
  ├── lawyers
  │
  └── messages

clients
  │
  ├── cases
  ├── consultations
  ├── appointments
  └── payments

cases
  │
  ├── documents
  ├── notes
  └── conversations

conversations
  │
  └── messages

consultations
  │
  └── video_sessions

---

السادس والعشرون: الأمان

يجب تنفيذ:

Password Hashing
Authentication
Authorization
Role-Based Access Control
Input Validation
File Validation
File Size Limits
Session Security
Rate Limiting
Audit Logging

ويمنع تماماً:

password = "123456";

أو تخزين كلمات المرور كنص صريح.

---

السابع والعشرون: حماية الملفات

لا يسمح للمستخدم بتحميل أي ملف تنفيذي بشكل مباشر.

يجب التحقق من:

MIME Type
Extension
File Size
User Permission
Case Permission

ولا يستطيع موكل مشاهدة ملف قضية موكل آخر.

---

الثامن والعشرون: نظام سجل العمليات

يجب تسجيل العمليات الحساسة:

تسجيل الدخول
إنشاء قضية
تعديل قضية
رفع ملف
حذف ملف
إرسال رسالة
مراجعة دفع
تغيير صلاحية
بدء جلسة
إنهاء جلسة

مثال:

function audit(userId, action, entityType, entityId) {

    db.prepare(`
        INSERT INTO audit_logs
        (user_id, action, entity_type, entity_id)
        VALUES (?, ?, ?, ?)
    `).run(
        userId,
        action,
        entityType,
        entityId
    );
}

---

التاسع والعشرون: API النهائية

يجب أن يكون النظام منظماً تقريباً هكذا:

/api/auth
/api/users
/api/clients
/api/lawyers
/api/cases
/api/documents
/api/messages
/api/conversations
/api/consultations
/api/appointments
/api/video
/api/services
/api/payments
/api/notifications
/api/ai
/api/reports
/api/admin

---

الثلاثون: تصميم الواجهة

الهوية البصرية:

خلفية كحلية داكنة
ذهبي ملكي
أبيض
درجات ذهبية هادئة
حدود ذهبية مزدوجة عند الحاجة
زوايا ناعمة
واجهة فخمة

ويجب أن تكون:

Mobile First
Responsive
RTL
Arabic
Accessible

---

الحادي والثلاثون: تحسين الكود الحالي

الكود الذي تم إرساله يحتوي حالياً على شاشات:

1 تسجيل الدخول
2 لوحة المستخدم
3 المساعد الذكي
4 الشات المجاني
5 قاعة الاستشارة
6 الدفع
7 الشات المدفوع

يجب الاحتفاظ بهذه الأفكار، ولكن تحويلها من Screens تجريبية إلى Modules حقيقية.

مثلاً:

nextScreen(3)

يستبدل تدريجياً بنظام Routing حقيقي:

/login
/dashboard
/ai
/free-chat
/consultation
/payment
/paid-chat

---

الثاني والثلاثون: إصلاح الشات الحالي

يجب عدم استخدام:

box.innerHTML += ...

لبناء الرسائل بدون معالجة.

يجب إنشاء عنصر DOM آمن:

function addMessage(text, type) {

    const message = document.createElement("div");

    message.className = `msg ${type}`;

    message.textContent = text;

    document.getElementById("chat-box")
        .appendChild(message);
}

وهذا يمنع إدخال HTML ضار من رسائل المستخدم.

---

الثالث والثلاثون: إدارة الحالة

يجب أن يعرف البرنامج:

المستخدم الحالي
صلاحياته
القضية الحالية
المحادثة الحالية
حالة الدفع
حالة الجلسة
حالة الاتصال

ولا يعتمد على متغيرات مؤقتة في الصفحة فقط.

---

الرابع والثلاثون: حالات الخطأ

كل عملية يجب أن تتعامل مع:

نجاح
فشل
انقطاع الإنترنت
جلسة منتهية
عدم وجود صلاحية
ملف غير صالح
بيانات ناقصة
خطأ بالخادم

ويجب عرض رسالة عربية مفهومة للمستخدم.

---

الخامس والثلاثون: الاختبارات

قبل اعتبار البرنامج مكتملاً يجب اختبار:

Authentication

تسجيل مستخدم
دخول صحيح
دخول خاطئ
تسجيل خروج
جلسة منتهية

Clients

إضافة
تعديل
بحث
عرض

Cases

إنشاء
تعديل
ربط بالموكل
عرض

Files

رفع
تحميل
حذف
صلاحيات

Chat

إرسال
استقبال
تخزين
إعادة فتح المحادثة

Video

Offer
Answer
ICE
Camera
Microphone
Screen Share
Disconnect

Payments

إنشاء طلب
رفع إيصال
مراجعة
قبول
رفض
تفعيل الخدمة

---

السادس والثلاثون: معايير اكتمال البرنامج

لا يعتبر البرنامج مكتملاً لمجرد أن جميع الشاشات ظهرت.

يعتبر مكتملاً فقط عندما:

✓ قاعدة البيانات تعمل
✓ تسجيل الدخول يعمل
✓ الصلاحيات تعمل
✓ الموكل يعمل
✓ المحامي يعمل
✓ القضايا تعمل
✓ المستندات تعمل
✓ الشات يعمل
✓ الرسائل تحفظ
✓ الفيديو يعمل
✓ الملفات تعمل
✓ الدفع له Workflow حقيقي
✓ الإشعارات تعمل
✓ التقارير تعمل
✓ المساعد الذكي متصل بالBackend
✓ معالجة الأخطاء موجودة
✓ حماية البيانات موجودة
✓ الاختبارات ناجحة

---

السابع والثلاثون: تعليمات خاصة لعبقرينو

يجب على عبقرينو عدم الاكتفاء بإنشاء التصميم.

عند بناء كل وحدة يجب أن ينشئ:

1. HTML
2. CSS
3. JavaScript
4. Backend API
5. Database Table
6. Validation
7. Error Handling
8. Permission Check
9. Test

مثلاً عند إنشاء وحدة القضايا لا ينشئ صفحة القضايا فقط.

بل ينشئ:

cases.html
cases.js
cases.css

GET /api/cases
POST /api/cases
PUT /api/cases/:id
DELETE /api/cases/:id

cases table

validation

permissions

tests

---

الثامن والثلاثون: أسلوب التنفيذ المرحلي

يجب ألا يحاول عبقرينو إنشاء المشروع كله في خطوة واحدة إذا كان ذلك سيؤدي إلى كود ناقص أو وهمي.

التنفيذ يكون:

المرحلة 1
الهيكل الأساسي + قاعدة البيانات

        ↓

المرحلة 2
Authentication + Users

        ↓

المرحلة 3
Client Dashboard

        ↓

المرحلة 4
Lawyer Dashboard

        ↓

المرحلة 5
Clients + Cases

        ↓

المرحلة 6
Documents

        ↓

المرحلة 7
Chat + Socket.IO

        ↓

المرحلة 8
Video + WebRTC

        ↓

المرحلة 9
Payments

        ↓

المرحلة 10
Appointments + Notifications

        ↓

المرحلة 11
AI Assistant

        ↓

المرحلة 12
Reports

        ↓

المرحلة 13
Security

        ↓

المرحلة 14
Testing

        ↓

المرحلة 15
Production Build

---

التاسع والثلاثون: قاعدة مهمة جداً

إذا كان هناك جزء لا يمكن تنفيذه فعلياً بدون خدمة خارجية، فلا يتم إنشاء زر وهمي له.

مثلاً:

الدفع الإلكتروني
SMS
البريد الإلكتروني
AI API
Cloud Storage
TURN Server

يجب إنشاء Integration Interface واضحة، مع وضع إعداداتها في:

.env

مثال:

PORT=3000
SESSION_SECRET=
AI_API_KEY=
DATABASE_PATH=
TURN_SERVER=
TURN_USERNAME=
TURN_PASSWORD=

---

الأربعون: المطلوب من عبقرينو في نهاية كل مرحلة

بعد إنهاء كل مرحلة يجب أن يعرض:

✓ الملفات التي تم إنشاؤها
✓ الملفات التي تم تعديلها
✓ الوظائف التي تم تنفيذها
✓ API التي تم إنشاؤها
✓ جداول قاعدة البيانات
✓ الاختبارات التي تم تشغيلها
✓ نتيجة الاختبارات
✓ الأخطاء المتبقية

ولا يقول:

تم بنجاح

إلا بعد تشغيل اختبار فعلي للوظيفة.

---

الحادي والأربعون: النتيجة النهائية المطلوبة

المنتج النهائي يجب أن يكون:

⚖️ منصة قانونية متكاملة

وليست مجرد:

HTML Demo

بل:

Frontend
      +
Backend
      +
Database
      +
Authentication
      +
Authorization
      +
Realtime
      +
WebRTC
      +
File Management
      +
Payment Workflow
      +
Notifications
      +
AI Integration
      +
Reports
      +
Security

---

الثاني والأربعون: أمر التنفيذ النهائي لعبقرينو

يجب اعتبار هذه الوثيقة مواصفة المشروع الأساسية.

ابدأ من الكود الحالي المقدم لك، وحافظ على الهوية البصرية والفكرة العامة، ثم قم بتحويل النموذج التجريبي إلى تطبيق حقيقي كامل الوظائف.

لا تحذف الوظائف الموجودة إلا إذا كان هناك سبب تقني واضح.

لا تنشئ وظائف وهمية.

لا تستخدم "alert()" كبديل عن Backend.

لا تخزن كلمات المرور بشكل صريح.

لا تضع مفاتيح API داخل Frontend.

لا تسمح للمستخدم بالوصول إلى بيانات مستخدم آخر.

كل وظيفة يجب أن يكون لها Frontend وBackend وDatabase عند الحاجة.

بعد كل مرحلة شغّل الاختبارات المناسبة وسجل نتيجتها.

إذا كانت هناك خدمة خارجية مطلوبة، أنشئ لها Integration Layer وإعدادات ".env" بدلاً من اختراع خدمة وهمية.

ابدأ أولاً ببناء البنية الأساسية وقاعدة البيانات والمصادقة، ثم نفذ باقي الوحدات بالترتيب المرحلي المحدد أعلاه.

الهدف النهائي:

منصة استشارات قانونية حقيقية قابلة للتشغيل والتطوير والنشر، وليست مجرد نموذج واجهات.

تم إنشاء هذا المشروع بواسطة عبقرينو Studio.

## البنية

- public — واجهة البرنامج
- server — تشغيل المشروع
- routes — مسارات التطبيق
- services — الخدمات والمنطق
- database — طبقة البيانات
- uploads — الملفات المرفوعة
- .abqaryno-requirements.json — المتطلبات والشاشات المعتمدة

## التشغيل

python server/server.py
