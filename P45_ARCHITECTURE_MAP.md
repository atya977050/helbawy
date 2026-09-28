# P45 — بيز 45
# الخريطة المعمارية الرسمية — P45 ARCHITECTURE MAP

> هذه الوثيقة هي مصدر الحقيقة المعماري الرسمي لـ P45، وتعمل مع P45_CODE_BOOK.md.

## القاعدة الأساسية

> لا نعيد بناء شيء موجود.
> لا نستبدل شيئًا يعمل.
> لا نكرر وظيفة موجودة.
> نربط الموجود إذا كان منفصلًا.
> نصلح الموجود إذا كان معيبًا.
> نضيف فقط ما ثبت أنه مفقود.

---

## 1. هوية P45

P45 بدأ من مشكلة حقيقية في مشروع بلبل، ثم تطور من فكرة إصلاح عيب إلى مشروع هندسي أوسع.

الهدف النهائي:

> Engineering Platform

منصة تستطيع فهم المشاريع وتحليلها وتشخيصها وتخطيط إصلاحها وتنفيذ الإصلاح بصورة مضبوطة والتحقق منه، ثم لاحقًا إنشاء المشاريع وتطويرها وترقيتها ونقلها ونشرها.

بلبل هو نقطة البداية وحالة الاستخدام الأولى، وليس حدود P45 النهائية.

---

## 2. دورة P45 الرسمية

### مسار المشروع القائم

DISCOVER → ANALYZE → DIAGNOSE → PLAN → APPROVE → SNAPSHOT → REPAIR → TEST → VERIFY → RE-ANALYZE → REPORT → DEPLOY


### التفصيل الرسمي لمسار المشروع القائم

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
DEPLOY


### مسار إنشاء مشروع جديد

REQUIREMENTS
   ↓
ARCHITECTURE
   ↓
PLAN
   ↓
BUILD
   ↓
TEST
   ↓
VERIFY
   ↓
REPORT
   ↓
DEPLOY


## 3. المبدأ المعماري

وجود المحرك لا يعني أنه تم تشغيله.

تشغيل المحرك لا يعني أنه نجح.

نجاح المحرك لا يعني أن مخرجاته صالحة للاستهلاك.

وجود التقرير لا يعني أنه حديث أو صحيح.

لذلك يجب أن يعرف P45 لكل مرحلة:
- Input
- Producer
- Execution
- Output
- Output Location
- Validation
- Consumer
- Failure State
- Evidence


## 3. المبدأ المعماري

وجود المحرك لا يعني أنه تم تشغيله.

تشغيل المحرك لا يعني أنه نجح.

نجاح المحرك لا يعني أن مخرجاته صالحة للاستهلاك.

وجود التقرير لا يعني أنه حديث أو صحيح.

لذلك يجب أن يعرف P45 لكل مرحلة:
- Input
- Producer
- Execution
- Output
- Output Location
- Validation
- Consumer
- Failure State
- Evidence


## 4. قاعدة المصدر والمالك

لكل وظيفة أو تقرير أو مرحلة في P45 يجب أن يكون هناك مصدر واضح ومالك واضح.

ONE FUNCTION
   ↓
ONE OWNER
   ↓
ONE DEFINED OUTPUT
   ↓
DEFINED CONSUMERS

إذا كان الشيء موجودًا ويعمل فلا يُعاد بناؤه.

إذا كان موجودًا لكنه منفصل عن دورة التنفيذ، يتم ربطه.

إذا كان موجودًا لكنه معيب، يتم إصلاحه.

إذا ثبت أنه غير موجود، عندها فقط يُضاف.


## 5. حالات التقارير

كل تقرير في P45 يجب أن تكون له حالة معروفة قبل أن يستهلكه أي Engine آخر.

MISSING
INVALID
STALE
VALID

### MISSING
التقرير غير موجود في المكان المتوقع.

MISSING لا تعني NO FINDINGS.

### INVALID
التقرير موجود لكنه لا يطابق البنية أو البيانات المطلوبة.

