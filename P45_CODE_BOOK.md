# P45 — بيز 45
# كتاب الأكواد — P45 CODE BOOK

> **الوثيقة المرجعية الهندسية للمشروع**
>
> هذه الوثيقة هي مصدر الحقيقة الهندسي لصيانة P45 وتطويره. لا تُعامل كشرح عابر، بل كخريطة تشغيلية تحفظ فلسفة المشروع، معماريته، دورة التنفيذ، حالة المحركات، الأدلة المثبتة، والفجوات المعروفة.

---

## 1. هوية المشروع

**الاسم:** P45 — بيز 45  
**الدور الحالي:** مستودع إصلاح وهندسة مشاريع برمجية  
**الهدف النهائي:** التحول من Repair Engine إلى **Engineering Platform** قادرة على فهم المشروع وتحليله وتشخيصه وإصلاحه والتحقق منه، ثم لاحقًا إنشاء مشاريع جديدة وتطويرها وترقيتها ونقلها ونشرها.

### قاعدة الهوية

> لا نعيد بناء شيء موجود. لا نستبدل شيئًا يعمل. لا نكرر وظيفة موجودة. نربط الموجود إذا كان منفصلًا، ونصلح الموجود إذا كان معيبًا، ونضيف فقط ما ثبت أنه مفقود.

---

## 2. أصل الفكرة

بدأ P45 من مشكلة حقيقية في مشروع **بلبل**. كان الهدف الأول إنشاء أداة تصلح العطل. أثناء التطوير اتسعت الفكرة بعد دراسة ما يمكن أن تفعله منصات مثل Base44، ثم أصبح الهدف بناء نظام مستقل يستطيع:

- فهم المشاريع.
- اكتشاف البنية والعلاقات.
- جمع الأدلة.
- تشخيص الأسباب الجذرية.
- تخطيط الإصلاح.
- تنفيذ إصلاحات مضبوطة بعد موافقة صريحة.
- أخذ Snapshot قبل التعديل.
- اختبار التغيير والتحقق منه.
- إعادة التحليل بعد الإصلاح.
- إنتاج تقرير قابل للمراجعة.
- تسجيل كل خطوة في Execution Log.
- الانتقال لاحقًا إلى إنشاء وتطوير المشاريع، لا إصلاحها فقط.

**بلبل هو الشرارة وحالة الاستخدام الأولى، وليس الغاية النهائية لـ P45.**

---

## 3. فلسفة P45

القواعد التالية غير قابلة للتجاوز أثناء الصيانة:

1. لا تعديل قبل الفهم.
2. لا حذف بلا دليل.
3. لا إصلاح بلا سبب موثق.
4. لا نجاح بلا اختبار.
5. لا اختراع لمتطلبات أو كود غير مثبت.
6. لا استبدال لواجهة تعمل بلا ضرورة.
7. الحفاظ على الأجزاء العاملة.
8. تطوير الأجزاء PARTIAL.
9. إصلاح الأجزاء BROKEN.
10. تقوية الأجزاء EXPERIMENTAL.
11. كل معلومة مهمة يجب أن يكون لها Evidence.
12. التمييز بين VERIFIED و INFERRED.
13. Simulation ليست Repair.
14. Planned ليست Applied.
15. Applied ليست Verified.
16. وجود المحرك لا يعني أنه نُفذ.
17. تنفيذ المحرك لا يعني نجاحه.
18. نجاح المحرك لا يعني أن مخرجاته صالحة للاستهلاك.
19. لا تعتبر مرحلة مخرجات مرحلة سابقة موجودة إلا بعد إثبات وجودها وصحتها ومصدرها.

### المبدأ النهائي

> **P45 يجب أن يفهم قبل أن يتصرف، وأن يثبت قبل أن يدّعي النجاح.**

---

## 4. دورة حياة P45 الرسمية

```text
PROBLEM
  ↓
DISCOVER
  ↓
ANALYZE
  ↓
DIAGNOSE
  ↓
PLAN
  ↓
APPROVE
  ↓
SNAPSHOT
  ↓
REPAIR
  ↓
TEST
  ↓
VERIFY
  ↓
RE-ANALYZE
  ↓
REPORT
  ↓
EXECUTION LOG
```

