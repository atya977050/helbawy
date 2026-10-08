from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json
import re
import html

def now():
    return datetime.now(timezone.utc).isoformat()

@dataclass
class ScreenProposal:
    screen_id: str
    title: str
    purpose: str
    variant: int
    layout: str
    components: list
    approved: bool = False

class ConversationState:

    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / '.abqaryno' / 'creation-state.json'

    def save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def load(self):
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:
            return {}

def _abqaryno_normalize_requirements(raw, idea):
    raw = raw if isinstance(raw, dict) else {}
    features = raw.get('features', [])
    capabilities = raw.get('capabilities', [])
    roles = raw.get('roles', [])
    app_types = raw.get('app_types', [])
    if not isinstance(features, list):
        features = [features] if features else []
    if not isinstance(capabilities, list):
        capabilities = [capabilities] if capabilities else []
    if not isinstance(roles, list):
        roles = [roles] if roles else []
    if not isinstance(app_types, list):
        app_types = [app_types] if app_types else []
    requirements = []
    source_items = []
    for item in features:
        source_items.append(('FUNCTIONAL', item))
    for item in capabilities:
        source_items.append(('CAPABILITY', item))
    for index, (category, item) in enumerate(source_items, start=1):
        text = str(item).strip()
        if not text:
            continue
        requirements.append({'requirement_id': f'REQ-{index:04d}', 'text': text, 'source': 'idea_analysis', 'category': category, 'priority': 'HIGH', 'acceptance_criteria': [f'يجب أن تكون الوظيفة الخاصة بـ: {text} محددة وقابلة للاختبار.'], 'approval': 'PENDING'})
    return {'idea': str(idea).strip(), 'requirements': requirements, 'features': features, 'capabilities': capabilities, 'roles': roles, 'app_types': app_types, 'approval': {'status': 'PENDING', 'approved_count': 0, 'rejected_count': 0, 'pending_count': len(requirements)}, 'phase': 'PHASE_2', 'contract_version': 2}

def _abqaryno_validate_requirements(data):
    if not isinstance(data, dict):
        return (False, ['requirements_not_dict'])
    errors = []
    if not str(data.get('idea', '')).strip():
        errors.append('idea_missing')
    requirements = data.get('requirements', [])
    if not isinstance(requirements, list):
        errors.append('requirements_not_list')
        return (False, errors)
    ids = set()
    for item in requirements:
        if not isinstance(item, dict):
            errors.append('requirement_not_object')
            continue
        rid = str(item.get('requirement_id', '')).strip()
        text = str(item.get('text', '')).strip()
        criteria = item.get('acceptance_criteria', [])
        approval = item.get('approval')
        if not rid:
            errors.append('requirement_id_missing')
        elif rid in ids:
            errors.append(f'duplicate_requirement_id:{rid}')
        ids.add(rid)
        if not text:
            errors.append(f'text_missing:{rid}')
        if not isinstance(criteria, list) or not criteria:
            errors.append(f'acceptance_criteria_missing:{rid}')
        if approval not in {'PENDING', 'APPROVED', 'REJECTED', 'EDIT_REQUIRED'}:
            errors.append(f'invalid_approval:{rid}')
    return (not errors, errors)

class ScreenPlanningEngine:
    """
    محرك تخطيط واختيار الشاشات.

    المعرفة بالشاشات والقواعد تبقى في النظام،
    وهذا المحرك مسؤول عن اختيار ما يناسب المشروع الحالي.
    """

    def plan(self, domain, domain_screen_rules, capabilities, roles, text):
        selected_ids = set()

        for sid, title, purpose in domain_screen_rules.get(domain, []):
            selected_ids.add(sid)

        if 'scheduling' in capabilities:
            selected_ids.add('sessions')

        if 'reports' in capabilities and (
            'dashboard' in capabilities or 'admin' in roles
        ):
            selected_ids.add('reports')

        if 'users' in capabilities and any(
            role in roles for role in ('admin', 'owner', 'staff', 'employee')
        ):
            selected_ids.add('users')

        if 'chat' in capabilities and domain not in {'legal', 'support'}:
            if 'support' in roles:
                selected_ids.add('support')

        if 'dashboard' in capabilities:
            selected_ids.add('dashboard')

        explicit_screen_rules = [
            ('service_selection', ['شاشة اختيار الخدمة', 'اختيار الخدمة']),
            ('client_dashboard', ['لوحة العميل']),
            ('management_dashboard',
             ['لوحة المحامي والإدارة', 'لوحة المحامي', 'لوحة الإدارة']),
        ]

        for screen_id, phrases in explicit_screen_rules:
            if any(phrase.lower() in text for phrase in phrases):
                selected_ids.add(screen_id)

        return selected_ids