### STALE
التقرير موجود لكنه أقدم من المدخلات التي يعتمد عليها أو لا يمثل الحالة الحالية للمشروع.

### VALID
التقرير موجود، وبنيته صحيحة، ومدخلاته معروفة، وحالته قابلة للاستهلاك.

لا يجوز لأي Consumer تحويل MISSING أو INVALID أو STALE إلى نتيجة ناجحة أو إلى غياب للمشكلات.


## 6. خريطة المحركات الحالية

P45 يحتوي حاليًا على محركات ووحدات هندسية موجودة بالفعل.

| Engine / Module | الوظيفة | الحالة المعمارية |
|---|---|---|
| engine/scanner.py | اكتشاف ملفات المشروع وتصنيفها | EXISTING |
| engine/socketio.py | تحليل Socket.IO وWebRTC والأدلة المرتبطة | EXISTING |
| engine/contract_graph.py | بناء Contract Graph | EXISTING |
| engine/root_cause.py | استخراج Root Causes قابلة للتتبع | EXISTING |
| engine/planner.py | بناء خطة هندسية ومرشحي الإصلاح | EXISTING |
| engine/snapshot.py | إنشاء Snapshot والتحقق من SHA | EXISTING |
| engine/repair.py | تنفيذ إصلاحات Exact Change بصورة مضبوطة | EXISTING |
| engine/verification.py | التحقق من التغييرات | EXISTING |
| engine/execution_log.py | تسجيل مراحل التنفيذ ونتائجها | EXISTING |

### القاعدة

هذه المحركات لا تُعاد كتابتها لمجرد وجود فجوة في orchestration.

إذا كان المحرك موجودًا ويعمل، نستخدمه.

إذا كان موجودًا لكنه غير متصل، نربطه.

إذا كان موجودًا لكنه معيب، نصلحه بعد إثبات العيب.

إذا ثبت أن وظيفة مطلوبة غير موجودة، عندها فقط نضيفها.


## 7. خريطة الربط التنفيذية

المسار المعماري المستهدف:

Scanner → Scan Report → Contract Analyzer → Contracts Report → Contract Graph → Contract Graph Report → Root Cause Engine → Root Cause Report → Planner → Execution Plan → Approval → Snapshot → Repair → Test → Verification → Re-Analysis → Final Report

### قاعدة الربط

كل سهم في المسار يجب أن يكون له دليل من الكود أو من سجل التنفيذ.

وجود Engine وحده لا يثبت وجود السهم.

وجود Report وحده لا يثبت أن Producer قام بإنشائه في التنفيذ الحالي.

وجود Consumer وحده لا يثبت أن Producer متصل به.

لذلك سيتم تدقيق كل علاقة بصيغة:

PRODUCER → OUTPUT → CONSUMER → VALIDATION

وأي علاقة لا يثبتها الكود أو سجل التنفيذ تسجل كـ GAP، ولا تُعالج قبل تحديد سببها.


## 8. الواقع التنفيذي الحالي — Current Implementation Reality

هذه الخريطة تفرق صراحة بين التصميم المستهدف وبين ما يثبته الكود وسجل التنفيذ.

