# عبقرينو — Core Contract

## 1. الغرض

الـ Core هو النواة العامة لإدارة دورة العمل داخل عبقرينو.

وظيفته:
- فهم الحالة الحالية.
- حفظ المعلومات المتاحة.
- تحديد المتطلبات.
- بناء الخطة.
- بناء الخريطة.
- اتخاذ القرار.
- تحديد الخطوة التالية.
- الانتظار عند نقص المعلومات.
- التوقف عند التعارض أو اكتشاف دورة غير صالحة.
- تسجيل كل انتقال قبل/بعد.

الـ Core لا يعتمد على مشروع أو تقنية أو ملف أو لغة برمجة محددة.

## 2. الحالات الرسمية

NEW
UNDERSTANDING
REQUIREMENTS
PLANNING
MAPPING
DECISION
NEXT_STEP
WAITING
BLOCKED
STOPPED
COMPLETED

## 3. القواعد الأساسية

1. لا يوجد انتقال غير موجود في خريطة الانتقالات.
2. كل انتقال يجب أن يكون له سبب.
3. كل قرار يجب أن يحتوي على action و reason و target_state.
4. نقص المعلومات يؤدي إلى WAITING.
5. التعارض يؤدي إلى BLOCKED أو STOPPED حسب القرار.
6. WAITING لا ينتقل إلى WAITING تلقائياً.
7. STOPPED حالة نهائية.
8. COMPLETED حالة نهائية.
9. لا يسمح للـ Core بالدخول في دورة لا نهائية.
10. كل انتقال يسجل before و after.
11. لا يتم تعديل منطق الـ Core بناءً على مشروع خارجي.
12. لا يفترض الـ Core أسماء ملفات أو تقنيات أو بنية مشروع.
13. عند غياب قاعدة قرار صالحة يجب التوقف بدلاً من التخمين.

## 4. البيانات الأساسية

CoreContext يحتوي على:
- state
- goal
- facts
- requirements
- plan
- map_data
- next_step
- history
- evidence
- status

## 5. Evidence

كل Evidence يحتوي على:
- source
- fact
- confidence

ولا يقبل المصدر أو الحقيقة الفارغة، ولا confidence خارج 0..1.

## 6. Decision

كل Decision يحتوي على:
- action
- reason
- target_state
- evidence

ولا يسمح بقرار ناقص.

## 7. Transition

كل Transition يحتوي على:
- before
- after
- reason
- decision

## 8. Engine Contract

CoreEngine.step():

1. يتحقق من السياق.
2. يمنع التشغيل بعد STOPPED.
3. يمنع التشغيل بعد COMPLETED.
4. يحصل على القرار.
5. يتحقق من القرار.
6. يتحقق من الانتقال.
7. يكشف الدورة غير الصالحة.
8. يسجل الانتقال.
9. يحدّث الحالة.
10. يعيد Transition.

## 9. مبدأ التوقف الآمن

عند وجود:
- معلومات ناقصة → WAITING.
- تعارض → BLOCKED أو STOPPED.
- دورة غير صالحة → STOPPED.
- حالة غير معروفة → STOPPED/خطأ واضح.
- عدم وجود قاعدة قرار → خطأ واضح.

لا يسمح بالتخمين أو الدوران اللانهائي.

## 10. حدود الـ Core

الـ Core لا ينفذ بنفسه:
- إنشاء التطبيقات.
- إصلاح الكود.
- WebRTC.
- Socket.IO.
- Deployment.
- تعديل مشاريع المستخدم.
- اختيار تقنية لمجرد افتراضها.

هذه وظائف خارجية تستخدم الـ Core لاحقاً.

## 11. مبدأ التوسع

أي Engine لاحق يجب أن يتعامل مع الـ Core من خلال هذا العقد، ولا يغير قواعده الداخلية مباشرة.

## 12. حالة المواصفة

Core Contract Version: 0.1
Core Status: STABLE
Creation Engine: DEFERRED
Repair Engine: DEFERRED
WebRTC: DEFERRED
Deployment: DEFERRED