class RequirementsEngine:

    def analyze(self, idea):
        """
        تحليل دلالي أولي لفكرة المستخدم.

        القاعدة الأساسية:
        الشاشة = وحدة تجربة مستقلة اختارها المستخدم.
        الوظيفة = قدرة داخل الشاشة وليست شاشة مستقلة تلقائياً.
        """
        idea = idea.strip()
        text = idea.lower()
        # تحليل القدرات أولاً؛ الشاشات تُقترح من طبيعة الفكرة نفسها.
        capability_engine = CapabilityEngine()
        capability_data = capability_engine.analyze(idea)
        capabilities = set(capability_data.get('capabilities', []))
        domains = set(capability_data.get('app_types', []))
        roles = capability_data.get('roles', ['user'])

        domain_screen_rules = {
            'software_engineering': [
                ('brain', 'العقل المركزي',
                 'فهم المشروع وتحليل المتطلبات واتخاذ القرارات وتنسيق دورة العمل'),
                ('creation', 'إنشاء البرامج',
                 'إنشاء المشاريع والانتقال من الفكرة إلى التخطيط والبناء والتحقق'),
                ('maintenance', 'صيانة البرامج',
                 'فحص المشاريع القائمة واكتشاف العيوب وإصلاحها واختبارها'),
                ('projects', 'المشاريع',
                 'إدارة المشاريع ومساحات العمل وحالة كل مشروع ودورة حياته'),
                ('research', 'البحث والمعرفة',
                 'البحث التقني وتجميع المعرفة والأدلة وربطها بالمشروع'),
                ('execution', 'التنفيذ والاختبارات',
                 'تنفيذ الخطط وتشغيل الأدوات والاختبارات والتحقق من النتائج'),
                ('memory', 'الذاكرة والمعرفة الخاصة بالمشروع',
                 'حفظ قرارات المشروع وسياقه ونتائج العمليات والمعرفة المتراكمة'),
            ],
            'legal': [
                ('service_selection', 'الخدمات والاستشارات',
                 'اختيار نوع الخدمة وبدء التجربة المناسبة'),
                ('consultations', 'الاستشارات',
                 'إدارة الاستشارات والمحادثات القانونية'),
                ('cases', 'القضايا والسجلات',
                 'إدارة القضايا والسجلات القانونية'),
            ],
            'education': [
                ('students', 'الطلاب',
                 'إدارة بيانات الطلاب والسجلات التعليمية'),
                ('teachers', 'المدرسون',
                 'إدارة بيانات المدرسين والمدرسات'),
                ('classes', 'الفصول',
                 'إدارة الفصول والمجموعات الدراسية'),
                ('attendance', 'الحضور والغياب',
                 'تسجيل ومتابعة حضور الطلاب وغيابهم'),
                ('grades', 'الدرجات والتقييم',
                 'إدارة درجات الطلاب ونتائجهم'),
                ('courses', 'الدورات والمحتوى',
                 'إدارة الدورات والمحتوى التعليمي'),
            ],
            'commerce': [
                ('products', 'المنتجات',
                 'إدارة المنتجات والعناصر المعروضة'),
            ],
            'booking': [
                ('sessions', 'المواعيد والحجوزات',
                 'إدارة المواعيد والجلسات والحجوزات'),
            ],
            'finance': [
                ('finance_records', 'السجلات المالية',
                 'إدارة البيانات والحركات المالية'),
            ],
            'crm': [
                ('clients', 'المستخدمون والعملاء',
                 'إدارة بيانات العملاء والمستفيدين'),
            ],
            'project_management': [
                ('projects', 'المشروعات والمهام',
                 'إدارة المشروعات والمهام المرتبطة بها'),
            ],
            'support': [
                ('support', 'طلبات الدعم',
                 'إدارة طلبات الدعم والتواصل مع المستخدمين'),
            ],
            'logistics': [
                ('orders', 'الطلبات والتوصيل',
                 'إدارة الطلبات وعمليات التوصيل'),
            ],
        }


        screens = [{
            'id': 'home',
            'title': 'الشاشة الرئيسية',
            'purpose': 'البوابة الرئيسية للبرنامج والتنقل بين الوظائف الأساسية',
            'selection_required': True,
            'source': 'analysis',
            'features': ['عرض الوظائف الأساسية والتنقل بينها']
        }]

        # تخطيط واختيار الشاشات مسؤولية مستقلة.
        domain = next(iter(capability_data.get('app_types', [])), 'general')

        selected_ids = ScreenPlanningEngine().plan(
            domain=domain,
            domain_screen_rules=domain_screen_rules,
            capabilities=capabilities,
            roles=roles,
            text=text,
        )

        # شاشة رئيسية واحدة فقط كبوابة عامة.
        screens = [{
            'id': 'home',
            'title': 'الشاشة الرئيسية',
            'purpose': 'البوابة الرئيسية للبرنامج والتنقل بين الوظائف الأساسية',
            'selection_required': True,
            'source': 'analysis',
            'features': ['عرض الوظائف الأساسية والتنقل بينها']
        }]

        generated_specs = {
            'brain': (
                'العقل المركزي',
                'فهم المشروع وتحليل المتطلبات واتخاذ القرارات وتنسيق دورة العمل',
            ),
            'creation': (
                'إنشاء البرامج',
                'إنشاء المشاريع والانتقال من الفكرة إلى التخطيط والبناء والتحقق',
            ),
            'maintenance': (
                'صيانة البرامج',
                'فحص المشاريع القائمة واكتشاف العيوب وإصلاحها واختبارها',
            ),
            'projects': (
                'المشاريع',
                'إدارة المشاريع ومساحات العمل وحالة كل مشروع ودورة حياته',
            ),
            'research': (
                'البحث والمعرفة',
                'البحث التقني وتجميع المعرفة والأدلة وربطها بالمشروع',
            ),
            'execution': (
                'التنفيذ والاختبارات',
                'تنفيذ الخطط وتشغيل الأدوات والاختبارات والتحقق من النتائج',
            ),
            'memory': (
                'الذاكرة والمعرفة الخاصة بالمشروع',
                'حفظ قرارات المشروع وسياقه ونتائج العمليات والمعرفة المتراكمة',
            ),
            'service_selection': (
                'اختيار الخدمة',
                'اختيار الخدمة أو العملية التي يريد المستخدم تنفيذها',
            ),
            'consultations': (
                'الاستشارات',
                'إدارة الاستشارات والمحادثات المرتبطة بها',
            ),
            'cases': (
                'القضايا والسجلات',
                'إدارة القضايا والسجلات الأساسية',
            ),
            'students': (
                'الطلاب',
                'إدارة بيانات الطلاب والسجلات التعليمية',
            ),
            'teachers': (
                'المدرسون',
                'إدارة بيانات المدرسين والمدرسات',
            ),
            'classes': (
                'الفصول',
                'إدارة الفصول والمجموعات الدراسية',
            ),
            'attendance': (
                'الحضور والغياب',
                'تسجيل ومتابعة حضور الطلاب وغيابهم',
            ),
            'grades': (
                'الدرجات والتقييم',
                'إدارة درجات الطلاب ونتائجهم',
            ),
            'courses': (
                'الدورات والمحتوى',
                'إدارة الدورات والمحتوى التعليمي',
            ),
            'products': (
                'المنتجات',
                'إدارة المنتجات والعناصر المعروضة',
            ),
            'sessions': (
                'المواعيد والجلسات',
                'إدارة المواعيد والجلسات والحجوزات',
            ),
            'finance_records': (
                'السجلات المالية',
                'إدارة البيانات والحركات المالية',
            ),
            'clients': (
                'المستخدمون والعملاء',
                'إدارة بيانات العملاء والمستفيدين',
            ),
            'projects': (
                'المشروعات والمهام',
                'إدارة المشروعات والمهام',
            ),
            'support': (
                'طلبات الدعم',
                'إدارة طلبات الدعم والتواصل مع المستخدمين',
            ),
            'orders': (
                'الطلبات والتوصيل',
                'إدارة الطلبات وعمليات التوصيل',
            ),
            'reports': (
                'التقارير',
                'عرض وإنشاء التقارير والنتائج',
            ),
            'users': (
                'المستخدمون',
                'إدارة المستخدمين والحسابات والصلاحيات',
            ),
            'dashboard': (
                'لوحة التحكم',
                'عرض ملخص البيانات والإحصائيات وأهم العمليات',
            ),
            'client_dashboard': (
                'لوحة العميل',
                'عرض بيانات المستخدم وخدماته وعملياته الأساسية',
            ),
            'management_dashboard': (
                'لوحة الإدارة',
                'إدارة العمليات والمستخدمين والبيانات الرئيسية',
            ),
        }

        for screen_id in selected_ids:
            spec = generated_specs.get(screen_id)
            if not spec:
                continue
            title, purpose = spec
            screens.append({
                'id': screen_id,
                'title': title,
                'purpose': purpose,
                'selection_required': True,
                'source': 'analysis',
                'features': [purpose]
            })

        features = []
        feature_labels = {
            'auth': 'تسجيل الدخول والحسابات',
            'users': 'إدارة المستخدمين',
            'roles': 'الأدوار والصلاحيات',
            'database': 'قاعدة البيانات وحفظ السجلات',
            'crud': 'إدارة السجلات',
            'chat': 'المحادثات والرسائل',
            'files': 'الملفات والمرفقات',
            'camera': 'الكاميرا والفيديو',
            'microphone': 'الصوت والتسجيل',
            'webrtc': 'الاتصال المباشر',
            'notifications': 'الإشعارات',
            'reports': 'التقارير',
            'export': 'التصدير',
            'print': 'الطباعة',
            'scheduling': 'المواعيد والحجوزات',
            'payments': 'المدفوعات والفواتير',
            'location': 'الموقع والخرائط',
            'settings': 'الإعدادات',
            'audit': 'سجل العمليات',
            'translation': 'الترجمة',
            'document_processing': 'معالجة المستندات',
            'ocr': 'التعرف على النصوص من الصور والمستندات',
            'speech_to_text': 'تحويل الصوت إلى نص',
            'text_to_speech': 'تحويل النص إلى صوت',
        }
        for capability in capability_data.get('capabilities', []):
            label = feature_labels.get(capability)
            if label:
                features.append(label)

        # الوظائف المذكورة صراحةً في الفكرة تُحفظ كخصائص داخل الشاشات،
        # وليست شاشات مستقلة.
        explicit_features = {
            'إرفاق': 'إرفاق الملفات',
            'مرفق': 'إرفاق الملفات',
            'فيديو': 'الفيديو',
            'صوت': 'الصوت والتسجيل',
            'نسخ': 'النسخ',
            'طباعة': 'الطباعة',
            'تصدير': 'التصدير',
        }
        for token, label in explicit_features.items():
            if token in text:
                features.append(label)

        features = list(dict.fromkeys(features))

        screen_selection = {
            'mode': 'USER_SELECTS',
            'selection_required': True,
            'user_may_reject': True,
            'only_selected_screens_enter_plan': True,
            'only_approved_designs_are_generated': True
        }

        capability_engine = CapabilityEngine()
        capability_data = capability_engine.analyze(idea)
        features = list(dict.fromkeys(features))

        # عقود API مشتقة من الشاشات والوظائف التي طلبها المستخدم.
        # لا نضيف API لمجرد وجود capability عامة؛ كل عقد هنا مرتبط
        # بوظيفة فعلية يحتاجها البرنامج الناتج.
        screen_ids = {
            str(screen.get('id', '')).strip().lower()
            for screen in screens
            if isinstance(screen, dict)
        }
        capability_set = set(capability_data.get('capabilities', []))

        api = [
            {
                'method': 'GET',
                'path': '/api/health',
                'purpose': 'فحص جاهزية البرنامج وواجهة API',
            }
        ]

        if 'users' in capability_set or 'auth' in capability_set:
            api.append({
                'method': 'POST',
                'path': '/api/users',
                'purpose': 'إنشاء مستخدم مرتبط بالاستشارة',
            })

        consultation_screens = {
            'free_consultation',
            'private_consultation',
        }

        if screen_ids & consultation_screens:
            api.extend([
                {
                    'method': 'GET',
                    'path': '/api/consultations',
                    'purpose': 'عرض الاستشارات الخاصة بالمستخدم',
                },
                {
                    'method': 'POST',
                    'path': '/api/consultations',
                    'purpose': 'فتح استشارة جديدة وإنشاء محادثتها',
                },
                {
                    'method': 'GET',
                    'path': '/api/conversations',
                    'purpose': 'استرجاع محادثة الاستشارة',
                },
            ])

        if 'chat' in capability_set or any(
            screen_id in screen_ids
            for screen_id in consultation_screens
        ):
            api.extend([
                {
                    'method': 'GET',
                    'path': '/api/messages',
                    'purpose': 'استرجاع رسائل المحادثة',
                },
                {
                    'method': 'POST',
                    'path': '/api/messages',
                    'purpose': 'إرسال رسالة داخل المحادثة',
                },
            ])

        if 'files' in capability_set or any(
            token in ' '.join(features)
            for token in ('ملف', 'مرفق', 'إرفاق')
        ):
            api.extend([
                {
                    'method': 'GET',
                    'path': '/api/documents',
                    'purpose': 'عرض الملفات المرفقة بالمحادثة',
                },
                {
                    'method': 'POST',
                    'path': '/api/documents',
                    'purpose': 'رفع ملف وربطه بالمحادثة',
                },
            ])

        # منع التكرار مع الحفاظ على ترتيب العقود.
        unique_api = []
        seen_api = set()
        for contract in api:
            key = (
                contract.get('method'),
                contract.get('path'),
            )
            if key not in seen_api:
                seen_api.add(key)
                unique_api.append(contract)

        # نموذج المشروع مستقل عن الشاشات.
        # الشاشات نتيجة من نتائج التخطيط وليست تعريفاً للمشروع.
        project_type = (
            capability_data['app_types'][0]
            if capability_data.get('app_types')
            else 'general'
        )

        # تحويل نتائج التحليل إلى نموذج هندسي منظم.
        # لا نحذف المعرفة العامة؛ نحدد فقط ما ينطبق على المشروع الحالي.
        structured_requirements = [
            {
                'id': f'req_{i + 1}',
                'type': 'capability',
                'capability': feature,
                'description': feature_labels.get(feature, feature),
                'source': 'analysis',
            }
            for i, feature in enumerate(capability_data.get('capabilities', []))
        ]

        # المتطلبات الهندسية لا تُستنتج من الشاشات.
        # عند اكتشاف مشروع هندسة برمجيات، يحدد العقل المركزي
        # المتطلبات الأساسية لدورة حياة البرنامج نفسها.
        engineering_requirement_catalog = [
            (
                'understanding',
                'الفهم والتحليل',
                'فهم فكرة المشروع وسياقه وحدوده وأهدافه قبل اتخاذ قرارات التنفيذ.',
            ),
            (
                'research',
                'البحث والأدلة',
                'إجراء البحث التقني عند الحاجة وتسجيل المصادر والأدلة المستخدمة في القرارات.',
            ),
            (
                'requirements',
                'هندسة المتطلبات',
                'تحويل الفكرة إلى متطلبات واضحة قابلة للتتبع والاختبار والمراجعة.',
            ),
            (
                'blueprint',
                'المخطط الهندسي',
                'إنشاء Blueprint يربط المتطلبات بالمكونات والوحدات والتدفقات والاعتماديات.',
            ),
            (
                'architecture',
                'الهندسة المعمارية',
                'تحديد المعمارية والتقنيات والحدود بين الطبقات والخدمات قبل البناء.',
            ),
            (
                'database',
                'هندسة البيانات',
                'تحديد الكيانات والمخططات والعلاقات والعقود الخاصة بالبيانات.',
            ),
            (
                'backend',
                'الخلفية البرمجية',
                'تحديد الخدمات وواجهات API والمنطق التشغيلي والتحقق من المدخلات.',
            ),
            (
                'frontend',
                'الواجهة والتجربة',
                'تحديد الواجهات والتدفقات والمكونات وربطها بالوظائف الفعلية.',
            ),
            (
                'security',
                'الأمن',
                'تحديد المصادقة والتفويض وحماية البيانات والتحقق من العمليات الحساسة.',
            ),
            (
                'integration',
                'التكامل',
                'ربط المكونات والخدمات والواجهات وقاعدة البيانات دون عقود متعارضة.',
            ),
            (
                'build',
                'البناء',
                'إنشاء ملفات المشروع الفعلية وتجميع المكونات وفق الخطة المعتمدة.',
            ),
            (
                'runtime',
                'التشغيل',
                'تشغيل المشروع فعليًا والتحقق من أن المكونات الأساسية تعمل في بيئتها المستهدفة.',
            ),
            (
                'testing',
                'الاختبارات',
                'تنفيذ اختبارات syntax وunit وintegration وAPI وruntime وregression حسب الحاجة.',
            ),
            (
                'verification',
                'التحقق بالأدلة',
                'عدم اعتبار التنفيذ ناجحًا إلا بوجود أدلة تشغيل واختبار ونتائج قابلة للتتبع.',
            ),
            (
                'repair',
                'الإصلاح',
                'عند وجود عيب، تحديد السبب والأثر ثم تنفيذ إصلاح محدود وقابل للرجوع واختباره.',
            ),
            (
                'regression',
                'اختبار الانحدار',
                'إعادة اختبار الوظائف المتأثرة بعد التغيير أو الإصلاح.',
            ),
            (
                'versioning',
                'الإصدارات والرجوع',
                'حفظ حالة التغيير وسببه ونتائجه وإتاحة الرجوع عند فشل التغيير.',
            ),
            (
                'deployment',
                'النشر',
                'إدارة البناء والنشر وفحص الصحة والتحقق من النسخة المنشورة.',
            ),
            (
                'continuous_development',
                'التطوير المستمر',
                'استقبال التغييرات اللاحقة مع تحليل الأثر وإعادة التخطيط والاختبار.',
            ),
            (
                'memory',
                'ذاكرة المشروع',
                'حفظ سياق المشروع والقرارات ونتائج التنفيذ والمعرفة الخاصة بالمشروع.',
            ),
            (
                'observability',
                'التتبع والمراقبة',
                'تتبع التنفيذ باستخدام Execution ID وCorrelation ID وProject ID وIntent ID وEngine ID وBatch ID.',
            ),
            (
                'human_approval',
                'الموافقة البشرية',
                'طلب موافقة المستخدم قبل العمليات الحساسة أو غير القابلة للعكس.',
            ),
            (
                'ai_provider',
                'طبقة مزودي الذكاء الاصطناعي',
                'استخدام طبقة موحدة لمزودي الذكاء الاصطناعي مع فصل المزود عن منطق النظام.',
            ),
        ]

        if project_type == 'software_engineering':
            existing_ids = {
                item.get('id')
                for item in structured_requirements
                if isinstance(item, dict)
            }

            next_requirement_number = len(structured_requirements) + 1

            for requirement_id, title, description in engineering_requirement_catalog:
                if requirement_id in existing_ids:
                    continue

                structured_requirements.append({
                    'id': f'req_{next_requirement_number}',
                    'type': 'engineering',
                    'engineering_area': requirement_id,
                    'title': title,
                    'description': description,
                    'priority': 'HIGH',
                    'source': 'software_engineering_analysis',
                    'acceptance_criteria': [
                        f'يجب أن تكون مرحلة {title} محددة وقابلة للتنفيذ والتحقق.',
                        'يجب أن تكون نتائج المرحلة قابلة للتتبع داخل نموذج المشروع.',
                    ],
                })

                next_requirement_number += 1

        module_catalog = {
            'auth': 'المصادقة والحسابات',
            'users': 'إدارة المستخدمين',
            'roles': 'الأدوار والصلاحيات',
            'database': 'إدارة البيانات وقاعدة البيانات',
            'crud': 'عمليات البيانات الأساسية',
            'search': 'البحث والتصفية',
            'dashboard': 'لوحات المعلومات',
            'chat': 'المحادثات والرسائل',
            'files': 'الملفات والمرفقات',
            'camera': 'الكاميرا والفيديو',
            'microphone': 'الصوت والميكروفون',
            'webrtc': 'الاتصال المباشر',
            'notifications': 'الإشعارات',
            'reports': 'التقارير',
            'export': 'التصدير',
            'print': 'الطباعة',
            'scheduling': 'المواعيد والحجوزات',
            'payments': 'المدفوعات والفواتير',
            'location': 'الموقع والخرائط',
            'audit': 'سجل العمليات',
            'translation': 'الترجمة',
            'document_processing': 'معالجة المستندات',
            'ocr': 'التعرف الضوئي على النصوص',
            'speech_to_text': 'تحويل الصوت إلى نص',
            'text_to_speech': 'تحويل النص إلى صوت',
        }

        if project_type == 'software_engineering':
            engineering_requirements = [
                item for item in structured_requirements
                if item.get('type') == 'engineering'
            ]

            modules = [
                {
                    'id': item['engineering_area'],
                    'name': item['title'],
                    'description': item['description'],
                    'requirements': [item['id']],
                    'capabilities': [],
                    'source': 'engineering_requirement',
                }
                for item in engineering_requirements
            ]

            workflow_steps = [
                requirement_id
                for requirement_id, _title, _description
                in engineering_requirement_catalog
            ]

            workflows = [{
                'id': 'software_engineering_lifecycle',
                'name': 'دورة حياة هندسة البرمجيات',
                'steps': workflow_steps,
                'source': 'engineering_requirement_catalog',
            }]

            dependencies = []

            for index in range(len(workflow_steps) - 1):
                source = workflow_steps[index]
                target = workflow_steps[index + 1]

                dependencies.append({
                    'from': source,
                    'to': target,
                    'reason': 'المرحلة التالية تعتمد على مخرجات المرحلة السابقة',
                    'source': 'engineering_lifecycle_rule',
                })

            engineering_dependency_rules = [
                (
                    'research',
                    'requirements',
                    'المتطلبات تعتمد على البحث والأدلة عند الحاجة'
                ),
                (
                    'requirements',
                    'blueprint',
                    'المخطط الهندسي يعتمد على المتطلبات'
                ),
                (
                    'blueprint',
                    'architecture',
                    'الهندسة المعمارية تعتمد على المخطط الهندسي'
                ),
                (
                    'architecture',
                    'database',
                    'هندسة البيانات تعتمد على قرارات المعمارية'
                ),
                (
                    'architecture',
                    'backend',
                    'الخلفية البرمجية تعتمد على المعمارية'
                ),
                (
                    'architecture',
                    'frontend',
                    'الواجهة تعتمد على المعمارية'
                ),
                (
                    'security',
                    'integration',
                    'التكامل يجب أن يلتزم بمتطلبات الأمن'
                ),
                (
                    'build',
                    'runtime',
                    'التشغيل يعتمد على مخرجات البناء'
                ),
                (
                    'testing',
                    'verification',
                    'التحقق يعتمد على نتائج الاختبارات'
                ),
                (
                    'repair',
                    'regression',
                    'الإصلاح يتطلب اختبار الانحدار'
                ),
                (
                    'versioning',
                    'deployment',
                    'النشر يرتبط بنسخة قابلة للتتبع'
                ),
                (
                    'memory',
                    'observability',
                    'المراقبة تغذي ذاكرة التنفيذ بالأدلة'
                ),
                (
                    'human_approval',
                    'deployment',
                    'العمليات الحساسة قد تتطلب موافقة بشرية'
                ),
                (
                    'ai_provider',
                    'research',
                    'مزود الذكاء الاصطناعي يستخدم ضمن البحث عند الحاجة'
                ),
            ]

            known_engineering = set(workflow_steps)

            for source, target, reason in engineering_dependency_rules:
                if source not in known_engineering:
                    continue
                if target not in known_engineering:
                    continue

                if any(
                    item['from'] == source and item['to'] == target
                    for item in dependencies
                ):
                    continue

                dependencies.append({
                    'from': source,
                    'to': target,
                    'reason': reason,
                    'source': 'engineering_dependency_rule',
                })

        else:
            modules = [
                {
                    'id': capability,
                    'name': module_catalog.get(capability, capability),
                    'capabilities': [capability],
                    'source': 'capability_analysis',
                }
                for capability in capability_data.get('capabilities', [])
                if capability in module_catalog
            ]

            workflow_steps = [
                'understanding',
                'requirements',
                'research',
                'analysis',
                'planning',
                'execution',
                'testing',
                'verification',
            ]

            workflows = [{
                'id': 'primary_lifecycle',
                'name': 'دورة حياة المشروع',
                'steps': workflow_steps,
                'source': 'project_type',
            }]

            dependencies = []

            dependency_rules = [
                ('roles', 'auth', 'الصلاحيات تعتمد على المصادقة'),
                ('users', 'roles', 'إدارة المستخدمين تحتاج نظام الأدوار'),
                ('crud', 'database', 'عمليات CRUD تعتمد على قاعدة البيانات'),
                ('search', 'database', 'البحث يعتمد على البيانات'),
                ('reports', 'database', 'التقارير تعتمد على البيانات'),
                ('export', 'reports', 'التصدير يعتمد على بيانات التقارير'),
                ('audit', 'auth', 'سجل العمليات يحتاج هوية المستخدم'),
                ('chat', 'users', 'المحادثات تحتاج هوية المستخدمين'),
                ('files', 'users', 'الملفات تحتاج ربطاً بالمستخدمين'),
                ('webrtc', 'auth', 'الاتصال المباشر يحتاج هوية وصلاحيات'),
                ('camera', 'webrtc', 'الفيديو يعتمد على الاتصال المباشر'),
                ('microphone', 'webrtc', 'الصوت يعتمد على الاتصال المباشر'),
                ('scheduling', 'users', 'المواعيد تحتاج مستخدمين'),
                ('payments', 'users', 'المدفوعات تحتاج هوية المستخدم'),
            ]

            active_capabilities = set(
                capability_data.get('capabilities', [])
            )

            for source, target, reason in dependency_rules:
                if source in active_capabilities and target in active_capabilities:
                    dependencies.append({
                        'from': source,
                        'to': target,
                        'reason': reason,
                        'source': 'dependency_rule',
                    })

        project_model = {
            'project_type': project_type,
            'project_types': list(capability_data.get('app_types', [])),
            'capabilities': list(capability_data.get('capabilities', [])),
            'roles': list(capability_data.get('roles', [])),
            'requirements': structured_requirements,
            'modules': modules,
            'workflows': workflows,
            'dependencies': dependencies,
            'engines': [],
            'security': {
                'authentication': 'auth' in capabilities,
                'authorization': 'roles' in capabilities,
                'audit': 'audit' in capabilities,
            },
            'testing': {
                'required': True,
                'levels': [
                    'syntax',
                    'unit',
                    'integration',
                    'regression',
                ],
            },
            'verification': {
                'required': True,
                'evidence_based': True,
            },
            'memory': {
                'project': True,
                'decision': True,
                'execution': True,
            },
            'research': {
                'required': True,
                'evidence_based': True,
            },
            'deployment': {
                'required': True,
            },
            'observability': {
                'execution_id': True,
                'correlation_id': True,
                'project_id': True,
                'intent_id': True,
                'engine_id': True,
                'batch_id': True,
            },
        }

        # هندسة البرمجيات تحتاج دورة محركات كاملة،
        # بينما اختيار الشاشات يظل من اختصاص ScreenPlanningEngine.
        if project_type == 'software_engineering':
            project_model['engines'] = [
                'blueprint',
                'requirements',
                'research',
                'architecture',
                'database',
                'backend',
                'frontend',
                'authentication',
                'authorization',
                'application_assembly',
                'runtime',
                'testing',
                'repair',
                'versioning',
                'deployment',
                'documentation',
                'integration',
            ]

        return {
            'idea': idea,
            'created_at': now(),
            'project_model': project_model,
            'screens': screens,
            'features': features,
            'screen_selection': screen_selection,
            'app_types': capability_data['app_types'],
            'roles': capability_data['roles'],
            'capabilities': capability_data['capabilities'],
            'capability_labels': capability_data['capability_labels'],
            'api': unique_api,
        }