| العنصر | الهدف المعماري | الواقع الحالي | الدليل | الحالة |
|---|---|---|---|---|
| Scanner | اكتشاف المشروع وتصنيفه | منفذ ومربوط بالـ CLI | repair-repository.py + scan-report.json | IMPLEMENTED |
| Contract Analyzer | تحليل العقود والأدلة | منفذ ومربوط بالـ CLI | repair-repository.py + contracts-report.json | IMPLEMENTED |
| Contract Graph | بناء Contract Graph | المحرك موجود لكن غير مربوط بالـ CLI الحالي | engine/contract_graph.py + غياب contract-graph.json | DISCONNECTED |
| Root Cause Engine | استخراج Root Causes | المحرك موجود لكن غير مربوط بالـ CLI الحالي | engine/root_cause.py + غياب root-cause-report.json | DISCONNECTED |
| Planner | بناء Execution Plan | منفذ ومربوط | repair-repository.py + execution-plan.json | IMPLEMENTED |
| Approval | اعتماد الإصلاح | موجود في مسار الإصلاح المباشر/الإنتاجي | cmd_repair | IMPLEMENTED |
| Snapshot | حفظ الحالة قبل التعديل | منفذ ومثبت | engine/snapshot.py + execution-log.json | VERIFIED |
| Repair | تنفيذ Exact Change | منفذ ومختبر | engine/repair.py + execution-log.json | VERIFIED |
| Test | اختبار المشروع بعد الإصلاح | لا توجد طبقة اختبار مشروع عامة مرتبطة بالدورة | tests/ + execution flow | INCOMPLETE |
| Verification | التحقق من التغيير | منفذ ومثبت باختبارات فعلية | engine/verification.py + execution-log.json | VERIFIED |
| Re-Analysis | إعادة تحليل المشروع بعد الإصلاح | غير موجودة في cmd_full الحالي | repair-repository.py | MISSING |
| Final Report | تقرير نهائي موحد للدورة | غير موجود كمرحلة مستقلة | repair-repository.py | MISSING |
| Deploy | نشر النتيجة | خارج دورة الإصلاح الحالية | repair-repository.py | NOT_CONNECTED |

### قاعدة القراءة

لا تعني الحالة IMPLEMENTED أن المرحلة منفذة في كل دورة.

لا تعني الحالة VERIFIED أن كل النظام متحقق منه.

ولا تعني الحالة DISCONNECTED أن المحرك معيب.

المعنى الرسمي للحالات:

IMPLEMENTED = الوظيفة موجودة ومتصلة بالكود التنفيذي.

DISCONNECTED = الوظيفة موجودة لكن لا يثبت اتصالها بالدورة الحالية.

INCOMPLETE = الوظيفة موجودة جزئيًا أو تفتقد جزءًا مطلوبًا من العقد المعماري.

MISSING = المرحلة المطلوبة معماريًا غير موجودة في التنفيذ الحالي.

VERIFIED = توجد أدلة تنفيذية مباشرة تثبت نجاح الوظيفة المحددة، وليس النظام بالكامل.

NOT_CONNECTED = الوظيفة قد تكون موجودة خارج الدورة الحالية، لكن لا يوجد ربط تنفيذي مثبت بها.

### القاعدة الحاكمة

ARCHITECTURE TARGET ≠ IMPLEMENTED

IMPLEMENTED ≠ CONNECTED

CONNECTED ≠ EXECUTED

EXECUTED ≠ VERIFIED

VERIFIED ≠ SYSTEM VERIFIED

ولا يجوز لـ P45 الانتقال من حالة إلى أخرى دون Evidence مناسب.


## 9. سجل الفجوات الرسمي — GAP REGISTER

هذا السجل يحول الفجوات المعمارية المثبتة إلى عناصر قابلة للتتبع. لا تُعتبر الفجوة عيبًا في Engine إلا إذا أثبت الكود أو التنفيذ ذلك صراحة.