والصيغة التشغيلية التفصيلية:

```text
Problem
→ Project Reader
→ Architecture
→ Evidence
→ Usage Graph
→ Contract Graph
→ Plan vs Reality
→ Root Cause
→ Repair Plan
→ User Approval
→ Snapshot
→ Repair
→ Verification
→ Re-Analysis
→ Final Report
→ Execution Log
```

---

## 5. Architecture Map — خريطة المعمارية

### 5.1 Project Scanner

**الملف:** `engine/scanner.py`

**الدور:** قراءة المشروع وتصنيف ملفاته ومجلداته.

**الحالة الحالية المثبتة:**
- يقرأ المشروع بصورة recursive.
- يستبعد مجلدات تشغيلية مثل `node_modules` و`plans` و`reports` و`snapshots` و`logs` وغيرها.
- يصنف client/server/config/tests/assets/other.

**المخرجات:** `reports/scan-report.json`

**قاعدة مهمة:** نتائج التصنيف دليل على ما اكتشفه Scanner، وليست دليلًا مطلقًا على عدم وجود شيء لم يصنفه.

---

### 5.2 Contract Analyzer

**الملف:** `engine/socketio.py`

**الدور:** تحليل Socket.IO وWebRTC وأنماط الاتصال والعقود البرمجية.

**يبحث عن:**
- Socket.IO initialization.
- emits.
- handlers.
- WebRTC APIs.
- signaling patterns.
- partial/evidence-limited findings.

**المخرج المتوقع:** `reports/contracts-report.json`

**مبدأ:** غياب تطابق Regex ليس إثباتًا قاطعًا لغياب عقد ديناميكي أو غير مباشر.

---

### 5.3 Contract Graph

**الملف:** `engine/contract_graph.py`

**الدور:** تحويل نتائج التحليل إلى رسم للعقود والعلاقات بين أجزاء المشروع.

**العقد الحالية:**
- server:socketio
- client:socketio
- signaling
- media-capture
- peer-connection
- remote-track
- dom:remote-video

**العلاقات:**
- client socket → server socket transport
- client socket → signaling contract
- media capture → peer connection
- peer connection → remote track
- remote track → DOM remote video

**المخرج:** `reports/contract-graph.json`

**ملاحظة معمارية مهمة:** التنفيذ الحالي يعتمد على أسماء root-level مثل `server.js` و`public/app.js` و`public/index.html`، بينما المشروع المستهدف الحالي يحتوي هذه الملفات داخل `بلبل-الجديد/`. هذه فجوة يجب إصلاحها في orchestration/path resolution قبل الاعتماد على الرسم كحقيقة للمشروع.

---

### 5.4 Root Cause Engine

**الملف:** `engine/root_cause.py`

**الدور:** تحويل Contract Graph + source evidence إلى أسباب جذرية قابلة للتتبع.

**التصنيفات:**
- CONFIRMED
- DERIVED
- INFERRED
- EVIDENCE_LIMITED

**أمثلة من منطق المحرك:**
- غياب `RTCPeerConnection` يمكن أن ينتج سببًا CONFIRMED في سياق التحليل.
- غياب signaling patterns يمكن أن ينتج سببًا CONFIRMED.
- `getUserMedia` مع `localStream` بلا `addTrack` يمكن أن ينتج DERIVED.
- بعض استنتاجات runtime تبقى INFERRED وتحتاج اختبار متصفح فعلي.

**المخرج:** `reports/root-cause-report.json`

**ملاحظة مهمة:** المحرك الحالي يقرأ root-level paths مثل `server.js` و`public/app.js` و`public/index.html`، لذلك يحتاج إلى ربط صحيح بجذر المشروع المستهدف قبل اعتباره منتجًا صالحًا للدورة الكاملة.

---

### 5.5 Planner

**الملف:** `engine/planner.py`

**الدور:** تجميع نتائج Scanner/Contracts/Graph/Root Cause وإنشاء خطة تنفيذ.

**المخرج:** `plans/execution-plan.json`