class CapabilityEngine:
    """
    محرك عام لفهم قدرات البرنامج المطلوبة من وصف المستخدم.
    لا يغيّر واجهة عبقرينو؛ يضيف فقط بيانات منظمة للمولد.
    """
    CAPABILITIES = {'auth': 'تسجيل الدخول والحسابات', 'users': 'إدارة المستخدمين', 'roles': 'الأدوار والصلاحيات', 'database': 'قاعدة البيانات وحفظ السجلات', 'crud': 'الإضافة والتعديل والحذف والعرض', 'search': 'البحث والتصفية', 'dashboard': 'لوحة التحكم والإحصائيات', 'chat': 'المحادثات والرسائل', 'files': 'الملفات والمرفقات', 'camera': 'الكاميرا والفيديو', 'microphone': 'الميكروفون والصوت', 'webrtc': 'الاتصال المباشر WebRTC', 'notifications': 'الإشعارات والتنبيهات', 'reports': 'التقارير', 'export': 'التصدير', 'print': 'الطباعة', 'scheduling': 'المواعيد والحجوزات', 'payments': 'المدفوعات والفواتير', 'location': 'الموقع والخرائط', 'settings': 'الإعدادات', 'audit': 'سجل العمليات', 'translation': 'ترجمة المستندات والنصوص بين اللغات', 'document_processing': 'معالجة المستندات واستخراج النصوص', 'ocr': 'التعرف الضوئي على النصوص من الصور والمستندات الممسوحة', 'speech_to_text': 'تحويل الصوت إلى نص', 'text_to_speech': 'تحويل النص إلى صوت'}
    ROLE_WORDS = {'admin': ['مدير', 'مشرف', 'ادمن', 'admin', 'administrator'], 'owner': ['صاحب الشركة', 'صاحب المشروع', 'مالك', 'owner'], 'employee': ['موظف', 'عامل', 'employee', 'staff'], 'lawyer': ['محامي', 'محامية', 'lawyer'], 'client': ['موكل', 'موكلة'], 'student': ['طالب', 'طالبة', 'student'], 'teacher': ['مدرس', 'مدرسة', 'معلم', 'معلمة', 'teacher'], 'customer': ['زبون', 'مشتري', 'customer'], 'doctor': ['طبيب', 'طبيبة', 'doctor'], 'patient': ['مريض', 'مريضة', 'patient'], 'driver': ['سائق', 'driver'], 'support': ['دعم', 'موظف دعم', 'support']}
    DOMAIN_RULES = [('legal', ['محام', 'قانون', 'قضية', 'محكمة', 'مكتب محاماة']), ('commerce', ['متجر', 'بيع', 'مبيعات', 'منتج', 'مخزن', 'مخزون']), ('education', ['تعليم', 'مدرس', 'طلاب', 'دورة', 'مدرسة', 'جامعة']), ('media', ['بث', 'بث مباشر', 'لايف', 'stream', 'live']), ('booking', ['حجز', 'حجوزات', 'موعد', 'مواعيد', 'reservation', 'booking']), ('finance', ['مصروف', 'مصروفات', 'حسابات', 'فاتورة', 'فواتير', 'مالية']), ('crm', ['عملاء', 'موكلين', 'crm', 'علاقات العملاء']), ('project_management', ['مشروع', 'مهام', 'فريق', 'إدارة مشاريع']), ('support', ['دعم فني', 'تذاكر', 'helpdesk', 'support']), ('logistics', ['توصيل', 'شحن', 'مندوب', 'سائق', 'طلبات'])]

    @staticmethod
    def _has(text, words):
        for word in words:
            word = word.lower()
            if re.search('[a-z]', word):
                if re.search('(?<![a-z0-9_])' + re.escape(word) + '(?![a-z0-9_])', text):
                    return True
            elif word in text:
                return True
        return False

    def analyze(self, idea):
        text = idea.strip().lower()
        capabilities = {'database', 'crud', 'settings'}
        roles = []
        domains = []
        for role, words in self.ROLE_WORDS.items():
            if self._has(text, words):
                roles.append(role)
        consultant_words = ['مستشار', 'المستشار', 'استشاري', 'الاستشاري', 'consultant', 'advisor']
        if self._has(text, consultant_words):
            roles.append('consultant')
        if 'consultant' in roles and 'user' not in roles:
            roles.insert(0, 'user')
        # اكتشاف مجال البرنامج يجب أن يعتمد على هوية الفكرة،
        # وليس على كلمة عابرة داخل قائمة متطلبات طويلة.
        domain_priority = [
            ('software_engineering', [
                'العقل المركزي',
                'إنشاء وصيانة البرامج',
                'إنشاء البرامج',
                'صيانة البرامج',
                'هندسة البرمجيات',
                'منصة هندسة البرمجيات',
                'منصة هندسة برمجيات',
                'هندسة برمجيات',
                'هندسة البرامج',
                'تطوير البرامج',
                'تطوير البرمجيات',
                'software engineering',
                'software development',
                'developer platform',
                'program creation',
                'code repair',
                'code generation',
            ]),
            ('legal', ['محام', 'قانون', 'قضية', 'محكمة', 'مكتب محاماة', 'استشارة قانونية', 'استشارات قانونية']),
            ('commerce', ['متجر إلكتروني', 'متجر', 'بيع المنتجات', 'إدارة المنتجات']),
            ('education', [
                'منصة تعليمية', 'برنامج تعليمي', 'مدرسة إلكترونية',
                'منصة دورات', 'إدارة الطلاب والمدرسين',
                'إدارة مدرسة', 'برنامج إدارة مدرسة', 'مدرسة',
                'الطلاب والمدرسين'
            ]),
            ('media', ['منصة بث', 'بث مباشر', 'منصة إعلامية', 'streaming platform']),
            ('booking', ['منصة حجز', 'نظام حجوزات', 'إدارة الحجوزات']),
            ('finance', ['نظام مالي', 'برنامج محاسبي', 'إدارة مالية']),
            ('crm', ['نظام إدارة علاقات العملاء', 'منصة crm']),
            ('project_management', ['إدارة مشاريع', 'نظام إدارة المشاريع', 'منصة إدارة المشاريع']),
            ('support', ['نظام دعم فني', 'منصة دعم فني', 'helpdesk']),
            ('logistics', ['نظام توصيل', 'إدارة الشحن', 'منصة لوجستية']),
        ]

        for domain, words in domain_priority:
            if self._has(text, words):
                domains.append(domain)
        rules = {'auth': ['تسجيل دخول', 'تسجيل الدخول', 'حساب', 'حسابات', 'login', 'signin', 'sign in', 'تسجيل المستخدم'], 'users': ['مستخدم', 'مستخدمين', 'users', 'user'], 'roles': ['صلاحيات', 'دور', 'أدوار', 'role', 'roles', 'مشرف', 'مدير'], 'chat': ['شات', 'دردشة', 'محادثة', 'رسائل', 'chat', 'message', 'messages'], 'files': ['ملف', 'ملفات', 'مرفق', 'مرفقات', 'إرفاق', 'attachment', 'attachments', 'file', 'files'], 'camera': ['كاميرا', 'camera', 'فيديو', 'video'], 'microphone': ['مايك', 'ميكروفون', 'microphone', 'mic', 'صوت', 'audio', 'تسجيل صوت'], 'webrtc': ['webrtc', 'مكالمة فيديو', 'اتصال فيديو', 'اتصال مباشر', 'مكالمة صوتية'], 'notifications': ['إشعار', 'إشعارات', 'تنبيه', 'تنبيهات', 'notification', 'notifications'], 'search': ['بحث', 'ابحث', 'تصفية', 'فلترة', 'search', 'filter'], 'dashboard': ['لوحة تحكم', 'إحصائيات', 'dashboard', 'statistics', 'stats'], 'reports': ['تقرير', 'تقارير', 'report', 'reports'], 'export': ['تصدير', 'excel', 'csv', 'pdf', 'export'], 'print': ['طباعة', 'اطبع', 'print'], 'scheduling': ['حجز', 'حجوزات', 'موعد', 'مواعيد', 'جدول', 'calendar', 'booking'], 'payments': ['دفع', 'مدفوعات', 'فاتورة', 'فواتير', 'سداد', 'payment', 'payments', 'invoice'], 'location': ['موقع', 'خريطة', 'خرائط', 'موقع جغرافي', 'map', 'maps', 'location', 'gps'], 'audit': ['سجل العمليات', 'سجل النشاط', 'audit', 'activity log', 'تتبع العمليات'], 'translation': ['ترجمة', 'ترجم', 'مترجم', 'translation', 'translate', 'translations', 'multilingual'], 'document_processing': ['مستند', 'مستندات', 'وثيقة', 'وثائق', 'pdf', 'word', 'docx', 'txt', 'html', 'document', 'documents'], 'ocr': ['ocr', 'مسح ضوئي', 'صورة مستند', 'صور ممسوحة', 'مستند ممسوح', 'مستندات ممسوحة', 'استخراج النص من الصورة', 'scanned', 'scan'], 'speech_to_text': ['تحويل الصوت إلى نص', 'تفريغ صوتي', 'speech to text', 'speech-to-text', 'transcription', 'audio transcription'], 'text_to_speech': ['نطق', 'قراءة صوتية', 'تحويل النص لصوت', 'تحويل النص إلى صوت', 'text to speech', 'tts']}
        for capability, words in rules.items():
            if self._has(text, words):
                capabilities.add(capability)
        if roles:
            capabilities.update({'auth', 'users', 'roles'})
        if any((x in domains for x in ['commerce', 'finance', 'crm', 'legal', 'project_management', 'logistics'])):
            capabilities.update({'search', 'reports'})
        if 'booking' in domains:
            capabilities.update({'scheduling', 'notifications'})
        if 'media' in domains:
            capabilities.update({'camera', 'microphone', 'webrtc'})
        if 'chat' in capabilities:
            capabilities.add('notifications')
        if 'payments' in capabilities:
            capabilities.update({'audit', 'reports'})
        return {'app_types': domains or ['general'], 'roles': roles or ['user'], 'capabilities': sorted(capabilities), 'capability_labels': {key: self.CAPABILITIES[key] for key in sorted(capabilities) if key in self.CAPABILITIES}}

class ScreenIntelligenceEngine:
    SCREEN_RULES = {
        'home': {
            'layout': 'بوابة الاستشارات',
            'components': [
                'عنوان البرنامج',
                'رسالة ترحيبية',
                'بطاقة الاستشارة المجانية',
                'بطاقة الاستشارة الخاصة',
                'شريط التنقل'
            ],
            'fields': [],
            'actions': [
                'فتح الاستشارة المجانية',
                'فتح الاستشارة الخاصة'
            ]
        },
        'consultation_choice': {
            'layout': 'اختيار نوع الاستشارة',
            'components': [
                'عنوان الشاشة',
                'رسالة توضيحية',
                'بطاقة الاستشارة المجانية',
                'بطاقة الاستشارة الخاصة'
            ],
            'fields': [],
            'actions': [
                {
                    'id': 'open_free_consultation',
                    'label': 'الاستشارة المجانية',
                    'method': 'GET'
                },
                {
                    'id': 'open_private_consultation',
                    'label': 'الاستشارة الخاصة',
                    'method': 'GET'
                }
            ]
        },
        'free_consultation': {
            'layout': 'محادثة استشارية',
            'components': [
                'عنوان الاستشارة',
                'منطقة الرسائل',
                'حقل كتابة الرسالة',
                'زر إرسال',
                'حالة الرسالة'
            ],
            'fields': ['الرسالة'],
            'actions': [
                'إرسال رسالة',
                'استقبال الرسائل',
                'عرض الرسائل',
                'نسخ رد المستشار',
                'طباعة رد المستشار',
                'تصدير رد المستشار'
            ]
        },
        'private_consultation': {
            'layout': 'محادثة خاصة مع المستشار',
            'components': [
                'بيانات المستشار',
                'منطقة الرسائل',
                'حقل كتابة الرسالة',
                'زر إرسال',
                'شريط أدوات المرفقات',
                'اختيار مستند',
                'اختيار ملف',
                'اختيار فيديو',
                'اختيار ملف صوتي',
                'قائمة الملفات المرفقة'
            ],
            'fields': ['الرسالة', 'الملف'],
            'actions': [
                'إرسال رسالة',
                'استقبال الرسائل',
                'إرفاق مستند',
                'إرفاق ملف',
                'إرفاق فيديو',
                'إرفاق ملف صوتي',
                'نسخ رد المستشار',
                'طباعة رد المستشار',
                'تصدير رد المستشار'
            ]
        },
        'chat': {
            'layout': 'محادثة',
            'components': [
                'قائمة المحادثات',
                'منطقة الرسائل',
                'حقل كتابة',
                'زر إرسال'
            ],
            'fields': ['الرسالة'],
            'actions': [
                'إرسال رسالة',
                'إرفاق ملف',
                'فتح الكاميرا',
                'تسجيل صوت'
            ]
        },
        'camera': {
            'layout': 'وسائط',
            'components': [
                'معاينة الكاميرا',
                'أزرار التحكم',
                'معاينة الوسائط'
            ],
            'fields': [],
            'actions': [
                'تشغيل الكاميرا',
                'إيقاف الكاميرا',
                'التقاط',
                'إرسال'
            ]
        },
        'microphone': {
            'layout': 'وسائط',
            'components': [
                'مؤشر التسجيل',
                'أزرار التحكم',
                'مشغل الصوت'
            ],
            'fields': [],
            'actions': [
                'بدء التسجيل',
                'إيقاف التسجيل',
                'تشغيل',
                'إرسال'
            ]
        },
        'attachments': {
            'layout': 'قائمة ملفات',
            'components': [
                'اختيار الملفات',
                'قائمة المرفقات',
                'حالة الرفع'
            ],
            'fields': ['الملف'],
            'actions': [
                'اختيار ملف',
                'رفع',
                'حذف',
                'فتح'
            ]
        },
        'cases': {
            'layout': 'إدارة سجلات',
            'components': [
                'شريط بحث',
                'قائمة القضايا',
                'بيانات القضية',
                'حالة القضية'
            ],
            'fields': [
                'رقم القضية',
                'المحكمة',
                'الدائرة',
                'الحالة',
                'ملاحظات'
            ],
            'actions': [
                'إضافة',
                'تعديل',
                'عرض',
                'حذف',
                'بحث'
            ]
        },
        'clients': {
            'layout': 'إدارة سجلات',
            'components': [
                'شريط بحث',
                'قائمة الموكلين',
                'بطاقة الموكل'
            ],
            'fields': [
                'الاسم',
                'رقم الهاتف',
                'البريد',
                'الحالة'
            ],
            'actions': [
                'إضافة',
                'تعديل',
                'عرض',
                'حذف',
                'بحث'
            ]
        },
        'sessions': {
            'layout': 'جدول مواعيد',
            'components': [
                'التقويم',
                'قائمة المواعيد',
                'تفاصيل الموعد'
            ],
            'fields': [
                'التاريخ',
                'الوقت',
                'الموضوع',
                'الحالة'
            ],
            'actions': [
                'حجز',
                'تعديل',
                'إلغاء',
                'فتح'
            ]
        },
        'documents': {
            'layout': 'مكتبة ملفات',
            'components': [
                'شريط بحث',
                'قائمة المستندات',
                'رفع ملف',
                'تفاصيل المستند'
            ],
            'fields': [
                'اسم المستند',
                'نوع الملف',
                'الوصف'
            ],
            'actions': [
                'رفع',
                'فتح',
                'تحميل',
                'حذف',
                'بحث'
            ]
        },
        'products': {
            'layout': 'كتالوج',
            'components': [
                'بحث',
                'بطاقات المنتجات',
                'تفاصيل المنتج'
            ],
            'fields': [
                'اسم المنتج',
                'السعر',
                'الكمية',
                'الوصف'
            ],
            'actions': [
                'إضافة',
                'تعديل',
                'عرض',
                'حذف',
                'بحث'
            ]
        },
        'students': {
            'layout': 'إدارة سجلات',
            'components': [
                'بحث',
                'قائمة الطلاب',
                'بطاقة الطالب'
            ],
            'fields': [
                'الاسم',
                'الصف',
                'رقم الطالب',
                'الحالة'
            ],
            'actions': [
                'إضافة',
                'تعديل',
                'عرض',
                'حذف',
                'بحث'
            ]
        },
        'courses': {
            'layout': 'كتالوج تعليمي',
            'components': [
                'قائمة الدورات',
                'تفاصيل الدورة',
                'بحث'
            ],
            'fields': [
                'اسم الدورة',
                'الوصف',
                'المدرس',
                'الحالة'
            ],
            'actions': [
                'إضافة',
                'تعديل',
                'عرض',
                'بحث'
            ]
        }
    }

    def analyze(self, screen, requirements=None):
        requirements = requirements or {}

        screen_id = screen.get('id', 'screen')
        title = str(screen.get('title', 'شاشة جديدة')).strip()
        purpose = str(screen.get('purpose', 'واجهة البرنامج')).strip()
        features = screen.get('features', [])
        if not isinstance(features, list):
            features = [str(features)]
        semantic_text = ' '.join(
            [title, purpose] + [str(item) for item in features]
        ).lower()

        capabilities = set(requirements.get('capabilities', []))
        roles = list(requirements.get('roles', ['user']))

        # نوع الشاشة يُستنتج من معناها ووظائفها، وليس من معرف ثابت.
        if any(word in semantic_text for word in (
            'محادثة', 'رسائل', 'رسالة', 'دردشة', 'chat',
            'استشارة', 'تواصل'
        )):
            screen_kind = 'conversation'
        elif any(word in semantic_text for word in (
            'موعد', 'مواعيد', 'حجز', 'جلسة', 'تقويم', 'calendar'
        )):
            screen_kind = 'scheduling'
        elif any(word in semantic_text for word in (
            'ملف', 'ملفات', 'مرفق', 'مرفقات', 'مستند',
            'مستندات', 'وثيقة', 'رفع', 'تحميل'
        )):
            screen_kind = 'files'
        elif any(word in semantic_text for word in (
            'لوحة تحكم', 'إحصائيات', 'ملخص', 'dashboard'
        )):
            screen_kind = 'dashboard'
        elif any(word in semantic_text for word in (
            'منتج', 'منتجات', 'دورة', 'دورات', 'كتالوج'
        )):
            screen_kind = 'catalog'
        elif any(word in semantic_text for word in (
            'قائمة', 'سجلات', 'إدارة', 'مستخدمين', 'موكلين',
            'عملاء', 'قضايا', 'بحث'
        )):
            screen_kind = 'records'
        elif any(word in semantic_text for word in (
            'كاميرا', 'فيديو', 'صوت', 'ميكروفون', 'وسائط'
        )):
            screen_kind = 'media'
        elif any(word in semantic_text for word in (
            'تسجيل', 'إنشاء', 'إضافة', 'تعديل', 'نموذج', 'بيانات'
        )):
            screen_kind = 'form'
        elif any(word in semantic_text for word in (
            'رئيسية', 'الرئيسية', 'ترحيب', 'بوابة', 'home', 'welcome'
        )):
            screen_kind = 'home'
        else:
            screen_kind = 'general'

        templates = {
            'home': {
                'layout': 'واجهة رئيسية',
                'components': ['عنوان البرنامج', 'رسالة ترحيبية', 'الوظائف الأساسية', 'شريط التنقل'],
                'fields': [],
                'actions': ['عرض الوظائف الأساسية', 'الانتقال إلى الوظيفة المختارة']
            },
            'conversation': {
                'layout': 'واجهة محادثة',
                'components': ['عنوان الشاشة', 'منطقة الرسائل', 'حقل كتابة الرسالة', 'زر إرسال'],
                'fields': ['الرسالة'],
                'actions': ['إرسال رسالة', 'استقبال الرسائل', 'عرض الرسائل']
            },
            'scheduling': {
                'layout': 'واجهة المواعيد',
                'components': ['التقويم', 'قائمة المواعيد', 'تفاصيل الموعد', 'إجراء رئيسي'],
                'fields': ['التاريخ', 'الوقت', 'الموضوع', 'الحالة'],
                'actions': ['إضافة موعد', 'تعديل الموعد', 'إلغاء الموعد', 'فتح الموعد']
            },
            'files': {
                'layout': 'واجهة الملفات',
                'components': ['قائمة الملفات', 'اختيار ملف', 'تفاصيل الملف', 'حالة الرفع'],
                'fields': ['الملف'],
                'actions': ['اختيار ملف', 'رفع', 'فتح', 'تحميل']
            },
            'dashboard': {
                'layout': 'لوحة تحكم',
                'components': ['العنوان', 'ملخص البيانات', 'بطاقات المعلومات', 'الإجراءات الرئيسية'],
                'fields': [],
                'actions': ['عرض الملخص', 'فتح الوظيفة المختارة']
            },
            'records': {
                'layout': 'واجهة إدارة سجلات',
                'components': ['شريط البحث', 'قائمة السجلات', 'تفاصيل السجل', 'الإجراءات'],
                'fields': ['بيانات السجل'],
                'actions': ['إضافة', 'تعديل', 'عرض', 'حذف', 'بحث']
            },
            'catalog': {
                'layout': 'واجهة كتالوج',
                'components': ['البحث', 'قائمة العناصر', 'بطاقات العناصر', 'تفاصيل العنصر'],
                'fields': ['بيانات العنصر'],
                'actions': ['عرض', 'بحث', 'فتح التفاصيل']
            },
            'media': {
                'layout': 'واجهة الوسائط',
                'components': ['معاينة الوسائط', 'أزرار التحكم', 'حالة الوسائط'],
                'fields': [],
                'actions': ['تشغيل', 'إيقاف', 'إرسال']
            },
            'form': {
                'layout': 'واجهة نموذج',
                'components': ['عنوان الشاشة', 'حقول البيانات', 'الإجراءات'],
                'fields': ['بيانات الشاشة'],
                'actions': ['حفظ', 'إلغاء']
            },
            'general': {
                'layout': 'واجهة قياسية متجاوبة',
                'components': ['العنوان', 'المحتوى', 'الإجراءات'],
                'fields': [],
                'actions': ['عرض', 'تنفيذ الإجراء الرئيسي']
            }
        }

        base = templates[screen_kind]

        # الوظائف الإضافية تُضاف داخل الشاشة المناسبة ولا تنشئ شاشة جديدة.
        actions = list(base['actions'])
        components = list(base['components'])

        if 'files' in capabilities and screen_kind == 'conversation':
            components.append('شريط المرفقات')
            actions.append('إرفاق ملف')

        if 'camera' in capabilities and screen_kind == 'conversation':
            actions.append('فتح الكاميرا')

        if 'microphone' in capabilities and screen_kind == 'conversation':
            actions.append('تسجيل صوت')

        if 'print' in capabilities:
            actions.append('طباعة')

        if 'export' in capabilities:
            actions.append('تصدير')

        # التنقل يُستنتج من الشاشات التي حللها عبقرينو، وليس من أسماء قانونية ثابتة.
        all_screens = requirements.get('screens', [])
        screen_ids = [
            item.get('id') for item in all_screens
            if isinstance(item, dict) and item.get('id')
        ]
        home_id = next(
            (sid for sid in screen_ids if sid == 'home'),
            None
        )

        if home_id and screen_id != home_id:
            navigation = {'from': [home_id], 'to': []}
        elif home_id and screen_id == home_id:
            navigation = {
                'from': [],
                'to': [sid for sid in screen_ids if sid != screen_id]
            }
        else:
            navigation = {'from': [], 'to': []}

        needed_by_kind = {
            'home': {'database'},
            'conversation': {'database', 'chat'},
            'scheduling': {'database', 'scheduling'},
            'files': {'database', 'files'},
            'dashboard': {'database'},
            'records': {'database', 'crud'},
            'catalog': {'database', 'crud'},
            'media': {'database'},
            'form': {'database'},
            'general': {'database'}
        }

        needed = needed_by_kind[screen_kind]
        screen_capabilities = sorted(
            needed.intersection(capabilities) or needed
        )

        return {
            'screen_id': screen_id,
            'title': title,
            'purpose': purpose,
            'layout': base['layout'],
            'components': list(dict.fromkeys(components)),
            'fields': list(base['fields']),
            'actions': list(dict.fromkeys(actions)),
            'roles': roles,
            'capabilities': screen_capabilities,
            'navigation': navigation,
        }