| GAP ID | العنصر | المطلوب معماريًا | الواقع المثبت | الدليل | نوع الفجوة | الأثر | الإجراء المقترح | الموافقة |
|---|---|---|---|---|---|---|---|---|
| GAP-001 | ContractGraphEngine | تنفيذ Contract Graph بعد تحليل العقود | المحرك موجود لكن لا يوجد استدعاء له في مسار CLI الحالي | repair-repository.py + engine/contract_graph.py + غياب contract-graph.json | DISCONNECTED | Planner لا يحصل على Graph حديث من الدورة الحالية | ربط المحرك بالدورة بعد تحديد عقد الإدخال والإخراج | REQUIRED |
| GAP-002 | RootCauseEngine | استخراج Root Causes من Contract Graph والأدلة | المحرك موجود لكن لا يوجد استدعاء له في مسار CLI الحالي | repair-repository.py + engine/root_cause.py + غياب root-cause-report.json | DISCONNECTED | Planner قد يعمل دون Root Cause Report حديث | ربط المحرك بعد ربط Contract Graph والتحقق من مخرجاته | REQUIRED |
| GAP-003 | Planner Evidence Gate | منع استهلاك التقارير MISSING أو INVALID أو STALE كأنها نتائج صالحة | Planner الحالي يستطيع تحميل تقرير مفقود كبيانات فارغة | engine/planner.py + reports الحالية | SAFETY GAP | قد تتحول الأدلة المفقودة إلى نتيجة بلا Root Causes | إضافة تحقق صريح من حالة التقارير قبل الاستهلاك | REQUIRED |
| GAP-004 | Project Test Layer | تنفيذ اختبارات المشروع ضمن دورة الإصلاح | لا توجد طبقة اختبارات مشروع عامة مرتبطة بـ cmd_full | tests/ + repair-repository.py | INCOMPLETE | لا يمكن إثبات Behavioral Verification بصورة عامة | تعريف Test Contract وربطه بالدورة | REQUIRED |
| GAP-005 | Re-Analysis | إعادة تحليل الحالة بعد الإصلاح ومقارنة Before/After | غير موجودة كمرحلة في cmd_full الحالي | repair-repository.py | MISSING | لا يوجد إثبات أن الإصلاح عالج السبب دون آثار جانبية معمارية | ربط مراحل التحليل وإنتاج مقارنة Before/After | REQUIRED |
| GAP-006 | Final Report | إنتاج تقرير نهائي موحد للدورة | لا توجد مرحلة Final Report مستقلة في cmd_full | repair-repository.py | MISSING | نتائج الدورة موزعة بين التقارير وسجل التنفيذ | إضافة مرحلة تقرير نهائي بعد Re-Analysis | REQUIRED |
| GAP-007 | Deploy Integration | ربط النشر بالدورة الرسمية عند اعتماد المشروع لذلك | غير متصل بدورة الإصلاح الحالية | repair-repository.py | NOT_CONNECTED | النشر ليس جزءًا مثبتًا من دورة الإصلاح الحالية | تعريف عقد نشر مستقل قبل الربط | REQUIRED |

### قواعد سجل الفجوات

1. GAP لا يعني أن الكود معيب؛ قد يعني فقط أن جزءًا موجودًا غير متصل.
2. لا تُغلق GAP إلا بدليل جديد يثبت المعالجة.
3. لا تُنفذ GAP تلقائيًا لمجرد تسجيلها.
4. كل GAP قابل للإصلاح يجب أن يحدد Target وReason وEvidence وVerification Criteria قبل التنفيذ.
5. إذا تغير الواقع التنفيذي، يجب تحديث حالة GAP بدل إنشاء GAP مكرر.
6. لا يجوز تحويل GAP إلى Repair Candidate إلا بعد اكتمال التشخيص والموافقة المطلوبة.

### دورة حياة GAP

DISCOVERED
   ↓
EVIDENCED
   ↓
ASSESSED
   ↓
PLANNED
   ↓
APPROVED
   ↓
REPAIRED
   ↓
VERIFIED
   ↓
CLOSED

ولا تنتقل GAP إلى CLOSED إلا بوجود Evidence يثبت الحالة الجديدة.


## 10. عقود المحركات — ENGINE CONTRACTS

كل Engine في P45 يجب أن يملك عقدًا واضحًا يحدد ما يدخل إليه، ومن ينتج المدخل، وما الذي ينفذه، وما الذي يخرجه، وأين يخرجه، ومن يستهلكه، وكيف يتم التحقق منه، وما حالة الفشل.