**Candidate schema:**
- `candidate_id`
- `reason`
- `title`
- `classification`
- `severity`
- `target`
- `status`
- `requires`
- `evidence`
- `verification`

**فجوة مثبتة:** `_load_report()` يعيد `{}` إذا كان التقرير مفقودًا. هذا قد يحول غياب الدليل إلى مظهر يشبه عدم وجود findings. يجب في النسخة المعمارية النهائية التمييز بين:

```text
REPORT_PRESENT_AND_EMPTY
REPORT_MISSING
REPORT_INVALID
REPORT_STALE
REPORT_VALID
```

ولا يجوز مساواة `REPORT_MISSING` بـ `REPORT_PRESENT_AND_EMPTY`.

---

### 5.6 Approval

**الحالة:** موجود كمبدأ في `RepairAction` وCLI، لكنه ليس بعد محرك موافقة مستقلًا مرتبطًا بالكامل بـ `candidate_id`.

**القاعدة:** لا إصلاح فعلي بلا موافقة صريحة.

---

### 5.7 Snapshot

**الملف:** `engine/snapshot.py`

**الدور:** إنشاء نسخة immutable من الهدف قبل التعديل وحساب SHA256.

**التحقق:**
- target exists
- snapshot exists
- SHA قبل التعديل
- SHA للنسخة
- فشل إذا لم تتطابق النسخة مع المصدر.

**الحالة:** مثبتة باختبار عملي داخل Execution Log.

---

### 5.8 Exact Repair

**الملف:** `engine/repair.py`

**الدور:** تنفيذ تعديل نصي دقيق ومحدود.

**ضمانات مثبتة:**
- approval required.
- target must be inside project.
- target must exist and be a file.
- `old_text` must match exactly.
- يجب أن يكون التطابق واحدًا فقط.
- Snapshot قبل التعديل.
- SHA قبل وبعد.
- رفض إذا لم يتغير SHA.
- تسجيل APPLIED بعد نجاح التغيير.

**الدالة الأساسية:** `apply_exact_change(...)`

**ملاحظة:** `execute_repairs()` الحالي آمن كـ no-op عندما لا يوجد approved repair action.

**الاستنتاج:** لا حاجة لإعادة بناء `engine/repair.py` لمجرد تحسين التكامل؛ المطلوب أساسًا هو ربطه بخطة/candidate موثقة وموافق عليها.

---

### 5.9 Verification

**الملف:** `engine/verification.py`

**الدور:** إثبات أن التغيير النصي المتوقع حدث.

**Exact Verification الحالية:**
- target exists
- old text absent
- new text present

**الحالة:** مثبتة عمليًا عبر `P45-VERIFY-001` و`P45-CLI-VERIFY-001`.

**الفجوة:** Exact Verification ليست Behavioral Verification. النجاح النصي لا يثبت أن التطبيق يعمل سلوكيًا.

---

### 5.10 Execution Log

**الملف:** `engine/execution_log.py`

**الدور:** تسجيل الأحداث الزمنية لجميع مراحل التنفيذ.

**الحقول المستخدمة:**
- timestamp
- phase
- action
- status
- target
- reason
- evidence
- before_sha256
- after_sha256
- snapshot
- tests
- verification
- error
- result

**المبدأ:** Execution Log هو سجل حقيقة التنفيذ، وليس بديلًا عن Architecture Map.

---

## 6. State Machine

**الملف:** `engine/contracts.py`

الحالات المعرفة حاليًا:

```text
DISCOVERED
EVIDENCED
PLANNED
APPROVED
SNAPSHOTTED
APPLIED
VERIFIED
FAILED
NOT_APPLIED
REJECTED
```

التسلسل المنطقي:

```text
DISCOVERED
  ↓
EVIDENCED
  ↓
PLANNED
  ↓
APPROVED
  ↓
SNAPSHOTTED
  ↓
APPLIED
  ↓
VERIFIED
```

مع مسارات فشل/رفض:

```text
REJECTED
NOT_APPLIED
FAILED
```

**قاعدة:** لا يتم استنتاج حالة أعلى من دليل أقل. مثلًا `APPLIED` لا تعني تلقائيًا `VERIFIED`.

---

## 7. CLI Architecture

**الملف:** `repair-repository.py`