class ScreenProposalEngine:

    def __init__(self, requirements=None):
        self.requirements = requirements or {}
        self.intelligence = ScreenIntelligenceEngine()

    def proposals(self, screen, offset=0):
        intelligent = self.intelligence.analyze(screen, self.requirements)
        layouts = [('بطاقات', ['العنوان', 'بطاقات الوظائف', 'شريط التنقل']), ('لوحة تحكم', ['العنوان', 'إحصائيات', 'أزرار رئيسية', 'قائمة']), ('قائمة مركزة', ['العنوان', 'قائمة الوظائف', 'زر إجراء رئيسي']), ('واجهة جانبية', ['قائمة جانبية', 'منطقة محتوى', 'زر رئيسي']), ('واجهة كبيرة', ['عنوان كبير', 'إجراءات رئيسية', 'محتوى']), ('واجهة مختصرة', ['عنوان', 'أزرار كبيرة', 'معلومات مختصرة'])]
        result = []
        for i in range(3):
            index = (offset + i) % len(layouts)
            fallback_layout, fallback_components = layouts[index]
            layout = intelligent['layout'] if i == 0 else fallback_layout
            components = intelligent['components'] if i == 0 else fallback_components
            proposal = ScreenProposal(screen_id=screen['id'], title=screen['title'], purpose=screen['purpose'], variant=i + 1, layout=layout, components=components)
            data = asdict(proposal)
            data.update({'fields': intelligent['fields'], 'actions': intelligent['actions'], 'roles': intelligent['roles'], 'capabilities': intelligent['capabilities'], 'navigation': intelligent['navigation']})
            result.append(data)
        return result

class ScreenApprovalWizard:

    def __init__(self):
        self.engine = ScreenProposalEngine()

    def display(self, proposal):
        print('\n' + '─' * 60)
        print(f'التصميم رقم {proposal.variant}')
        print(f'الشاشة: {proposal.title}')
        print(f'الغرض: {proposal.purpose}')
        print(f'النمط: {proposal.layout}')
        print('العناصر: ' + ' • '.join(proposal.components))
        print('─' * 60)

    def choose(self, screen):
        offset = 0
        while True:
            proposals = self.engine.proposals(screen, offset)
            print('\n╔══════════════════════════════════════╗')
            print(f"  اقتراحات شاشة: {screen['title']}")
            print('╚══════════════════════════════════════╝')
            for proposal in proposals:
                self.display(proposal)
            print('\n1 - اختيار التصميم الأول\n2 - اختيار التصميم الثاني\n3 - اختيار التصميم الثالث\n4 - عرض تصميمات أخرى\n5 - تعديل الشاشة\n6 - رفض الشاشة\n')
            choice = input('اختيارك: ').strip()
            if choice in ('1', '2', '3'):
                selected = proposals[int(choice) - 1]
                selected.approved = True
                return asdict(selected)
            if choice == '4':
                offset += 3
                continue
            if choice == '5':
                change = input('ما التعديل المطلوب؟ ').strip()
                if change:
                    screen = dict(screen)
                    screen['purpose'] += ' — تعديل المستخدم: ' + change
                continue
            if choice == '6':
                return None
            print('[-] اختيار غير صحيح.')

class DatabaseEngine:
    TABLE_RULES = {'users': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL'), ('email', 'TEXT'), ('phone', 'TEXT'), ('password_hash', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'roles': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL UNIQUE')]}, 'permissions': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL UNIQUE'), ('description', 'TEXT')]}, 'user_roles': {'columns': [('user_id', 'INTEGER NOT NULL'), ('role_id', 'INTEGER NOT NULL')]}, 'clients': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL'), ('phone', 'TEXT'), ('email', 'TEXT'), ('status', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'lawyers': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL'), ('phone', 'TEXT'), ('email', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'cases': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('case_number', 'TEXT'), ('court', 'TEXT'), ('chamber', 'TEXT'), ('status', 'TEXT'), ('notes', 'TEXT'), ('client_id', 'INTEGER'), ('lawyer_id', 'INTEGER'), ('created_at', 'TEXT NOT NULL')]}, 'case_notes': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('case_id', 'INTEGER NOT NULL'), ('user_id', 'INTEGER'), ('note', 'TEXT NOT NULL'), ('created_at', 'TEXT NOT NULL')]}, 'appointments': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('title', 'TEXT NOT NULL'), ('appointment_date', 'TEXT NOT NULL'), ('status', 'TEXT'), ('user_id', 'INTEGER'), ('created_at', 'TEXT NOT NULL')]}, 'consultations': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('user_id', 'INTEGER NOT NULL'), ('consultant_id', 'INTEGER'), ('type', 'TEXT NOT NULL'), ('status', 'TEXT'), ('subject', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'documents': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('conversation_id', 'INTEGER NOT NULL'), ('uploaded_by', 'INTEGER NOT NULL'), ('name', 'TEXT NOT NULL'), ('file_path', 'TEXT NOT NULL'), ('mime_type', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'messages': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('conversation_id', 'INTEGER NOT NULL'), ('sender_id', 'INTEGER NOT NULL'), ('message', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'conversations': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('consultation_id', 'INTEGER NOT NULL'), ('title', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'conversation_members': {'columns': [('conversation_id', 'INTEGER NOT NULL'), ('user_id', 'INTEGER NOT NULL'), ('joined_at', 'TEXT NOT NULL')]}, 'translations': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('document_id', 'INTEGER'), ('source_text', 'TEXT'), ('source_language', 'TEXT'), ('target_language', 'TEXT'), ('translated_text', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'document_text': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('document_id', 'INTEGER NOT NULL'), ('extracted_text', 'TEXT'), ('extraction_method', 'TEXT'), ('detected_language', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'audio_transcriptions': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('file_path', 'TEXT'), ('transcription_text', 'TEXT'), ('detected_language', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'audio_outputs': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('source_text', 'TEXT'), ('language', 'TEXT'), ('audio_path', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'notifications': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('user_id', 'INTEGER'), ('title', 'TEXT NOT NULL'), ('message', 'TEXT'), ('is_read', 'INTEGER NOT NULL DEFAULT 0'), ('created_at', 'TEXT NOT NULL')]}, 'products': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL'), ('price', 'REAL NOT NULL DEFAULT 0'), ('quantity', 'INTEGER NOT NULL DEFAULT 0'), ('description', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'orders': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('user_id', 'INTEGER'), ('total', 'REAL NOT NULL DEFAULT 0'), ('status', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'courses': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL'), ('description', 'TEXT'), ('teacher_id', 'INTEGER'), ('status', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'students': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('name', 'TEXT NOT NULL'), ('student_number', 'TEXT'), ('class_name', 'TEXT'), ('status', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'reports': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('title', 'TEXT NOT NULL'), ('report_type', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}, 'audit_logs': {'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('user_id', 'INTEGER'), ('action', 'TEXT NOT NULL'), ('target', 'TEXT'), ('created_at', 'TEXT NOT NULL')]}}
    DOMAIN_TABLES = {'legal': ['clients', 'lawyers', 'cases', 'documents'], 'commerce': ['products', 'orders'], 'education': ['courses', 'students'], 'crm': ['clients'], 'booking': ['appointments'], 'finance': ['orders', 'reports'], 'project_management': ['reports'], 'support': ['tickets'], 'logistics': ['orders']}
    CAPABILITY_TABLES = {'translation': ['translations'], 'document_processing': ['documents'], 'ocr': ['document_text'], 'speech_to_text': ['audio_transcriptions'], 'text_to_speech': ['audio_outputs'], 'auth': ['users', 'roles', 'user_roles'], 'users': ['users'], 'roles': ['roles', 'user_roles'], 'chat': ['messages'], 'files': ['documents'], 'notifications': ['notifications'], 'reports': ['reports'], 'audit': ['audit_logs'], 'scheduling': ['appointments']}

    def analyze(self, requirements):
        tables = {'users'}

        # المصدر الأساسي للجداول هو الكيانات الصريحة.
        # إذا لم تكن موجودة، نستنتج الكيانات من الشاشات والخصائص
        # التي حللها عبقرينو من فكرة المستخدم.
        entities = requirements.get('entities', [])
        if not isinstance(entities, list):
            entities = []

        if not entities:
            screens = requirements.get('screens', [])
            if not isinstance(screens, list):
                screens = []

            screen_ids = {
                str(screen.get('id', '')).strip()
                for screen in screens
                if isinstance(screen, dict)
            }

            features = requirements.get('features', [])
            if not isinstance(features, list):
                features = []

            feature_text = ' '.join(
                str(item).strip()
                for item in features
            )

            if {'free_consultation', 'private_consultation'} & screen_ids:
                entities.append('consultations')

            if (
                'محادثة' in feature_text
                or 'رسائل' in feature_text
                or 'إرسال واستقبال' in feature_text
                or 'الرسائل' in feature_text
            ):
                entities.extend([
                    'conversations',
                    'messages',
                ])

            if (
                'ملف' in feature_text
                or 'مستند' in feature_text
                or 'مرفق' in feature_text
                or 'إرفاق' in feature_text
                or 'فيديو' in feature_text
                or 'صوت' in feature_text
            ):
                entities.append('documents')

        for entity in entities:
            if entity in self.TABLE_RULES:
                tables.add(entity)

        # ربط المحادثات بالاستشارات عند وجودها.
        if 'consultations' in tables:
            tables.add('conversations')

        if 'conversations' in tables:
            tables.add('messages')

        roles = requirements.get('roles', [])
        if roles:
            tables.update({'roles', 'user_roles'})
        if 'cases' in tables:
            tables.update({'clients', 'lawyers'})
        if 'documents' in tables and 'cases' in tables:
            tables.add('documents')
        if 'translation' in requirements.get('capabilities', []):
            tables.add('translations')
        if 'document_processing' in requirements.get('capabilities', []):
            tables.add('documents')
        if 'ocr' in requirements.get('capabilities', []):
            tables.add('document_text')
        if 'speech_to_text' in requirements.get('capabilities', []):
            tables.add('audio_transcriptions')
        if 'text_to_speech' in requirements.get('capabilities', []):
            tables.add('audio_outputs')
        return sorted((table for table in tables if table in self.TABLE_RULES))

    def schema(self, requirements):
        tables = self.analyze(requirements)
        statements = ['PRAGMA foreign_keys = ON;']
        for table in tables:
            columns = self.TABLE_RULES[table]['columns']
            column_sql = ',\n    '.join((f'{name} {definition}' for name, definition in columns))
            statements.append(f'CREATE TABLE IF NOT EXISTS {table} (\n    {column_sql}\n);')
        if 'user_roles' in tables:
            statements.append('CREATE UNIQUE INDEX IF NOT EXISTS idx_user_roles_unique ON user_roles(user_id, role_id);')
        if 'cases' in tables:
            statements.extend(['CREATE INDEX IF NOT EXISTS idx_cases_client ON cases(client_id);', 'CREATE INDEX IF NOT EXISTS idx_cases_lawyer ON cases(lawyer_id);'])
        if 'messages' in tables:
            statements.append('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, sender_id);')
        return '\n\n'.join(statements) + '\n'