| Engine | INPUT | PRODUCER | EXECUTION | OUTPUT | LOCATION | CONSUMER | VALIDATION | FAILURE STATE |
|---|---|---|---|---|---|---|---|---|
| Scanner | Project Path | CLI / Orchestrator | ProjectScanner.scan() | Project Structure + Classification | reports/scan-report.json | Contract Analyzer / Planner | Report exists + structure valid + root matches | FAILED / MISSING |
| Contract Analyzer | Project Path | CLI / Orchestrator | SocketIOAnalyzer.analyze() | Socket.IO/WebRTC contract evidence | reports/contracts-report.json | Contract Graph / Planner | Report exists + input scope known | FAILED / EVIDENCE_LIMITED |
| ContractGraphEngine | Scan + Contract Evidence | Orchestrator | ContractGraphEngine | Contract Graph | reports/contract-graph.json | RootCauseEngine / Planner | Report exists + nodes/edges valid + source evidence known | MISSING / INVALID / STALE / FAILED |
| RootCauseEngine | Contract Graph + Source Evidence | Orchestrator | RootCauseEngine | Traceable Root Causes | reports/root-cause-report.json | Planner | Report exists + causes trace to evidence | MISSING / INVALID / STALE / FAILED |
| Planner | Scan + Contracts + Contract Graph + Root Causes | Previous analysis stages | EngineeringPlanner.diagnose_and_plan() | Diagnosis + Evidence + Repair Candidates + Execution Plan | plans/execution-plan.json | Approval / Repair | Required reports VALID and current | BLOCKED / INVALID / EVIDENCE_MISSING |
| Snapshot | Approved Repair Target | Approval / Repair | SnapshotEngine | Immutable Snapshot + SHA | snapshots/ | Repair / Verification | Snapshot SHA matches source before change | FAILED |
| Repair | Approved Exact Change | Approval | DeepRepairEngine.apply_exact_change() | Modified Target + Before/After SHA | Project Target + Execution Log | Test / Verification / Re-Analysis | Exact match + one occurrence + SHA changed | REJECTED / FAILED / NOT_APPLIED |
| Test | Repaired Project | Repair | Project Test Contract | Test Results | Execution Log / Test Report | Verification | Tests actually executed and result recorded | FAILED / NOT_EXECUTED |
| Verification | Applied Change + Expected State | Repair / Test | VerificationEngine | Exact Verification Result | Execution Log / Verification Report | Re-Analysis / Final Report | Required checks explicitly PASS | FAILED / NOT_VERIFIED |
| Re-Analysis | Current Project + Previous Analysis | Verification | Analysis Engines | Before/After Analysis | Defined Re-Analysis Report | Final Report | Current inputs + comparison evidence | MISSING / INVALID / FAILED |
| Final Report | Execution Log + Reports + Verification + Re-Analysis | Previous stages | Final Report stage | Unified Cycle Report | Defined Final Report Location | User / Audit / Deployment | All required stages and statuses reconciled | INCOMPLETE / FAILED |
| Deploy | Verified Project + Final Report | Final Report / Approval | Deployment mechanism | Deployed Project | Defined Deployment Target | User / Runtime | Deployment result independently confirmed | NOT_CONNECTED / FAILED |

### قاعدة العقد

لا يجوز لـ Consumer استهلاك Output من Engine سابق دون التحقق من:

1. وجود المخرج.
2. صحة بنيته.
3. معرفة مصدره.
4. معرفة مدخلاته.
5. حداثته بالنسبة إلى مدخلاته.
6. توافقه مع العقد المطلوب.

### قاعدة خاصة بالتقارير

MISSING ≠ NO FINDINGS

INVALID ≠ NO FINDINGS

STALE ≠ CURRENT

EVIDENCE_LIMITED ≠ PROVEN ABSENCE

ولا يجوز تحويل أي من هذه الحالات إلى نتيجة ناجحة أو إلى غياب للمشكلة.

### قاعدة الربط

إذا كان Engine موجودًا وعقده معروفًا لكن Producer أو Consumer غير مربوط به، تصنف الحالة DISCONNECTED.

إذا كان العقد نفسه غير محدد، لا يتم اختراع عقد جديد قبل فحص الكود الفعلي للمحرك ومخرجاته.

إذا ثبت أن العقد الموجود لا يطابق التنفيذ، تسجل GAP مستقلة قبل التعديل.

### قاعدة عدم التكرار

لا ينشئ Engine جديد وظيفة يؤديها Engine موجود.

ولا ينشئ Report جديد نفس المعلومات التي ينتجها Report موجود.

إذا احتاج Engine إلى معلومة موجودة، يجب أن يستهلك مصدرها الرسمي بدل إعادة تحليلها بلا سبب.