الأوامر الحالية:

```text
scan
contracts
plan
diagnose
repair
verify
full
```

### الواقع الحالي

`cmd_full` ينفذ فعليًا:

```text
scan
→ contracts
→ plan
→ diagnose
```

ثم لا ينفذ repair إلا إذا أعطي direct repair مع target وold/new.

**الفجوة الرئيسية:** `cmd_plan` و`cmd_diagnose` و`cmd_full` لا يثبت من الكود الحالي أنها تستدعي صراحة:

```text
ContractGraphEngine
RootCauseEngine
```

لذلك وجود المحركين في `engine/` لا يعني أنهما يدخلان في دورة CLI.

---

## 8. Plan vs Reality

### Planned

المعمارية المخططة:

```text
Scanner
→ Contract Analyzer
→ Contract Graph
→ Root Cause
→ Planner
→ Approval
→ Snapshot
→ Repair
→ Test
→ Verify
→ Re-Analyze
→ Report
```

### Reality المثبتة في آخر تدقيق

```text
Scanner
→ Contract Analyzer
→ Planner
→ Diagnose
```

مع وجود Graph وRoot Cause كملفات engine، لكن دون إثبات orchestration الكامل.

### القاعدة

> **وجود Engine ≠ Engine Executed ≠ Engine Succeeded ≠ Output Validated ≠ Output Consumed**

---

## 9. الحالة الفعلية للمشروع المستهدف

المشروع المستهدف الحالي داخل P45 هو:

```text
بلبل-الجديد/
```

آخر Scanner أثبت:

- 23 ملفًا.
- 10 مجلدات.
- 2 client files.
- 1 server file.
- 1 config file.
- 0 test files.

الملفات المهمة المكتشفة:

```text
بلبل-الجديد/public/app.js
بلبل-الجديد/public/index.html
بلبل-الجديد/server.js
بلبل-الجديد/package.json
```

---

## 10. حالة التقارير

داخل P45 root `reports/` كانت الحالة المثبتة:

```text
contracts-report.json
scan-report.json
```

وكان `contracts-report.json` في آخر فحص غير صالح للاعتماد الكامل، حيث ظهرت قيم مثل:

```text
project = None
files_analyzed = None
emits = 0
handlers = 0
socketio_initialization = 0
webrtc = 0
findings = 0
```

بينما كانت هناك تقارير داخل:

```text
بلبل-الجديد/reports/
```

منها:

```text
contract-graph.json
contracts-report.json
deep-repair-report.json
root-cause-report.json
scan-report.json
```

**لا يجوز افتراض أن تقريرًا داخل المشروع المستهدف هو نفسه تقرير P45 إلا بعد إثبات المصدر والزمن والجذر.**

---

## 11. آخر Execution Plan المثبت

آخر إعادة توليد للخطة أعطت:

```text
status: PLANNED
findings: 1 WARNING
planned actions: 1
repair_candidates: []
```

التحذير:

```text
No test files were classified by the scanner.
```

والإجراء المخطط:

```text
P45-PLAN-TEST-COVERAGE-001
```

والسبب:

```text
Establish project verification coverage before claiming behavioral repair success.
```

### Evidence المثبتة في الخطة

1. Scanner identified 23 project files, 10 directories.
2. Client classification = 2 files.
3. Server classification = 1 file.
4. Config classification = 1 file.
5. Tests = 0.
6. Contract analyzer inspected 0 files في التقرير الحالي.
7. Socket.IO emit/on contracts لم تثبت، والحالة EVIDENCE_LIMITED.
8. Root Cause Engine produced 0 traceable root causes في التقرير الذي استهلكته Planner.

**لكن هذه النقطة لا تعني أن Root Cause Engine أثبت أن المشروع بلا أسباب؛ لأن التقارير المطلوبة كانت مفقودة من P45 root، وPlanner كان يتعامل مع المفقود كـ `{}`.**

---

## 12. Execution Evidence المثبتة

### P45-TEST-001

تم اختبار Exact Repair فعليًا:

- Snapshot.
- before SHA.
- Apply.
- after SHA مختلف.
- تسجيل APPLIED.

### P45-VERIFY-001