class ProjectGenerator:

    def __init__(self, root):
        self.root = Path(root)

    @staticmethod
    def create_zip(project_path, output_dir=None):
        import shutil
        from pathlib import Path
        project_path = Path(project_path).resolve()
        if not project_path.exists() or not project_path.is_dir():
            raise FileNotFoundError(f'المشروع غير موجود: {project_path}')
        output_dir = Path(output_dir).resolve() if output_dir else project_path.parent.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_base = output_dir / project_path.name
        old_zip = archive_base.with_suffix('.zip')
        if old_zip.exists():
            old_zip.unlink()
        archive = shutil.make_archive(str(archive_base), 'zip', root_dir=project_path.parent, base_dir=project_path.name)
        return str(Path(archive).resolve())

    @staticmethod
    def safe_name(text):
        text = re.sub('[^\\w\\u0600-\\u06FF -]+', '', text, flags=re.UNICODE)
        text = re.sub('\\s+', '-', text.strip())
        return text[:80] or 'abqaryno-project'

    def generate(self, idea, requirements, approved_screens, options=None):
        raw_idea = str(idea or '').strip()
        display_idea = raw_idea
        document_marker = 'وثيقة تنفيذية'
        if document_marker in display_idea:
            display_idea = display_idea.split(document_marker, 1)[0].strip()
        display_idea = display_idea.rstrip(' -—:|')
        if not display_idea:
            display_idea = 'مشروع عبقرينو'
        name = self.safe_name(display_idea)
        options = options or []
        target = self.root / name
        public = target / 'public'
        public.mkdir(parents=True, exist_ok=True)
        project_dirs = [target / 'server', target / 'routes', target / 'services', target / 'database', target / 'uploads', public / 'css', public / 'js']
        for directory in project_dirs:
            directory.mkdir(parents=True, exist_ok=True)
        cards = []
        for screen in approved_screens:
            cards.append(f"""\n<section class="screen">\n<h2>{html.escape(screen['title'])}</h2>\n<p>{html.escape(screen['purpose'])}</p>\n<strong>\nالتصميم: {html.escape(screen.get('layout', 'واجهة قياسية متجاوبة'))}\n</strong>\n</section>\n""")
        page = f"""<!doctype html>\n<html lang="ar" dir="rtl">\n\n<head>\n\n<meta charset="utf-8">\n\n<meta name="viewport"\ncontent="width=device-width,initial-scale=1">\n\n<title>{html.escape(display_idea)}</title>\n\n<style>\n\nbody {{\n    margin: 0;\n    background: #101010;\n    color: #f5d76e;\n    font-family: Tahoma, Arial;\n}}\n\nheader {{\n    padding: 30px;\n    text-align: center;\n    border-bottom: 1px solid #66551c;\n}}\n\nmain {{\n    max-width: 1100px;\n    margin: auto;\n    padding: 25px;\n    display: grid;\n    grid-template-columns:\n        repeat(auto-fit,minmax(260px,1fr));\n    gap: 20px;\n}}\n\n.screen {{\n    background: #1d1d1d;\n    border: 1px solid #806b24;\n    border-radius: 18px;\n    padding: 25px;\n}}\n\n</style>\n\n<link rel="stylesheet" href="/css/style.css">\n</head>\n\n<body>\n\n<header>\n\n<div class="brand-logo-wrap">\n    <button\n        id="logo-button"\n        class="logo-button"\n        type="button"\n        title="تغيير اللوجو"\n        aria-label="تغيير اللوجو"\n    >\n        <span id="logo-placeholder" class="logo-placeholder">👤</span>\n        <img id="app-logo" class="logo-image" alt="لوجو البرنامج">\n    </button>\n\n    <input\n        id="logo-input"\n        type="file"\n        accept="image/*"\n        hidden\n    >\n\n    <div class="logo-actions">\n        <button id="logo-change" type="button">تغيير اللوجو</button>\n        <button id="logo-remove" type="button">حذف اللوجو</button>\n    </div>\n</div>\n\n<h1>{html.escape(display_idea)}</h1>\n\n<p>\nتم تصميم المشروع واعتماد شاشاته بواسطة عبقرينو\n</p>\n\n</header>\n\n<main>\n\n{''.join(cards)}\n\n</main>\n\n</body>\n\n</html>\n"""
        tools_ui = '\n<section id="abqaryno-tools" class="tools-panel">\n\n    <div class="tool-card" id="chat-tool">\n        <h2>💬 المحادثة</h2>\n        <div id="chat-messages" class="chat-messages"></div>\n        <div class="chat-input-row">\n            <input id="chat-input" type="text" placeholder="اكتب رسالتك...">\n            <button id="chat-send">إرسال</button>\n        </div>\n    </div>\n\n    <div class="tool-card" id="camera-tool">\n        <h2>📷 الكاميرا</h2>\n        <video id="camera-preview" autoplay playsinline muted></video>\n        <div class="tool-actions">\n            <button id="camera-start">تشغيل الكاميرا</button>\n            <button id="camera-stop">إيقاف الكاميرا</button>\n        </div>\n    </div>\n\n    <div class="tool-card" id="microphone-tool">\n        <h2>🎙️ المايك والتسجيل</h2>\n        <div class="tool-actions">\n            <button id="mic-start">تشغيل المايك</button>\n            <button id="mic-record">بدء التسجيل</button>\n            <button id="mic-stop">إيقاف التسجيل</button>\n        </div>\n        <audio id="recorded-audio" controls hidden></audio>\n    </div>\n\n    <div class="tool-card" id="attachments-tool">\n        <h2>📎 المرفقات</h2>\n        <input id="attachment-input" type="file" multiple>\n        <div id="attachment-list"></div>\n    </div>\n\n</section>\n'
        page = page.replace('</main>', tools_ui + '\n</main>', 1)
        interactive_script = '\n<script>\ndocument.addEventListener("DOMContentLoaded", () => {\n\n    // لوجو البرنامج: اختيار وتغيير وحذف وحفظ محلي\n    const logoButton = document.getElementById("logo-button");\n    const logoInput = document.getElementById("logo-input");\n    const logoImage = document.getElementById("app-logo");\n    const logoPlaceholder = document.getElementById("logo-placeholder");\n    const logoChange = document.getElementById("logo-change");\n    const logoRemove = document.getElementById("logo-remove");\n    const logoStorageKey = "abqarynoLogo";\n\n    function renderLogo(value) {\n        if (value) {\n            logoImage.src = value;\n            logoImage.style.display = "block";\n            logoPlaceholder.style.display = "none";\n        } else {\n            logoImage.removeAttribute("src");\n            logoImage.style.display = "none";\n            logoPlaceholder.style.display = "inline";\n        }\n    }\n\n    function openLogoPicker() {\n        if (logoInput) {\n            logoInput.click();\n        }\n    }\n\n    renderLogo(localStorage.getItem(logoStorageKey));\n\n    if (logoButton) {\n        logoButton.addEventListener("click", openLogoPicker);\n    }\n\n    if (logoChange) {\n        logoChange.addEventListener("click", openLogoPicker);\n    }\n\n    if (logoInput) {\n        logoInput.addEventListener("change", event => {\n            const file = event.target.files && event.target.files[0];\n\n            if (!file) return;\n\n            if (!file.type.startsWith("image/")) {\n                alert("من فضلك اختر صورة فقط.");\n                return;\n            }\n\n            const reader = new FileReader();\n\n            reader.onload = () => {\n                const value = reader.result;\n                localStorage.setItem(logoStorageKey, value);\n                renderLogo(value);\n            };\n\n            reader.readAsDataURL(file);\n        });\n    }\n\n    if (logoRemove) {\n        logoRemove.addEventListener("click", () => {\n            localStorage.removeItem(logoStorageKey);\n            renderLogo(null);\n\n            if (logoInput) {\n                logoInput.value = "";\n            }\n        });\n    }\n\n    const chatInput = document.getElementById("chat-input");\n    const chatSend = document.getElementById("chat-send");\n    const chatMessages = document.getElementById("chat-messages");\n\n    if (window.abqarynoChat && chatInput && chatSend) {\n        chatSend.addEventListener("click", () => {\n            const item = window.abqarynoChat.send(chatInput.value);\n\n            if (!item) return;\n\n            const message = document.createElement("div");\n            message.className = "chat-message";\n            message.textContent = item.text;\n\n            chatMessages.appendChild(message);\n            chatInput.value = "";\n            chatInput.focus();\n        });\n\n        chatInput.addEventListener("keydown", event => {\n            if (event.key === "Enter") {\n                chatSend.click();\n            }\n        });\n    }\n\n    const video = document.getElementById("camera-preview");\n    const cameraStart = document.getElementById("camera-start");\n    const cameraStop = document.getElementById("camera-stop");\n\n    const camera = window.AbqarynoCamera\n        ? new window.AbqarynoCamera()\n        : null;\n\n    if (camera && cameraStart) {\n        cameraStart.addEventListener("click", async () => {\n            try {\n                await camera.start(video);\n            } catch (error) {\n                alert("تعذر تشغيل الكاميرا: " + error.message);\n            }\n        });\n    }\n\n    if (camera && cameraStop) {\n        cameraStop.addEventListener("click", () => camera.stop());\n    }\n\n    const micStart = document.getElementById("mic-start");\n    const micRecord = document.getElementById("mic-record");\n    const micStop = document.getElementById("mic-stop");\n    const recordedAudio = document.getElementById("recorded-audio");\n\n    const microphone = window.AbqarynoMicrophone\n        ? new window.AbqarynoMicrophone()\n        : null;\n\n    if (microphone && micStart) {\n        micStart.addEventListener("click", async () => {\n            try {\n                await microphone.start();\n            } catch (error) {\n                alert("تعذر تشغيل المايك: " + error.message);\n            }\n        });\n    }\n\n    if (microphone && micRecord) {\n        micRecord.addEventListener("click", () => {\n            try {\n                microphone.record();\n            } catch (error) {\n                alert(error.message);\n            }\n        });\n    }\n\n    if (microphone && micStop) {\n        micStop.addEventListener("click", async () => {\n            const blob = await microphone.stopRecording();\n\n            if (!blob || !recordedAudio) return;\n\n            recordedAudio.src = URL.createObjectURL(blob);\n            recordedAudio.hidden = false;\n        });\n    }\n\n    const attachmentInput =\n        document.getElementById("attachment-input");\n\n    const attachmentList =\n        document.getElementById("attachment-list");\n\n    if (window.abqarynoAttachments && attachmentInput) {\n        attachmentInput.addEventListener("change", event => {\n\n            const files =\n                window.abqarynoAttachments.add(\n                    event.target.files\n                );\n\n            attachmentList.innerHTML = "";\n\n            files.forEach(file => {\n                const item = document.createElement("div");\n\n                item.className = "attachment-item";\n                item.textContent =\n                    file.name +\n                    " (" +\n                    Math.round(file.size / 1024) +\n                    " KB)";\n\n                attachmentList.appendChild(item);\n            });\n        });\n    }\n});\n</script>\n'
        assistant_ui = '\n<style>\n#abqaryno-assistant .assistant-action-confirmation {\n    display: flex;\n    flex-wrap: wrap;\n    align-items: center;\n    gap: 8px;\n    margin: 10px 0;\n    padding: 10px;\n    border: 1px solid rgba(255, 193, 7, 0.35);\n    border-radius: 10px;\n}\n\n#abqaryno-assistant .assistant-action-confirmation button {\n    border: 0;\n    border-radius: 8px;\n    padding: 8px 14px;\n    cursor: pointer;\n    font: inherit;\n}\n\n#abqaryno-assistant .assistant-action-confirmation button:first-child {\n    background: #198754;\n    color: #fff;\n}\n\n#abqaryno-assistant .assistant-action-confirmation button:nth-child(2) {\n    background: #6c757d;\n    color: #fff;\n}\n\n#abqaryno-assistant .assistant-action-confirmation button:disabled {\n    opacity: 0.55;\n    cursor: not-allowed;\n}\n\n#abqaryno-assistant .assistant-action-status {\n    font-size: 0.9em;\n    opacity: 0.8;\n}\n</style>\n\n<section id="abqaryno-assistant" class="assistant-panel">\n    <div class="assistant-header">\n        <div>\n            <h2>🧠 المساعد الذكي</h2>\n            <p id="assistant-context-label">\n                يفهم البرنامج والشاشة الحالية ويساعدك أثناء الاستخدام.\n            </p>\n        </div>\n        <button\n            id="assistant-clear"\n            type="button"\n            aria-label="مسح محادثة المساعد"\n        >\n            مسح\n        </button>\n    </div>\n\n    <div\n        id="assistant-messages"\n        class="assistant-messages"\n        aria-live="polite"\n    ></div>\n\n    <div class="assistant-input-row">\n        <input\n            id="assistant-input"\n            type="text"\n            placeholder="اسأل المساعد عن البرنامج أو الشاشة الحالية..."\n            autocomplete="off"\n        >\n        <button id="assistant-send" type="button">\n            إرسال\n        </button>\n    </div>\n\n    <div class="assistant-suggestions">\n        <button type="button" data-assistant-question="ماذا يمكنني أن أفعل هنا؟">\n            ماذا أفعل هنا؟\n        </button>\n        <button type="button" data-assistant-question="ما الشاشات الموجودة في البرنامج؟">\n            الشاشات\n        </button>\n        <button type="button" data-assistant-question="ما الوظائف المتاحة؟">\n            الوظائف\n        </button>\n    </div>\n</section>\n\n<script src="/js/assistant.js"></script>\n'
        page = page.replace('</main>', assistant_ui + '\n</main>', 1)
        page = page.replace('</body>', interactive_script + '\n</body>', 1)
        (public / 'index.html').write_text(page, encoding='utf-8')
        assistant_context = {'idea': idea, 'screens': approved_screens, 'roles': requirements.get('roles', []), 'capabilities': requirements.get('capabilities', []), 'capability_labels': requirements.get('capability_labels', {}), 'app_types': requirements.get('app_types', []), 'options': options}
        (public / 'assistant-context.json').write_text(json.dumps(assistant_context, ensure_ascii=False, indent=2), encoding='utf-8')
        assistant_js = '\n(() => {\n    "use strict";\n\n    const state = {\n        context: null,\n        messages: []\n    };\n\n    const $ = id => document.getElementById(id);\n\n    function addMessage(text, type) {\n        const container = $("assistant-messages");\n        if (!container) return;\n\n        const item = document.createElement("div");\n        item.className = "assistant-message " + type;\n        item.textContent = text;\n        container.appendChild(item);\n\n        container.scrollTop = container.scrollHeight;\n        state.messages.push({text, type});\n    }\n\n    function capabilityLabel(key) {\n        const labels =\n            state.context &&\n            state.context.capability_labels;\n\n        return (labels && labels[key]) || key;\n    }\n\n    function currentScreen() {\n        const screens =\n            state.context && state.context.screens;\n\n        if (!Array.isArray(screens) || !screens.length) {\n            return null;\n        }\n\n        const visible = Array.from(\n            document.querySelectorAll(".screen")\n        );\n\n        if (visible.length) {\n            const index = Math.min(\n                Math.max(\n                    window.scrollY > 20 ? 1 : 0,\n                    0\n                ),\n                screens.length - 1\n            );\n\n            return screens[index] || screens[0];\n        }\n\n        return screens[0];\n    }\n\n    function answer(question) {\n        const q = String(question || "").trim().toLowerCase();\n\n        if (!state.context) {\n            return "المساعد ما زال يحمّل معلومات البرنامج. حاول مرة أخرى.";\n        }\n\n        const screen = currentScreen();\n        const screens = Array.isArray(state.context.screens)\n            ? state.context.screens\n            : [];\n\n        const capabilities = Array.isArray(state.context.capabilities)\n            ? state.context.capabilities\n            : [];\n\n        if (\n            q.includes("ماذا") &&\n            (q.includes("أفعل") || q.includes("هنا"))\n        ) {\n            if (screen) {\n                return (\n                    "أنت الآن في شاشة " +\n                    (screen.title || "الحالية") +\n                    ". " +\n                    (screen.purpose || "يمكنك استخدام الوظائف المتاحة في هذه الشاشة.") +\n                    (\n                        Array.isArray(screen.actions) &&\n                        screen.actions.length\n                            ? " الإجراءات المتاحة: " +\n                              screen.actions.join("، ") +\n                              "."\n                            : ""\n                    )\n                );\n            }\n\n            return "يمكنك استخدام الشاشات والوظائف التي أنشأها البرنامج حسب صلاحياتك.";\n        }\n\n        if (\n            q.includes("الشاشات") ||\n            q.includes("شاشة") ||\n            q.includes("الصفحات")\n        ) {\n            if (!screens.length) {\n                return "لم يتم اعتماد شاشات إضافية لهذا البرنامج.";\n            }\n\n            return (\n                "الشاشات المعتمدة: " +\n                screens\n                    .map(item => item.title || item.id)\n                    .filter(Boolean)\n                    .join("، ") +\n                "."\n            );\n        }\n\n        if (\n            q.includes("الوظائف") ||\n            q.includes("القدرات") ||\n            q.includes("ماذا يمكن")\n        ) {\n            if (!capabilities.length) {\n                return "لم يتم تسجيل قدرات إضافية لهذا البرنامج.";\n            }\n\n            return (\n                "الوظائف المتاحة تشمل: " +\n                capabilities\n                    .map(capabilityLabel)\n                    .join("، ") +\n                "."\n            );\n        }\n\n        if (\n            q.includes("ترجم") ||\n            q.includes("ترجمة")\n        ) {\n            if (capabilities.includes("translation")) {\n                return "البرنامج يدعم الترجمة. استخدم وظيفة المستندات أو الترجمة المتاحة في الشاشة المناسبة.";\n            }\n\n            return "ميزة الترجمة غير مفعلة في هذا البرنامج.";\n        }\n\n        if (\n            q.includes("مستند") ||\n            q.includes("pdf") ||\n            q.includes("word")\n        ) {\n            if (\n                capabilities.includes("document_processing") ||\n                capabilities.includes("files")\n            ) {\n                return "البرنامج يحتوي على قدرات للتعامل مع المستندات والملفات. يمكنك اختيار الملف من وظيفة المرفقات أو المستندات.";\n            }\n\n            return "لا توجد قدرة مستندات مسجلة لهذا البرنامج.";\n        }\n\n        if (\n            q.includes("صوت") ||\n            q.includes("تسجيل")\n        ) {\n            if (\n                capabilities.includes("microphone") ||\n                capabilities.includes("speech_to_text") ||\n                capabilities.includes("text_to_speech")\n            ) {\n                return "البرنامج يحتوي على وظائف صوتية مفعلة، ويمكن استخدامها حسب الأدوات الموجودة في الشاشة.";\n            }\n\n            return "الوظائف الصوتية غير مفعلة في هذا البرنامج.";\n        }\n\n        if (\n            q.includes("من أنت") ||\n            q.includes("المساعد")\n        ) {\n            return "أنا المساعد الذكي المدمج في هذا البرنامج. أقرأ سياق البرنامج والشاشات والقدرات لمساعدتك أثناء الاستخدام.";\n        }\n\n        return (\n            "أفهم سؤالك. أستطيع مساعدتك في التنقل وفهم الشاشات والوظائف والمستندات والقدرات المتاحة. " +\n            "جرّب السؤال عن الشاشة الحالية أو الوظائف المتاحة."\n        );\n    }\n\n    async function send(question) {\n        const input = $("assistant-input");\n        const value = String(\n            question !== undefined\n                ? question\n                : input && input.value\n        ).trim();\n\n        if (!value) return;\n\n        addMessage(value, "user");\n\n        if (input) {\n            input.value = "";\n        }\n\n        try {\n            const screen = currentScreen() || {};\n\n            const response = await fetch("/api/assistant", {\n                method: "POST",\n                headers: {\n                    "Content-Type": "application/json"\n                },\n                body: JSON.stringify({\n                    prompt: value,\n                    idea: state.context && state.context.idea\n                        ? state.context.idea\n                        : "",\n                    requirements: state.context || {},\n                    screen: screen,\n                    user: {}\n                })\n            });\n\n            if (!response.ok) {\n                throw new Error("تعذر الاتصال بالمساعد الذكي");\n            }\n\n            const result = await response.json();\n\n            if (!result.ok) {\n                throw new Error(\n                    result.error || "تعذر معالجة طلب المساعد"\n                );\n            }\n\n            addMessage(\n                result.answer || "تم تحليل طلبك.",\n                "assistant"\n            );\n\n            if (Array.isArray(result.actions) && result.actions.length) {\n                result.actions.forEach(action => {\n                    const needsConfirmation =\n                        Boolean(action.requires_confirmation);\n\n                    const suffix = needsConfirmation\n                        ? " — يحتاج إلى تأكيدك قبل التنفيذ."\n                        : "";\n\n                    addMessage(\n                        "اقتراح: " +\n                        (action.title || action.action_id || "إجراء") +\n                        suffix,\n                        "assistant"\n                    );\n\n                    if (needsConfirmation) {\n                        addConfirmationControls(action);\n                    }\n                });\n            }\n        } catch (error) {\n            addMessage(\n                "تعذر الاتصال بالمساعد الذكي حاليًا. " +\n                "جرّب مرة أخرى.",\n                "assistant"\n            );\n        }\n    }\n\n    function addConfirmationControls(action) {\n        const container = $("assistant-messages");\n        if (!container) return;\n\n        const wrapper = document.createElement("div");\n        wrapper.className = "assistant-action-confirmation";\n\n        const confirmButton = document.createElement("button");\n        confirmButton.type = "button";\n        confirmButton.textContent = "تأكيد التنفيذ";\n\n        const cancelButton = document.createElement("button");\n        cancelButton.type = "button";\n        cancelButton.textContent = "إلغاء";\n\n        const status = document.createElement("span");\n        status.className = "assistant-action-status";\n        status.textContent = "بانتظار تأكيدك";\n\n        const setDisabled = () => {\n            confirmButton.disabled = true;\n            cancelButton.disabled = true;\n        };\n\n        const confirm = async confirmed => {\n            setDisabled();\n            status.textContent = "جارٍ معالجة التأكيد...";\n\n            try {\n                const response = await fetch(\n                    "/api/assistant/confirm",\n                    {\n                        method: "POST",\n                        headers: {\n                            "Content-Type": "application/json"\n                        },\n                        body: JSON.stringify({\n                            confirmed,\n                            action: {\n                                action_id: action.action_id || "",\n                                title: action.title || "",\n                                description: action.description || "",\n                                requires_confirmation:\n                                    Boolean(action.requires_confirmation),\n                                status: action.status || "proposed"\n                            }\n                        })\n                    }\n                );\n\n                if (!response.ok) {\n                    throw new Error("تعذر إرسال التأكيد");\n                }\n\n                const result = await response.json();\n\n                if (!result.ok) {\n                    throw new Error(\n                        result.error || "تعذر معالجة التأكيد"\n                    );\n                }\n\n                const finalStatus =\n                    result.action && result.action.status\n                        ? result.action.status\n                        : (confirmed ? "approved" : "cancelled");\n\n                status.textContent =\n                    finalStatus === "approved"\n                        ? "تم تأكيد الإجراء."\n                        : "تم إلغاء الإجراء.";\n\n                if (finalStatus === "approved") {\n                    addMessage(\n                        "تم اعتماد الإجراء بعد تأكيدك.",\n                        "assistant"\n                    );\n                } else {\n                    addMessage(\n                        "تم إلغاء الإجراء.",\n                        "assistant"\n                    );\n                }\n            } catch (error) {\n                confirmButton.disabled = false;\n                cancelButton.disabled = false;\n                status.textContent =\n                    "تعذر معالجة التأكيد. حاول مرة أخرى.";\n            }\n        };\n\n        confirmButton.addEventListener(\n            "click",\n            () => confirm(true)\n        );\n\n        cancelButton.addEventListener(\n            "click",\n            () => confirm(false)\n        );\n\n        wrapper.appendChild(confirmButton);\n        wrapper.appendChild(cancelButton);\n        wrapper.appendChild(status);\n\n        container.appendChild(wrapper);\n        container.scrollTop = container.scrollHeight;\n    }\n\n    function clearMessages() {\n        const container = $("assistant-messages");\n        if (container) {\n            container.innerHTML = "";\n        }\n\n        state.messages = [];\n\n        addMessage(\n            "مرحبًا. أنا المساعد الذكي للبرنامج. كيف أساعدك؟",\n            "assistant"\n        );\n    }\n\n    async function initialize() {\n        try {\n            const response = await fetch(\n                "/assistant-context.json",\n                {cache: "no-store"}\n            );\n\n            if (!response.ok) {\n                throw new Error("تعذر تحميل سياق البرنامج");\n            }\n\n            state.context = await response.json();\n\n            const label = $("assistant-context-label");\n\n            if (label && state.context.idea) {\n                label.textContent =\n                    "المساعد يفهم برنامج: " +\n                    state.context.idea;\n            }\n\n            addMessage(\n                "مرحبًا. أنا المساعد الذكي للبرنامج. اسألني عن الشاشة الحالية أو الوظائف المتاحة.",\n                "assistant"\n            );\n        } catch (error) {\n            addMessage(\n                "تعذر تحميل سياق البرنامج حاليًا.",\n                "assistant"\n            );\n        }\n\n        const input = $("assistant-input");\n        const sendButton = $("assistant-send");\n        const clearButton = $("assistant-clear");\n\n        if (sendButton) {\n            sendButton.addEventListener(\n                "click",\n                () => send()\n            );\n        }\n\n        if (input) {\n            input.addEventListener(\n                "keydown",\n                event => {\n                    if (event.key === "Enter") {\n                        event.preventDefault();\n                        send();\n                    }\n                }\n            );\n        }\n\n        if (clearButton) {\n            clearButton.addEventListener(\n                "click",\n                clearMessages\n            );\n        }\n\n        document\n            .querySelectorAll("[data-assistant-question]")\n            .forEach(button => {\n                button.addEventListener(\n                    "click",\n                    () => send(\n                        button.getAttribute(\n                            "data-assistant-question"\n                        )\n                    )\n                );\n            });\n    }\n\n    if (document.readyState === "loading") {\n        document.addEventListener(\n            "DOMContentLoaded",\n            initialize,\n            {once: true}\n        );\n    } else {\n        initialize();\n    }\n})();\n'
        (public / 'js' / 'assistant.js').write_text(assistant_js, encoding='utf-8')
        traceability = []
        features = requirements.get('features', [])
        capabilities = requirements.get('capabilities', [])
        for index, screen in enumerate(approved_screens, start=1):
            screen_id = str(screen.get('screen_id') or screen.get('id') or f'screen-{index}')
            screen_title = screen.get('title', f'الشاشة {index}')
            related_requirements = []
            for requirement in features:
                requirement_text = str(requirement).strip()
                if requirement_text:
                    related_requirements.append(requirement_text)
            for capability in capabilities:
                capability_text = str(capability).strip()
                if capability_text and capability_text not in related_requirements:
                    related_requirements.append(capability_text)
            actions = screen.get('actions', [])
            if not isinstance(actions, list):
                actions = []
            contracts = []
            if actions:
                for action_index, action in enumerate(actions, start=1):
                    contracts.append({'contract_id': f'{screen_id}-contract-{action_index}', 'name': str(action), 'status': 'DEFINED'})
            else:
                contracts.append({'contract_id': f'{screen_id}-contract-1', 'name': f'وظائف الشاشة: {screen_title}', 'status': 'DEFINED'})
            traceability.append({'trace_id': f'TRACE-{index:04d}', 'requirements': related_requirements, 'screen': {'id': screen_id, 'title': screen_title}, 'contracts': contracts, 'implementation': {'status': 'GENERATED', 'targets': ['public/index.html', 'public/css/style.css', 'public/js/assistant.js']}, 'test': {'status': 'NOT_RUN', 'tests': [], 'result': 'PENDING_GENERATED_PROJECT_VERIFICATION'}})
        manifest = {'idea': idea, 'created_at': now(), 'requirements': requirements, 'approved_screens': approved_screens, 'options': options, 'traceability': {'version': 1, 'chain': ['requirement', 'screen', 'contract', 'implementation', 'test', 'result'], 'items': traceability}}
        (target / '.abqaryno-requirements.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        (public / 'css' / 'style.css').write_text('\n* {\n    box-sizing: border-box;\n}\n\n:root {\n    --bg: #0b1020;\n    --panel: #121a2e;\n    --panel-2: #18233d;\n    --border: rgba(255,255,255,.10);\n    --text: #f5f7ff;\n    --muted: #aeb8d0;\n    --gold: #d9b45b;\n    --gold-2: #f0d58a;\n}\n\nbody {\n    margin: 0;\n    min-height: 100vh;\n    background:\n        radial-gradient(circle at top right, rgba(217,180,91,.12), transparent 30%),\n        linear-gradient(145deg, #080c18, var(--bg));\n    color: var(--text);\n    font-family: Arial, "Noto Sans Arabic", sans-serif;\n    direction: rtl;\n}\n\nheader {\n    padding: 28px 20px;\n    text-align: center;\n    border-bottom: 1px solid var(--border);\n    background: rgba(10,15,30,.88);\n}\n\nheader h1 {\n    margin: 0 0 8px;\n    font-size: clamp(24px, 5vw, 38px);\n}\n\nheader p {\n    margin: 0;\n    color: var(--muted);\n}\n\n.brand-logo-wrap {\n    display: flex;\n    flex-direction: column;\n    align-items: center;\n    gap: 10px;\n    margin-bottom: 18px;\n}\n\n.logo-button {\n    width: 92px;\n    height: 92px;\n    padding: 0;\n    border: 2px solid rgba(217,180,91,.55);\n    border-radius: 50%;\n    overflow: hidden;\n    background: linear-gradient(145deg,#18233d,#0d1424);\n    color: var(--gold-2);\n    cursor: pointer;\n    display: flex;\n    align-items: center;\n    justify-content: center;\n    box-shadow: 0 12px 30px rgba(0,0,0,.28);\n}\n\n.logo-button:hover {\n    transform: scale(1.04);\n    border-color: var(--gold-2);\n}\n\n.logo-placeholder {\n    font-size: 38px;\n}\n\n.logo-image {\n    width: 100%;\n    height: 100%;\n    object-fit: cover;\n    display: none;\n}\n\n.logo-actions {\n    display: flex;\n    gap: 8px;\n    flex-wrap: wrap;\n    justify-content: center;\n}\n\n.logo-actions button {\n    border: 1px solid rgba(217,180,91,.35);\n    border-radius: 10px;\n    padding: 7px 12px;\n    background: rgba(217,180,91,.10);\n    color: var(--gold-2);\n    cursor: pointer;\n}\n\n.logo-actions button:hover {\n    background: rgba(217,180,91,.18);\n}\n\n@media (max-width: 600px) {\n    .logo-button {\n        width: 82px;\n        height: 82px;\n    }\n}\n\nmain {\n    width: min(1100px, calc(100% - 28px));\n    margin: 28px auto 50px;\n}\n\n.screen {\n    padding: 20px;\n    margin-bottom: 16px;\n    border: 1px solid var(--border);\n    border-radius: 18px;\n    background: rgba(18,26,46,.82);\n    box-shadow: 0 12px 35px rgba(0,0,0,.20);\n}\n\n.screen h2 {\n    margin-top: 0;\n    color: var(--gold-2);\n}\n\n.tools-panel {\n    display: grid;\n    grid-template-columns: repeat(2, minmax(0, 1fr));\n    gap: 18px;\n    margin-top: 24px;\n}\n\n.tool-card {\n    padding: 20px;\n    border: 1px solid var(--border);\n    border-radius: 20px;\n    background: linear-gradient(160deg, rgba(24,35,61,.96), rgba(15,22,40,.96));\n    box-shadow: 0 15px 40px rgba(0,0,0,.24);\n}\n\n.tool-card h2 {\n    margin: 0 0 16px;\n    color: var(--gold-2);\n    font-size: 21px;\n}\n\n.chat-messages {\n    min-height: 150px;\n    max-height: 300px;\n    overflow-y: auto;\n    padding: 12px;\n    margin-bottom: 12px;\n    border: 1px solid var(--border);\n    border-radius: 14px;\n    background: rgba(0,0,0,.16);\n}\n\n.chat-message {\n    width: fit-content;\n    max-width: 85%;\n    margin: 7px 0;\n    padding: 10px 14px;\n    border-radius: 14px;\n    background: var(--panel-2);\n    border: 1px solid var(--border);\n    word-break: break-word;\n}\n\n.chat-input-row {\n    display: flex;\n    gap: 8px;\n}\n\ninput[type="text"],\ninput[type="file"] {\n    width: 100%;\n    min-height: 46px;\n    padding: 10px 13px;\n    border: 1px solid var(--border);\n    border-radius: 12px;\n    background: rgba(0,0,0,.22);\n    color: var(--text);\n    outline: none;\n}\n\nbutton {\n    min-height: 44px;\n    padding: 10px 16px;\n    border: 1px solid rgba(217,180,91,.45);\n    border-radius: 12px;\n    background: linear-gradient(135deg, var(--gold), var(--gold-2));\n    color: #15110a;\n    font-weight: 700;\n    cursor: pointer;\n}\n\nbutton:hover {\n    filter: brightness(1.08);\n}\n\n.tool-actions {\n    display: flex;\n    flex-wrap: wrap;\n    gap: 8px;\n}\n\n#camera-preview {\n    display: block;\n    width: 100%;\n    min-height: 220px;\n    max-height: 420px;\n    margin-bottom: 14px;\n    object-fit: cover;\n    border-radius: 16px;\n    background: #050811;\n    border: 1px solid var(--border);\n}\n\n#recorded-audio {\n    width: 100%;\n    margin-top: 16px;\n}\n\n#attachment-list {\n    display: grid;\n    gap: 8px;\n    margin-top: 14px;\n}\n\n.attachment-item {\n    padding: 11px 13px;\n    border: 1px solid var(--border);\n    border-radius: 12px;\n    background: rgba(0,0,0,.16);\n    color: var(--muted);\n    word-break: break-word;\n}\n\n@media (max-width: 760px) {\n    main {\n        width: min(100% - 18px, 680px);\n    }\n\n    .tools-panel {\n        grid-template-columns: 1fr;\n    }\n\n    .chat-input-row {\n        flex-direction: column;\n    }\n\n    .chat-input-row button {\n        width: 100%;\n    }\n\n    .tool-actions button {\n        flex: 1 1 140px;\n    }\n}\n', encoding='utf-8')
        (public / 'project.json').write_text(json.dumps({'name': name, 'idea': idea, 'created_at': manifest['created_at'], 'features': requirements.get('features', []), 'screens': approved_screens, 'options': options}, ensure_ascii=False, indent=2), encoding='utf-8')
        (public / 'js' / 'app.js').write_text('const AbqarynoAPI = {\n    async request(path, options = {}) {\n        const response = await fetch(path, {\n            headers: {\n                "Content-Type": "application/json",\n                ...(options.headers || {})\n            },\n            ...options\n        });\n\n        let data = {};\n        try {\n            data = await response.json();\n        } catch (error) {\n            data = {\n                ok: false,\n                error: "استجابة API غير صالحة."\n            };\n        }\n\n        if (!response.ok) {\n            const error = new Error(\n                data.error || `HTTP ${response.status}`\n            );\n            error.status = response.status;\n            error.data = data;\n            throw error;\n        }\n\n        return data;\n    },\n\n    health() {\n        return this.request("/api/health");\n    },\n\n    search(query, items = []) {\n        return this.request("/api/search", {\n            method: "POST",\n            body: JSON.stringify({\n                query,\n                items\n            })\n        });\n    },\n\n    report(title, data = {}) {\n        return this.request("/api/advanced_reports", {\n            method: "POST",\n            body: JSON.stringify({\n                title,\n                data\n            })\n        });\n    },\n\n    ocr(data = {}) {\n        return this.request("/api/ocr", {\n            method: "POST",\n            body: JSON.stringify(data)\n        });\n    },\n\n    translation(data = {}) {\n        return this.request("/api/translation", {\n            method: "POST",\n            body: JSON.stringify(data)\n        });\n    },\n\n    voice(data = {}) {\n        return this.request("/api/voice", {\n            method: "POST",\n            body: JSON.stringify(data)\n        });\n    }\n};\n\nwindow.abqarynoAPI = AbqarynoAPI;\n\nfunction optionIds(project) {\n    return (project.options || [])\n        .map(option => {\n            if (typeof option === "string") {\n                return option;\n            }\n            return option && option.option_id;\n        })\n        .filter(Boolean);\n}\n\nfunction createServicePanel(project) {\n    const ids = optionIds(project);\n\n    if (!ids.length) {\n        return;\n    }\n\n    const main = document.querySelector("main");\n\n    if (!main) {\n        return;\n    }\n\n    if (document.getElementById("abqaryno-api-tools")) {\n        return;\n    }\n\n    const panel = document.createElement("section");\n    panel.id = "abqaryno-api-tools";\n    panel.className = "tools-panel";\n\n    panel.innerHTML = `\n        <div class="tool-card">\n            <h3>🔌 خدمات البرنامج</h3>\n            <p>الخدمات التي تم اختيارها أثناء إنشاء المشروع.</p>\n            <div id="abqaryno-api-status">جاري فحص الاتصال...</div>\n        </div>\n    `;\n\n    if (ids.includes("search")) {\n        const card = document.createElement("div");\n        card.className = "tool-card";\n        card.innerHTML = `\n            <h3>🔎 البحث</h3>\n            <input id="abqaryno-api-search-input"\n                   type="text"\n                   placeholder="اكتب عبارة البحث...">\n            <button id="abqaryno-api-search-button" type="button">\n                بحث\n            </button>\n            <div id="abqaryno-api-search-results"></div>\n        `;\n        panel.appendChild(card);\n    }\n\n    if (ids.includes("advanced_reports")) {\n        const card = document.createElement("div");\n        card.className = "tool-card";\n        card.innerHTML = `\n            <h3>📊 التقارير</h3>\n            <input id="abqaryno-api-report-title"\n                   type="text"\n                   placeholder="عنوان التقرير">\n            <button id="abqaryno-api-report-button" type="button">\n                إنشاء تقرير\n            </button>\n            <div id="abqaryno-api-report-result"></div>\n        `;\n        panel.appendChild(card);\n    }\n\n    for (const [id, label] of [\n        ["ocr", "📄 OCR"],\n        ["translation", "🌐 الترجمة"],\n        ["voice", "🎙️ الصوت"]\n    ]) {\n        if (!ids.includes(id)) {\n            continue;\n        }\n\n        const card = document.createElement("div");\n        card.className = "tool-card";\n        card.innerHTML = `\n            <h3>${label}</h3>\n            <p>الخدمة موجودة في المشروع، لكن محركها غير موصل بعد.</p>\n        `;\n        panel.appendChild(card);\n    }\n\n    main.appendChild(panel);\n\n    const searchButton = document.getElementById(\n        "abqaryno-api-search-button"\n    );\n\n    if (searchButton) {\n        searchButton.addEventListener("click", async () => {\n            const input = document.getElementById(\n                "abqaryno-api-search-input"\n            );\n            const output = document.getElementById(\n                "abqaryno-api-search-results"\n            );\n\n            const query = String(\n                input ? input.value : ""\n            ).trim();\n\n            if (!query) {\n                output.textContent = "اكتب عبارة البحث أولًا.";\n                return;\n            }\n\n            output.textContent = "جاري البحث...";\n\n            try {\n                const result = await AbqarynoAPI.search(\n                    query,\n                    []\n                );\n\n                output.textContent = (\n                    result.results || []\n                ).join("، ") || "لا توجد نتائج.";\n            } catch (error) {\n                output.textContent =\n                    error.data?.error ||\n                    error.message ||\n                    "تعذر تنفيذ البحث.";\n            }\n        });\n    }\n\n    const reportButton = document.getElementById(\n        "abqaryno-api-report-button"\n    );\n\n    if (reportButton) {\n        reportButton.addEventListener("click", async () => {\n            const input = document.getElementById(\n                "abqaryno-api-report-title"\n            );\n            const output = document.getElementById(\n                "abqaryno-api-report-result"\n            );\n\n            const title = String(\n                input ? input.value : ""\n            ).trim();\n\n            if (!title) {\n                output.textContent = "اكتب عنوان التقرير أولًا.";\n                return;\n            }\n\n            output.textContent = "جاري إنشاء التقرير...";\n\n            try {\n                const result = await AbqarynoAPI.report(\n                    title,\n                    {}\n                );\n\n                output.textContent =\n                    result.title || "تم إنشاء التقرير.";\n            } catch (error) {\n                output.textContent =\n                    error.data?.error ||\n                    error.message ||\n                    "تعذر إنشاء التقرير.";\n            }\n        });\n    }\n}\n\nasync function loadProject() {\n    try {\n        const response = await fetch("/project.json");\n        const project = await response.json();\n\n        const container = document.querySelector("main");\n\n        if (!container) {\n            return;\n        }\n\n        container.dataset.project = project.name || "";\n\n        createServicePanel(project);\n\n        try {\n            const health = await AbqarynoAPI.health();\n            const status = document.getElementById(\n                "abqaryno-api-status"\n            );\n\n            if (status) {\n                status.textContent = health.ok\n                    ? "متصل بخدمات البرنامج."\n                    : "الخدمة غير متاحة.";\n            }\n        } catch (error) {\n            const status = document.getElementById(\n                "abqaryno-api-status"\n            );\n\n            if (status) {\n                status.textContent =\n                    "تعذر الاتصال بخدمات البرنامج.";\n            }\n        }\n\n        console.log(\n            "تم تحميل مشروع عبقرينو:",\n            project.name\n        );\n    } catch (error) {\n        console.error(\n            "تعذر تحميل مواصفات المشروع:",\n            error\n        );\n    }\n}\n\ndocument.addEventListener(\n    "DOMContentLoaded",\n    loadProject\n);\n', encoding='utf-8')
        js_dir = public / 'js'
        (js_dir / 'chat.js').write_text('class AbqarynoChat {\n    constructor() {\n        this.messages = [];\n    }\n\n    send(message) {\n        const text = String(message || "").trim();\n\n        if (!text) {\n            return null;\n        }\n\n        const item = {\n            id: Date.now(),\n            text,\n            created_at: new Date().toISOString()\n        };\n\n        this.messages.push(item);\n\n        document.dispatchEvent(\n            new CustomEvent("abqaryno:message", {\n                detail: item\n            })\n        );\n\n        return item;\n    }\n\n    getMessages() {\n        return [...this.messages];\n    }\n}\n\nwindow.AbqarynoChat = AbqarynoChat;\nwindow.abqarynoChat = new AbqarynoChat();\n', encoding='utf-8')
        (js_dir / 'camera.js').write_text('class AbqarynoCamera {\n    constructor() {\n        this.stream = null;\n    }\n\n    async start(videoElement) {\n        if (!navigator.mediaDevices?.getUserMedia) {\n            throw new Error("الكاميرا غير مدعومة في هذا المتصفح");\n        }\n\n        this.stream = await navigator.mediaDevices.getUserMedia({\n            video: true,\n            audio: false\n        });\n\n        if (videoElement) {\n            videoElement.srcObject = this.stream;\n            videoElement.autoplay = true;\n            videoElement.playsInline = true;\n        }\n\n        return this.stream;\n    }\n\n    stop() {\n        if (!this.stream) {\n            return;\n        }\n\n        this.stream.getTracks().forEach(\n            track => track.stop()\n        );\n\n        this.stream = null;\n    }\n}\n\nwindow.AbqarynoCamera = AbqarynoCamera;\n', encoding='utf-8')
        (js_dir / 'microphone.js').write_text('class AbqarynoMicrophone {\n    constructor() {\n        this.stream = null;\n        this.recorder = null;\n        this.chunks = [];\n    }\n\n    async start() {\n        if (!navigator.mediaDevices?.getUserMedia) {\n            throw new Error("المايك غير مدعوم في هذا المتصفح");\n        }\n\n        this.stream = await navigator.mediaDevices.getUserMedia({\n            audio: true\n        });\n\n        return this.stream;\n    }\n\n    record() {\n        if (!this.stream) {\n            throw new Error("شغّل المايك أولًا");\n        }\n\n        this.chunks = [];\n        this.recorder = new MediaRecorder(this.stream);\n\n        this.recorder.ondataavailable = event => {\n            if (event.data.size > 0) {\n                this.chunks.push(event.data);\n            }\n        };\n\n        this.recorder.start();\n    }\n\n    stopRecording() {\n        return new Promise(resolve => {\n            if (!this.recorder) {\n                resolve(null);\n                return;\n            }\n\n            this.recorder.onstop = () => {\n                const blob = new Blob(\n                    this.chunks,\n                    { type: "audio/webm" }\n                );\n\n                resolve(blob);\n            };\n\n            this.recorder.stop();\n        });\n    }\n\n    stop() {\n        if (this.stream) {\n            this.stream.getTracks().forEach(\n                track => track.stop()\n            );\n        }\n\n        this.stream = null;\n        this.recorder = null;\n    }\n}\n\nwindow.AbqarynoMicrophone = AbqarynoMicrophone;\n', encoding='utf-8')
        (js_dir / 'attachments.js').write_text('class AbqarynoAttachments {\n    constructor() {\n        this.files = [];\n    }\n\n    add(fileList) {\n        const files = Array.from(fileList || []);\n\n        this.files.push(...files);\n\n        document.dispatchEvent(\n            new CustomEvent("abqaryno:attachments", {\n                detail: files\n            })\n        );\n\n        return files;\n    }\n\n    clear() {\n        this.files = [];\n    }\n\n    getFiles() {\n        return [...this.files];\n    }\n}\n\nwindow.AbqarynoAttachments = AbqarynoAttachments;\nwindow.abqarynoAttachments = new AbqarynoAttachments();\n', encoding='utf-8')
        scripts = ['app.js']
        feature_text = ' '.join((str(x) for x in requirements.get('features', [])))
        screen_text = ' '.join((str(x) for x in approved_screens))
        combined = f'{feature_text} {screen_text}'
        if any((x in combined for x in ['الرسائل', 'شات', 'محادثة'])):
            scripts.append('chat.js')
        if any((x in combined for x in ['الكاميرا', 'فيديو'])):
            scripts.append('camera.js')
        if any((x in combined for x in ['المايك', 'الصوت', 'تسجيل'])):
            scripts.append('microphone.js')
        if any((x in combined for x in ['الملفات', 'مرفقات', 'إرفاق'])):
            scripts.append('attachments.js')
        script_tags = '\n'.join((f'<script src="/js/{name}"></script>' for name in scripts))
        page = page.replace('</body>', f'{script_tags}\n</body>')
        (public / 'index.html').write_text(page, encoding='utf-8')
        option_ids = {str(option.get('option_id', '')).strip() for option in options if isinstance(option, dict)}
        server_template = 'from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler\nfrom pathlib import Path\nfrom urllib.parse import urlparse, parse_qs\nfrom email.parser import BytesParser\nfrom email.policy import default\nfrom datetime import datetime, timezone\nimport json\nimport os\nimport sqlite3\nimport uuid\nimport sys\n\nROOT = Path(__file__).resolve().parents[1]\nPUBLIC = ROOT / "public"\nDATABASE_DIR = ROOT / "database"\nDATABASE = DATABASE_DIR / "app.db"\nUPLOADS = ROOT / "uploads"\n\nsys.path.insert(0, str(ROOT))\n\nDATABASE_DIR.mkdir(parents=True, exist_ok=True)\nUPLOADS.mkdir(parents=True, exist_ok=True)\n\ndef now():\n    return datetime.now(timezone.utc).isoformat()\n\ndef connection():\n    db = sqlite3.connect(DATABASE)\n    db.row_factory = sqlite3.Row\n    db.execute("PRAGMA foreign_keys = ON")\n    return db\n\ndef initialize_database():\n    schema = (DATABASE_DIR / "schema.sql").read_text(encoding="utf-8")\n    with connection() as db:\n        db.executescript(schema)\n        db.commit()\n\ndef row_dict(row):\n    return dict(row) if row is not None else None\n\nclass GeneratedHandler(SimpleHTTPRequestHandler):\n\n    def send_json(self, payload, status=200):\n        body = json.dumps(\n            payload,\n            ensure_ascii=False,\n            default=str\n        ).encode("utf-8")\n\n        self.send_response(status)\n        self.send_header(\n            "Content-Type",\n            "application/json; charset=utf-8"\n        )\n        self.send_header(\n            "Content-Length",\n            str(len(body))\n        )\n        self.end_headers()\n        self.wfile.write(body)\n\n    def read_json(self):\n        length = int(\n            self.headers.get("Content-Length", "0") or 0\n        )\n        raw = self.rfile.read(length) if length else b"{}"\n\n        try:\n            return json.loads(raw.decode("utf-8"))\n        except (json.JSONDecodeError, UnicodeDecodeError):\n            return {}\n\n    def do_GET(self):\n        parsed = urlparse(self.path)\n        path = parsed.path\n        query = parse_qs(parsed.query)\n\n        if path == "/api/health":\n            return self.send_json({\n                "ok": True,\n                "service": "abqaryno-generated-api"\n            })\n\n        if path == "/api/consultations":\n            user_id = query.get("user_id", [None])[0]\n\n            sql = """\n                SELECT id, user_id, consultant_id,\n                       type, status, subject, created_at\n                FROM consultations\n            """\n            params = []\n\n            if user_id:\n                sql += " WHERE user_id = ?"\n                params.append(int(user_id))\n\n            sql += " ORDER BY id DESC"\n\n            with connection() as db:\n                rows = db.execute(sql, params).fetchall()\n\n            return self.send_json({\n                "ok": True,\n                "consultations": [row_dict(r) for r in rows]\n            })\n\n        if path == "/api/conversations":\n            conversation_id = query.get("id", [None])[0]\n            consultation_id = query.get("consultation_id", [None])[0]\n\n            with connection() as db:\n                if consultation_id:\n                    rows = db.execute(\n                        """\n                        SELECT id, consultation_id, title, created_at\n                        FROM conversations\n                        WHERE consultation_id = ?\n                        ORDER BY id\n                        """,\n                        (int(consultation_id),)\n                    ).fetchall()\n                elif conversation_id:\n                    rows = db.execute(\n                        """\n                        SELECT id, consultation_id, title, created_at\n                        FROM conversations\n                        WHERE id = ?\n                        """,\n                        (int(conversation_id),)\n                    ).fetchall()\n                else:\n                    return self.send_json({\n                        "ok": False,\n                        "error": "consultation_id أو id مطلوب"\n                    }, 400)\n\n            return self.send_json({\n                "ok": True,\n                "conversations": [row_dict(r) for r in rows]\n            })\n\n        if path == "/api/messages":\n            conversation_id = query.get("conversation_id", [None])[0]\n\n            if not conversation_id:\n                return self.send_json({\n                    "ok": False,\n                    "error": "conversation_id مطلوب"\n                }, 400)\n\n            with connection() as db:\n                rows = db.execute(\n                    """\n                    SELECT\n                        m.id,\n                        m.conversation_id,\n                        m.sender_id,\n                        u.name AS sender_name,\n                        m.message,\n                        m.created_at\n                    FROM messages m\n                    LEFT JOIN users u ON u.id = m.sender_id\n                    WHERE m.conversation_id = ?\n                    ORDER BY m.id\n                    """,\n                    (int(conversation_id),)\n                ).fetchall()\n\n            return self.send_json({\n                "ok": True,\n                "messages": [row_dict(r) for r in rows]\n            })\n\n        if path == "/api/documents":\n            conversation_id = query.get("conversation_id", [None])[0]\n\n            if not conversation_id:\n                return self.send_json({\n                    "ok": False,\n                    "error": "conversation_id مطلوب"\n                }, 400)\n\n            with connection() as db:\n                rows = db.execute(\n                    """\n                    SELECT id, conversation_id, uploaded_by,\n                           name, file_path, mime_type, created_at\n                    FROM documents\n                    WHERE conversation_id = ?\n                    ORDER BY id\n                    """,\n                    (int(conversation_id),)\n                ).fetchall()\n\n            return self.send_json({\n                "ok": True,\n                "documents": [row_dict(r) for r in rows]\n            })\n\n        return super().do_GET()\n\n    def do_POST(self):\n        path = urlparse(self.path).path\n\n        if path == "/api/users":\n            data = self.read_json()\n            name = str(data.get("name", "")).strip()\n\n            if not name:\n                return self.send_json({\n                    "ok": False,\n                    "error": "name مطلوب"\n                }, 400)\n\n            with connection() as db:\n                cur = db.execute(\n                    """\n                    INSERT INTO users\n                    (name, email, phone, password_hash, created_at)\n                    VALUES (?, ?, ?, ?, ?)\n                    """,\n                    (\n                        name,\n                        data.get("email"),\n                        data.get("phone"),\n                        data.get("password_hash"),\n                        now()\n                    )\n                )\n                db.commit()\n\n            return self.send_json({\n                "ok": True,\n                "user": {\n                    "id": cur.lastrowid,\n                    "name": name\n                }\n            }, 201)\n\n        if path == "/api/consultations":\n            data = self.read_json()\n\n            user_id = data.get("user_id")\n            consultation_type = str(\n                data.get("type", "")\n            ).strip().lower()\n\n            if not user_id:\n                return self.send_json({\n                    "ok": False,\n                    "error": "user_id مطلوب"\n                }, 400)\n\n            if consultation_type not in {"free", "private"}:\n                return self.send_json({\n                    "ok": False,\n                    "error": "type يجب أن يكون free أو private"\n                }, 400)\n\n            with connection() as db:\n                cur = db.execute(\n                    """\n                    INSERT INTO consultations\n                    (user_id, consultant_id, type, status,\n                     subject, created_at)\n                    VALUES (?, ?, ?, ?, ?, ?)\n                    """,\n                    (\n                        int(user_id),\n                        data.get("consultant_id"),\n                        consultation_type,\n                        "open",\n                        data.get("subject"),\n                        now()\n                    )\n                )\n\n                consultation_id = cur.lastrowid\n\n                conv = db.execute(\n                    """\n                    INSERT INTO conversations\n                    (consultation_id, title, created_at)\n                    VALUES (?, ?, ?)\n                    """,\n                    (\n                        consultation_id,\n                        data.get("subject") or "محادثة الاستشارة",\n                        now()\n                    )\n                )\n\n                conversation_id = conv.lastrowid\n                db.commit()\n\n            return self.send_json({\n                "ok": True,\n                "consultation": {\n                    "id": consultation_id,\n                    "type": consultation_type,\n                    "status": "open"\n                },\n                "conversation": {\n                    "id": conversation_id\n                }\n            }, 201)\n\n        if path == "/api/messages":\n            data = self.read_json()\n\n            conversation_id = data.get("conversation_id")\n            sender_id = data.get("sender_id")\n            message = str(data.get("message", "")).strip()\n\n            if not conversation_id or not sender_id or not message:\n                return self.send_json({\n                    "ok": False,\n                    "error": "conversation_id و sender_id و message مطلوبة"\n                }, 400)\n\n            with connection() as db:\n                cur = db.execute(\n                    """\n                    INSERT INTO messages\n                    (conversation_id, sender_id, message, created_at)\n                    VALUES (?, ?, ?, ?)\n                    """,\n                    (\n                        int(conversation_id),\n                        int(sender_id),\n                        message,\n                        now()\n                    )\n                )\n                db.commit()\n\n                row = db.execute(\n                    """\n                    SELECT\n                        m.id,\n                        m.conversation_id,\n                        m.sender_id,\n                        u.name AS sender_name,\n                        m.message,\n                        m.created_at\n                    FROM messages m\n                    LEFT JOIN users u ON u.id = m.sender_id\n                    WHERE m.id = ?\n                    """,\n                    (cur.lastrowid,)\n                ).fetchone()\n\n            return self.send_json({\n                "ok": True,\n                "message": row_dict(row)\n            }, 201)\n\n        if path == "/api/documents":\n            content_type = self.headers.get("Content-Type", "")\n\n            if not content_type.startswith("multipart/form-data"):\n                return self.send_json({\n                    "ok": False,\n                    "error": "رفع الملفات يحتاج multipart/form-data"\n                }, 400)\n\n            length = int(\n                self.headers.get("Content-Length", "0") or 0\n            )\n            raw = self.rfile.read(length)\n\n            header = (\n                b"Content-Type: " +\n                content_type.encode("utf-8") +\n                b"\\r\\nMIME-Version: 1.0\\r\\n\\r\\n"\n            )\n\n            message = BytesParser(\n                policy=default\n            ).parsebytes(header + raw)\n\n            fields = {}\n            uploaded = None\n\n            for part in message.iter_parts():\n                name = part.get_param(\n                    "name",\n                    header="Content-Disposition"\n                )\n                filename = part.get_filename()\n                payload = part.get_payload(decode=True) or b""\n\n                if filename:\n                    uploaded = (\n                        filename,\n                        part.get_content_type(),\n                        payload\n                    )\n                elif name:\n                    fields[name] = payload.decode(\n                        "utf-8",\n                        errors="replace"\n                    )\n\n            if uploaded is None:\n                return self.send_json({\n                    "ok": False,\n                    "error": "لم يتم إرسال ملف"\n                }, 400)\n\n            conversation_id = fields.get("conversation_id")\n            uploaded_by = fields.get("uploaded_by")\n\n            if not conversation_id or not uploaded_by:\n                return self.send_json({\n                    "ok": False,\n                    "error": "conversation_id و uploaded_by مطلوبان"\n                }, 400)\n\n            original_name, mime_type, payload = uploaded\n\n            safe_name = (\n                uuid.uuid4().hex +\n                "_" +\n                Path(original_name).name\n            )\n\n            file_path = UPLOADS / safe_name\n            file_path.write_bytes(payload)\n\n            with connection() as db:\n                cur = db.execute(\n                    """\n                    INSERT INTO documents\n                    (conversation_id, uploaded_by, name,\n                     file_path, mime_type, created_at)\n                    VALUES (?, ?, ?, ?, ?, ?)\n                    """,\n                    (\n                        int(conversation_id),\n                        int(uploaded_by),\n                        original_name,\n                        str(file_path.relative_to(ROOT)),\n                        mime_type,\n                        now()\n                    )\n                )\n                db.commit()\n\n            return self.send_json({\n                "ok": True,\n                "document": {\n                    "id": cur.lastrowid,\n                    "name": original_name,\n                    "mime_type": mime_type,\n                    "file_path": str(file_path.relative_to(ROOT))\n                }\n            }, 201)\n\n        return self.send_json({\n            "ok": False,\n            "error": "API not found"\n        }, 404)\n\n\ninitialize_database()\n\nos.chdir(PUBLIC)\n\nserver = ThreadingHTTPServer(\n    ("127.0.0.1", 8080),\n    GeneratedHandler\n)\n\nprint("Generated project: http://127.0.0.1:8080")\nserver.serve_forever()\n'
        (target / 'server' / 'server.py').write_text(server_template, encoding='utf-8')
        (target / 'routes' / '__init__.py').write_text('', encoding='utf-8')
        (target / 'services' / '__init__.py').write_text('', encoding='utf-8')
        database_dir = target / 'database'
        schema_sql = DatabaseEngine().schema(requirements)
        (database_dir / 'schema.sql').write_text(schema_sql, encoding='utf-8')
        database_py = 'from pathlib import Path\nimport sqlite3\n\nDATABASE = Path(__file__).resolve().parent / "app.db"\nSCHEMA = Path(__file__).resolve().parent / "schema.sql"\n\n\ndef get_connection():\n    connection = sqlite3.connect(DATABASE)\n    connection.row_factory = sqlite3.Row\n    connection.execute("PRAGMA foreign_keys = ON")\n    return connection\n\n\ndef initialize():\n    schema = SCHEMA.read_text(encoding="utf-8")\n\n    with get_connection() as connection:\n        connection.executescript(schema)\n        connection.commit()\n\n    return DATABASE\n\n\nif __name__ == "__main__":\n    path = initialize()\n    print(f"Database initialized: {path}")\n'
        (database_dir / 'database.py').write_text(database_py, encoding='utf-8')
        (database_dir / 'README.md').write_text('# قاعدة بيانات المشروع\\n\\n- app.db — قاعدة SQLite الفعلية\\n- schema.sql — مخطط قاعدة البيانات\\n- database.py — تهيئة والاتصال بقاعدة البيانات\\n', encoding='utf-8')
        import sqlite3
        database_file = database_dir / 'app.db'

        # كل توليد جديد يجب أن يبدأ بقاعدة بيانات مطابقة
        # للمخطط الحالي، وليس بقاعدة قديمة من توليد سابق.
        if database_file.exists():
            database_file.unlink()

        with sqlite3.connect(database_file) as connection:
            connection.executescript(schema_sql)
            connection.commit()
        (target / 'uploads' / '.gitkeep').write_text('', encoding='utf-8')
        if 'ocr' in option_ids:
            (target / 'services' / 'ocr.py').write_text('from pathlib import Path\nimport subprocess\n\n\nclass OCRService:\n    """خدمة OCR اختيارية للمشروع الناتج."""\n\n    def extract_text(self, image_path, language="eng"):\n        image_path = Path(image_path)\n\n        if not image_path.exists():\n            raise FileNotFoundError(f"ملف الصورة غير موجود: {image_path}")\n\n        try:\n            result = subprocess.run(\n                [\n                    "tesseract",\n                    str(image_path),\n                    "stdout",\n                    "-l",\n                    str(language or "eng"),\n                ],\n                capture_output=True,\n                text=True,\n                check=True,\n            )\n        except FileNotFoundError as exc:\n            raise RuntimeError("Tesseract OCR غير مثبت في بيئة التشغيل.") from exc\n        except subprocess.CalledProcessError as exc:\n            message = exc.stderr.strip() or "فشل استخراج النص من الصورة."\n            raise RuntimeError(message) from exc\n\n        return result.stdout.strip()\n\n\ndef extract_text(image_path, language="eng"):\n    return OCRService().extract_text(image_path, language)\n', encoding='utf-8')
            (target / 'routes' / 'ocr.py').write_text('from pathlib import Path\n\nfrom services.ocr import OCRService\n\n\ndef extract_uploaded_image(image_path, language="eng"):\n    return OCRService().extract_text(\n        Path(image_path),\n        language,\n    )\n', encoding='utf-8')
            (target / 'OCR.md').write_text('# OCR\n\nتمت إضافة خدمة OCR لأن خيار OCR تم اختياره أثناء إنشاء المشروع.\n\nالخدمة موجودة في services/ocr.py.\nالمسار المساعد موجود في routes/ocr.py.\nتحتاج بيئة التشغيل إلى Tesseract OCR.\n', encoding='utf-8')
        if 'translation' in option_ids:
            (target / 'services' / 'translation.py').write_text('from dataclasses import dataclass\n\n\n@dataclass\nclass TranslationResult:\n    source_text: str\n    source_language: str\n    target_language: str\n    translated_text: str\n\n\nclass TranslationService:\n    """خدمة ترجمة اختيارية للمشروع الناتج."""\n\n    def translate(\n        self,\n        source_text,\n        source_language="auto",\n        target_language="ar",\n    ):\n        source_text = str(source_text or "").strip()\n        source_language = str(source_language or "auto").strip()\n        target_language = str(target_language or "ar").strip()\n\n        if not source_text:\n            raise ValueError("النص المطلوب ترجمته فارغ.")\n\n        raise RuntimeError(\n            "محرك الترجمة غير موصل بعد. الخدمة جاهزة للربط بمحرك ترجمة."\n        )\n\n\ndef translate(\n    source_text,\n    source_language="auto",\n    target_language="ar",\n):\n    return TranslationService().translate(\n        source_text,\n        source_language,\n        target_language,\n    )\n', encoding='utf-8')
            (target / 'routes' / 'translation.py').write_text('from services.translation import TranslationService\n\n\ndef translate_text(\n    source_text,\n    source_language="auto",\n    target_language="ar",\n):\n    return TranslationService().translate(\n        source_text,\n        source_language,\n        target_language,\n    )\n', encoding='utf-8')
            (target / 'TRANSLATION.md').write_text('# Translation\n\nتمت إضافة خدمة الترجمة لأن خيار Translation تم اختياره أثناء إنشاء المشروع.\n\nالخدمة موجودة في services/translation.py.\nالمسار المساعد موجود في routes/translation.py.\nمحرك الترجمة يحتاج إلى الربط بمزود ترجمة عند تشغيله.\n', encoding='utf-8')
        if 'voice' in option_ids:
            (target / 'services' / 'voice.py').write_text('from pathlib import Path\nimport subprocess\n\n\nclass VoiceService:\n    """خدمة الصوت الاختيارية للمشروع الناتج."""\n\n    def transcribe(self, audio_path, language="ar"):\n        audio_path = Path(audio_path)\n\n        if not audio_path.exists():\n            raise FileNotFoundError(\n                f"ملف الصوت غير موجود: {audio_path}"\n            )\n\n        raise RuntimeError(\n            "محرك تحويل الصوت إلى نص غير موصل بعد. "\n            "الخدمة جاهزة للربط بمحرك STT."\n        )\n\n    def synthesize(self, text, language="ar", output_path=None):\n        text = str(text or "").strip()\n\n        if not text:\n            raise ValueError("النص المطلوب تحويله إلى صوت فارغ.")\n\n        raise RuntimeError(\n            "محرك تحويل النص إلى صوت غير موصل بعد. "\n            "الخدمة جاهزة للربط بمحرك TTS."\n        )\n\n\ndef transcribe(audio_path, language="ar"):\n    return VoiceService().transcribe(audio_path, language)\n\n\ndef synthesize(text, language="ar", output_path=None):\n    return VoiceService().synthesize(\n        text,\n        language,\n        output_path,\n    )\n', encoding='utf-8')
            (target / 'routes' / 'voice.py').write_text('from services.voice import VoiceService\n\n\ndef transcribe_audio(audio_path, language="ar"):\n    return VoiceService().transcribe(\n        audio_path,\n        language,\n    )\n\n\ndef synthesize_text(\n    text,\n    language="ar",\n    output_path=None,\n):\n    return VoiceService().synthesize(\n        text,\n        language,\n        output_path,\n    )\n', encoding='utf-8')
            (target / 'VOICE.md').write_text('# Voice\n\nتمت إضافة خدمة الصوت لأن خيار Voice تم اختياره أثناء إنشاء المشروع.\n\nالخدمة موجودة في services/voice.py.\nالمسار المساعد موجود في routes/voice.py.\nالخدمة جاهزة للربط بمحركات STT وTTS.\n', encoding='utf-8')
        if 'search' in option_ids:
            (target / 'services' / 'search.py').write_text('from dataclasses import dataclass\n\n\n@dataclass\nclass SearchResult:\n    query: str\n    results: list\n\n\nclass SearchService:\n    """خدمة البحث الاختيارية للمشروع الناتج."""\n\n    def search(self, query, items=None):\n        query = str(query or "").strip()\n\n        if not query:\n            raise ValueError("عبارة البحث مطلوبة.")\n\n        items = items or []\n        query_lower = query.casefold()\n\n        results = [\n            item\n            for item in items\n            if query_lower in str(item).casefold()\n        ]\n\n        return SearchResult(\n            query=query,\n            results=results,\n        )\n\n\ndef search(query, items=None):\n    return SearchService().search(query, items)\n', encoding='utf-8')
            (target / 'routes' / 'search.py').write_text('from services.search import SearchService\n\n\ndef search_items(query, items=None):\n    return SearchService().search(\n        query,\n        items,\n    )\n', encoding='utf-8')
            (target / 'SEARCH.md').write_text('# Search\\n\\nتمت إضافة خدمة البحث لأن خيار البحث تم اختياره أثناء إنشاء المشروع.\\n\\nالخدمة موجودة في services/search.py.\\nالمسار المساعد موجود في routes/search.py.\\n', encoding='utf-8')
        if 'advanced_reports' in option_ids:
            (target / 'services' / 'reports.py').write_text('from dataclasses import dataclass\nfrom datetime import datetime\n\n\n@dataclass\nclass ReportResult:\n    title: str\n    generated_at: str\n    data: dict\n\n\nclass ReportsService:\n    """خدمة التقارير المتقدمة الاختيارية للمشروع الناتج."""\n\n    def generate(self, title, data=None):\n        title = str(title or "").strip()\n\n        if not title:\n            raise ValueError("عنوان التقرير مطلوب.")\n\n        return ReportResult(\n            title=title,\n            generated_at=datetime.now().isoformat(),\n            data=data or {},\n        )\n\n\ndef generate_report(title, data=None):\n    return ReportsService().generate(title, data)\n', encoding='utf-8')
            (target / 'routes' / 'reports.py').write_text('from services.reports import ReportsService\n\n\ndef generate_report(title, data=None):\n    return ReportsService().generate(\n        title,\n        data,\n    )\n', encoding='utf-8')
            (target / 'REPORTS.md').write_text('# Advanced Reports\n\nتمت إضافة خدمة التقارير المتقدمة لأن الخيار تم اختياره أثناء إنشاء المشروع.\n\nالخدمة موجودة في services/reports.py.\nالمسار المساعد موجود في routes/reports.py.\n', encoding='utf-8')
        (target / 'README.md').write_text(f'# {idea}\n\nتم إنشاء هذا المشروع بواسطة عبقرينو Studio.\n\n## البنية\n\n- public — واجهة البرنامج\n- server — تشغيل المشروع\n- routes — مسارات التطبيق\n- services — الخدمات والمنطق\n- database — طبقة البيانات\n- uploads — الملفات المرفوعة\n- .abqaryno-requirements.json — المتطلبات والشاشات المعتمدة\n\n## التشغيل\n\npython server/server.py\n', encoding='utf-8')
        verification = CreationVerificationEngine().verify(target)
        manifest['verification'] = verification
        if verification['status'] != 'PASSED':
            manifest['creation_status'] = 'VERIFICATION_FAILED'
        else:
            manifest['creation_status'] = 'VERIFIED'
        (target / '.abqaryno-requirements.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        return (target, manifest)

class CreationVerificationEngine:
    """بوابة تحقق فعلية للمشاريع التي ينشئها عبقرينو."""
    NODE_REQUIRED_FILES = ('package.json', 'server.js', 'database/schema.sql', 'public/index.html')
    PYTHON_REQUIRED_FILES = ('README.md', 'public/index.html', 'public/css/style.css', 'public/js/app.js', 'server/server.py', 'database/schema.sql', 'database/database.py', 'database/app.db', '.abqaryno-requirements.json')

    @staticmethod
    def _run_http_check(url):
        import urllib.request
        request = urllib.request.Request(url, method='GET', headers={'User-Agent': 'Abqaryno-Verification/1.0'})
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read(4096).decode('utf-8', errors='replace')
            return {'status_code': response.status, 'body_bytes_checked': len(body)}

    @staticmethod
    def _detect_port(target):
        import json
        import re
        package_path = target / 'package.json'
        server_path = target / 'server.js'
        port = 3000
        if package_path.exists():
            try:
                package = json.loads(package_path.read_text(encoding='utf-8'))
                config_port = package.get('abqaryno', {}).get('port')
                if isinstance(config_port, int):
                    port = config_port
            except Exception:
                pass
        if server_path.exists():
            try:
                server_text = server_path.read_text(encoding='utf-8')
                matches = re.findall('listen\\s*\\(\\s*(?:process\\.env\\.\\w+\\s*\\|\\|\\s*)?(\\d+)', server_text)
                if matches:
                    port = int(matches[-1])
            except Exception:
                pass
        return port

    def _verify_node_project(self, target, checks):
        import json
        import shutil
        import subprocess
        import time
        missing = [item for item in self.NODE_REQUIRED_FILES if not (target / item).exists()]
        checks.append({'name': 'required_files', 'status': 'PASSED' if not missing else 'FAILED', 'missing': missing})
        if missing:
            return
        node = shutil.which('node')
        if not node:
            checks.append({'name': 'node_available', 'status': 'FAILED', 'error': 'node executable not found'})
            return
        syntax = subprocess.run([node, '--check', 'server.js'], cwd=target, text=True, capture_output=True, timeout=15)
        checks.append({'name': 'node_syntax', 'status': 'PASSED' if syntax.returncode == 0 else 'FAILED', 'exit_code': syntax.returncode, 'stdout': syntax.stdout[-2000:], 'stderr': syntax.stderr[-2000:]})
        if syntax.returncode != 0:
            return
        package_path = target / 'package.json'
        package = json.loads(package_path.read_text(encoding='utf-8'))
        dependencies = package.get('dependencies', {})
        if dependencies and (not (target / 'node_modules').exists()):
            npm = shutil.which('npm')
            if not npm:
                checks.append({'name': 'npm_dependencies', 'status': 'FAILED', 'error': 'npm executable not found'})
                return
            install = subprocess.run([npm, 'install', '--no-audit', '--no-fund'], cwd=target, text=True, capture_output=True, timeout=180)
            checks.append({'name': 'npm_dependencies', 'status': 'PASSED' if install.returncode == 0 else 'FAILED', 'exit_code': install.returncode, 'stdout': install.stdout[-3000:], 'stderr': install.stderr[-3000:]})
            if install.returncode != 0:
                return
        port = self._detect_port(target)
        process = None
        try:
            process = subprocess.Popen([node, 'server.js'], cwd=target, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            last_error = None
            http_result = None
            for _ in range(20):
                time.sleep(0.25)
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=2)
                    checks.append({'name': 'runtime_process', 'status': 'FAILED', 'exit_code': process.returncode, 'stdout': stdout[-3000:], 'stderr': stderr[-3000:]})
                    return
                try:
                    http_result = self._run_http_check(f'http://127.0.0.1:{port}/')
                    break
                except Exception as exc:
                    last_error = str(exc)
            if http_result is None:
                checks.append({'name': 'http_runtime', 'status': 'FAILED', 'port': port, 'error': last_error})
                return
            checks.append({'name': 'runtime_process', 'status': 'PASSED', 'port': port})
            checks.append({'name': 'http_runtime', 'status': 'PASSED' if 200 <= http_result['status_code'] < 500 else 'FAILED', 'port': port, **http_result})
        except Exception as exc:
            checks.append({'name': 'http_runtime', 'status': 'FAILED', 'error': str(exc)})
        finally:
            if process is not None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass

    def _verify_python_project(self, target, checks):
        import shutil
        import subprocess
        import time
        missing = [item for item in self.PYTHON_REQUIRED_FILES if not (target / item).exists()]
        checks.append({'name': 'required_files', 'status': 'PASSED' if not missing else 'FAILED', 'missing': missing})
        if missing:
            return
        python_executable = shutil.which('python3') or shutil.which('python')
        if not python_executable:
            checks.append({'name': 'python_available', 'status': 'FAILED', 'error': 'python/python3 executable not found'})
            return
        python_files = sorted(target.rglob('*.py'))
        python_errors = []
        for py_file in python_files:
            try:
                compile(py_file.read_text(encoding='utf-8'), str(py_file), 'exec')
            except Exception as exc:
                python_errors.append({'file': str(py_file.relative_to(target)), 'error': str(exc)})
        checks.append({'name': 'python_syntax', 'status': 'PASSED' if not python_errors else 'FAILED', 'files_checked': len(python_files), 'errors': python_errors})
        if python_errors:
            return
        database_status = 'PASSED'
        database_error = None
        try:
            import sqlite3
            database_file = target / 'database' / 'app.db'
            with sqlite3.connect(database_file) as connection:
                result = connection.execute('PRAGMA integrity_check').fetchone()
                if not result or result[0] != 'ok':
                    database_status = 'FAILED'
                    database_error = str(result)
        except Exception as exc:
            database_status = 'FAILED'
            database_error = str(exc)
        checks.append({'name': 'sqlite_integrity', 'status': database_status, 'error': database_error})
        if database_status != 'PASSED':
            return
        server_path = target / 'server' / 'server.py'
        if not server_path.exists():
            checks.append({'name': 'runtime_process', 'status': 'FAILED', 'error': 'Generated Python server not found'})
            return
        process = None
        port = 8080
        try:
            process = subprocess.Popen([python_executable, str(server_path)], cwd=target, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            last_error = None
            http_result = None
            for _ in range(20):
                time.sleep(0.25)
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=2)
                    checks.append({'name': 'runtime_process', 'status': 'FAILED', 'exit_code': process.returncode, 'stdout': stdout[-3000:], 'stderr': stderr[-3000:]})
                    return
                try:
                    http_result = self._run_http_check(f'http://127.0.0.1:{port}/')
                    break
                except Exception as exc:
                    last_error = str(exc)
            if http_result is None:
                checks.append({'name': 'http_runtime', 'status': 'FAILED', 'port': port, 'error': last_error})
                return
            checks.append({'name': 'runtime_process', 'status': 'PASSED', 'port': port})
            checks.append({'name': 'http_runtime', 'status': 'PASSED' if 200 <= http_result['status_code'] < 500 else 'FAILED', 'port': port, **http_result})
        except Exception as exc:
            checks.append({'name': 'http_runtime', 'status': 'FAILED', 'port': port, 'error': str(exc)})
        finally:
            if process is not None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass

    def verify(self, target):
        target = Path(target)
        checks = []
        if (target / 'server.js').exists():
            project_type = 'node'
            self._verify_node_project(target, checks)
        elif (target / 'server/server.py').exists():
            project_type = 'python'
            self._verify_python_project(target, checks)
        else:
            project_type = 'unknown'
            checks.append({'name': 'project_type', 'status': 'FAILED', 'error': 'No supported server entry point found'})
        failed = [check['name'] for check in checks if check['status'] != 'PASSED']
        return {'version': 2, 'project_type': project_type, 'status': 'FAILED' if failed else 'PASSED', 'checks': checks, 'failed_checks': failed}

class FinalReport:

    def write(self, root, target, manifest):
        reports = Path(root) / 'reports'
        reports.mkdir(parents=True, exist_ok=True)
        report = {'status': 'COMPLETED', 'time': now(), 'target': str(target), 'idea': manifest['idea'], 'approved_screen_count': len(manifest['approved_screens']), 'approved_screens': manifest['approved_screens']}
        path = reports / 'creation-final-report.json'
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        return path

def abqaryno_factory_build(project_generator, project_spec, output_dir, verifier=None):
    """
    Real creation pipeline:
    specification -> ProjectGenerator.generate -> generated project
    -> CreationVerificationEngine.verify
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = project_generator.generate(project_spec, output_dir)
    if not output_dir.exists():
        raise RuntimeError('Generated project directory was not created')
    files = [p for p in output_dir.rglob('*') if p.is_file()]
    if not files:
        raise RuntimeError('Factory reported generation but produced no files')
    verification = None
    if verifier is not None:
        verification = verifier.verify(output_dir)
    return {'status': 'PASS', 'output_dir': str(output_dir), 'files_created': len(files), 'verification': verification}