تم التحقق من:

```text
TARGET_EXISTS = true
OLD_TEXT_ABSENT = true
NEW_TEXT_PRESENT = true
```

والحالة:

```text
VERIFIED
```

### P45-CLI-REPAIR-001

تم اختبار مسار CLI المباشر:

- direct mode = true
- Snapshot.
- before SHA.
- after SHA.
- APPLIED.

### P45-CLI-VERIFY-001

تم التحقق من التغيير النصي:

```text
VERIFIED
```

### ما لم يثبت بعد

- لم يتم تنفيذ إصلاح حقيقي من أحد Root Cause Candidates.
- لم يتم إثبات Candidate-bound approval.
- لم يتم إثبات Behavioral Verification.
- لم يتم إثبات Post-Repair Re-Analysis.
- لم يتم إثبات Final Report كامل.

---

## 13. Execution Log — ملخص الحقيقة التنفيذية

السجل الحالي `logs/execution-log.json` يثبت بالتتابع:

```text
VERIFY request → NOT_EXECUTED
REPAIR request بدون approved action → NOT_APPLIED
P45-TEST-001 → SNAPSHOTTED → APPLIED
P45-VERIFY-001 → VERIFIED
P45-CLI-REPAIR-001 → SNAPSHOTTED → APPLIED
P45-CLI-VERIFY-001 → VERIFIED
```

هذا يثبت أن **آلية الإصلاح الدقيقة تعمل في اختبارات معزولة**، لكنه لا يثبت أن دورة التشخيص والإصلاح الكاملة للمشروع المستهدف مكتملة.

---

## 14. أهم الفجوات المعمارية الحالية

1. Graph/Root Cause غير مربوطين بدورة CLI الكاملة بصورة مثبتة.
2. التقرير المفقود قد يتحول إلى `{}` داخل Planner.
3. لا توجد حالة صريحة موحدة لـ Missing/Stale/Invalid Reports.
4. Contract Analyzer الحالي لم يثبت تحليل ملفات الهدف في التقرير الأخير.
5. لا توجد ملفات tests مصنفة.
6. لا توجد Post-Repair Re-Analysis كاملة.
7. لا يوجد Final Report كامل للدورة.
8. Approval ليس مربوطًا بالكامل بـ `candidate_id`.
9. Planned actions وRepair Candidates غير متصلين بالكامل بمسار CLI.
10. بعض المحركات تفترض root-level paths بينما الهدف داخل `بلبل-الجديد/`.

---

## 15. قاعدة عدم التكرار

قبل إضافة أي Engine أو ملف أو وظيفة:

### اسأل بالترتيب

1. هل الوظيفة موجودة؟
2. أين توجد؟
3. هل تعمل؟
4. هل يتم استدعاؤها؟
5. هل مخرجاتها صحيحة؟
6. هل يستهلكها المستهلك الصحيح؟
7. هل المشكلة في الوظيفة أم في orchestration؟

### القرار

```text
موجود + يعمل + مربوط
→ لا نلمسه.

موجود + يعمل + غير مربوط
→ نربطه.

موجود + معيب
→ نصلحه.

موجود + غير مستخدم لكن مطلوب
→ ندمجه بعد إثبات مكانه.

غير موجود + ثبت الاحتياج
→ نضيفه.

غير مثبت الاحتياج
→ لا نضيفه.
```

---

## 16. Architecture Source of Truth

هذه الوثيقة هي **Code Book**، لكنها لا تلغي الملفات التنفيذية.

مصادر الحقيقة موزعة حسب الوظيفة:

```text
P45_CODE_BOOK.md
    ↓ فلسفة + معمارية + قرارات + خريطة
README.md
    ↓ واجهة الاستخدام الأساسية
plans/execution-plan.json
    ↓ الخطة التنفيذية الحالية
logs/execution-log.json
    ↓ الحقيقة التنفيذية الزمنية
reports/*.json
    ↓ الأدلة والتحليلات الناتجة
engine/*.py
    ↓ التنفيذ الفعلي
```

**إذا تعارض الوصف مع الكود الفعلي:** الكود الفعلي يحتاج تدقيقًا، ولا يجوز تعديل الوثيقة لتغطية خطأ تنفيذي دون تسجيل القرار.

---

## 17. طريقة صيانة P45 مستقبلًا

أي مساعد جديد يجب أن يبدأ بهذا الترتيب:

```text
1. اقرأ P45_CODE_BOOK.md
2. اقرأ README.md
3. اقرأ plans/execution-plan.json
4. اقرأ logs/execution-log.json
5. افحص reports الحالية
6. افحص Architecture Map مقابل الكود الفعلي
7. حدد Plan vs Reality
8. لا تعدّل قبل تحديد الفجوة
9. نفذ أقل تعديل ممكن
10. اختبر syntax/tests
11. تحقق Exact + Behavioral عند الحاجة
12. أعد التحليل
13. حدّث Execution Log
14. حدّث Code Book إذا تغيرت المعمارية
```

---

## 18. بروتوكول تعديل أي Engine

قبل تعديل أي `engine/*.py`:

```text
READ
→ IDENTIFY CONTRACT
→ LOCATE CONSUMERS
→ VERIFY INPUTS
→ VERIFY OUTPUTS
→ VERIFY CURRENT CALL PATH
→ PATCH MINIMALLY
→ SYNTAX CHECK
→ FOCUSED TEST
→ RE-ANALYZE
→ LOG
```

لا يتم استبدال Engine كامل بسبب فجوة صغيرة.

---

## 19. بروتوكول إنشاء تقرير جديد

أي تقرير جديد يجب أن يجيب عن:

- من أنشأه؟
- متى؟
- على أي project root؟
- من أي input reports؟
- ما حالة inputs؟
- ما الذي تم تحليله فعليًا؟
- ما الذي لم يمكن إثباته؟
- ما findings؟
- ما evidence؟

ويجب أن يميز على الأقل بين:

```text
VALID
MISSING
INVALID
STALE
EVIDENCE_LIMITED
```

---

## 20. Verification Model

### Exact Verification

تثبت أن النص المطلوب تغير كما هو متوقع.

### Behavioral Verification

تثبت أن السلوك المطلوب يعمل فعليًا.

### قاعدة

```text
Exact Verified
≠
Behaviorally Verified
```

وفي المشاريع التي تحتوي WebRTC أو Socket.IO أو UI تفاعلية، يجب عدم الادعاء بنجاح سلوكي اعتمادًا على فحص النص فقط.

---

## 21. Safety Model

الإصلاح المسموح يجب أن يمر عبر:

```text
Candidate
→ Approval
→ Snapshot
→ Exact Repair
→ SHA
→ Verification
```

ولا يجوز تحويل:

```text
PLAN
```
إلى:

```text
APPLIED
```

إلا بدليل تنفيذي.

---

## 22. V2 / V3 / V4 — إرث هندسي لا يُحذف

الإصدارات السابقة تحتوي أفكارًا مهمة ولا ينبغي حذفها لمجرد أن المسار الحالي تطور.

### V2
- Truth Trace.
- API tracing.
- Socket tracing.
- Execution Plan comparison.
- syntax tests.
- evidence references.

### V3
- Plan vs Reality.
- extra files.
- duplicate detection.
- unused dependency candidates.
- artifacts.
- cleanup authorization.
- repair action candidates.

### V4
- architecture summary.
- client/server Socket.IO analysis.
- API contract analysis.
- Socket contract comparison.

**قاعدة:** لا ندمج أو نحذف أفكار V2/V3/V4 إلا بعد معرفة دورها الحالي في Architecture Map.

---

## 23. خارطة الطريق الكبرى

### P45-0 — Origin
بلبل → مشكلة حقيقية → فكرة أداة إصلاح.

### P45-1 — العقل
Project Understanding + Scanner + Architecture.

### P45-2 — التشخيص
Contracts + Contract Graph + Root Cause.

### P45-3 — Controlled Repair
Approval + Snapshot + Exact Repair.

### P45-4 — Verification
Exact + Behavioral + Re-Analysis.

### P45-5 — Full Engineering Cycle
من المشكلة إلى التقرير النهائي مع Execution Log كامل.

### P45-6 — Project Generator
إنشاء مشاريع جديدة اعتمادًا على فهم المتطلبات والبنية والعقود.

### P45-7 — Engineering Platform
Repair + Build + Upgrade + Migration + Deployment + Maintenance.

---

## 24. قرارات معمارية مهمة

### القرار 001
P45 ليس مجرد أداة إصلاح نصي؛ الإصلاح النصي مرحلة واحدة من دورة هندسية كاملة.

### القرار 002
بلبل هو أول مشروع وحالة استخدام، وليس حدود المنتج.

### القرار 003
Architecture Map يجب أن تكون المرجع قبل إعادة بناء أي وظيفة.

### القرار 004
وجود Engine لا يعني دخوله في دورة التنفيذ.

### القرار 005
Missing report لا يساوي Empty report.

### القرار 006
Planner لا يجوز أن يفسر غياب report كدليل على غياب findings.

### القرار 007
Exact Verification لا تكفي وحدها للمشاريع السلوكية.

### القرار 008
Execution Log يسجل ما حدث، ولا يثبت وحده أن المعمارية صحيحة.

### القرار 009
المسارات يجب أن تكون project-root aware ولا تعتمد على أسماء root-level ثابتة عندما يكون الهدف nested.

### القرار 010
لا نضيف محركًا جديدًا إذا كانت الوظيفة موجودة ويمكن ربطها أو إصلاحها.

---

## 25. Known Gaps — الحالة التي يجب ألا تُنسى

هذه الفجوات ليست اقتراحات عشوائية؛ هي ناتجة عن التدقيق الفعلي الأخير:

- Graph engine موجود لكن orchestration غير مثبت.
- Root Cause engine موجود لكن orchestration غير مثبت.
- Planner يتسامح مع missing reports.
- Contract report الأخير لا يثبت تحليل الهدف بصورة صحيحة.
- لا tests مصنفة.
- لا Post-Repair Re-Analysis كاملة.
- لا Final Report كاملة.
- Candidate approval غير مربوط بالكامل بـ candidate_id.
- CLI repair يقبل target/old/new يدويًا بدل ربط الإصلاح مباشرة بخطة candidate موثقة.
- بعض engines تفترض root-level paths بينما الهدف الحالي nested.

---

## 26. لا تعتبر هذه الوثيقة بديلًا عن الأدلة

Code Book يشرح **كيف يجب أن يعمل P45** و**ما الذي ثبت حتى الآن**، لكنه لا يسمح بتجاوز الدليل.

عند وجود تعارض:

```text
Actual Source
+ Execution Log
+ Valid Report
+ Test Result
```

تسبق أي افتراض مكتوب.

إذا كانت الوثيقة قديمة، يجب تحديثها بعد إثبات التغيير، لا قبل ذلك.

---

## 27. حالة الوثيقة

```text
DOCUMENT: P45_CODE_BOOK.md
ROLE: Engineering Source of Truth
STATUS: INITIALIZED
BASIS: Actual P45 source audit + execution evidence
TARGET: P45 / بيز 45
CURRENT USE: Maintenance + Architecture + Continuity
NEXT: Keep synchronized with verified architectural changes
```

---

# الخلاصة

P45 ليس ملفًا واحدًا ولا Engine واحدًا.

هو منظومة يجب أن تتصل مراحلها بهذا الشكل:

```text
UNDERSTAND
   ↓
EVIDENCE
   ↓
DIAGNOSE
   ↓
PLAN
   ↓
APPROVE
   ↓
SNAPSHOT
   ↓
REPAIR
   ↓
TEST
   ↓
VERIFY
   ↓
RE-ANALYZE
   ↓
REPORT
   ↓
LEARN / UPDATE CODE BOOK
```

والقاعدة التي يجب أن تبقى مع P45 في كل صيانة مستقبلية:

> **لا نبني ما هو موجود. لا نستبدل ما يعمل. لا نكرر وظيفة موجودة. نربط الموجود إذا كان منفصلًا. نصلح الموجود إذا كان معيبًا. نضيف فقط ما ثبت أنه مفقود.**

> **P45 يفهم قبل أن يتصرف، ويثبت قبل أن يدّعي النجاح.**
