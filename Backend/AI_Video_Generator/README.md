# Frame AI Video Studio — Professional API-powered edition

واجهة عربية لإنشاء فيديوهات باستخدام نماذج توليد الفيديو على Replicate. بخلاف العرض المحلي التجريبي، هذه النسخة ترسل الطلب إلى نموذج فيديو حقيقي وتعرض حالة التوليد ثم رابط الفيديو الناتج.

## المتطلبات

- Python 3.10 أو أحدث
- حساب Replicate ومفتاح API صالح
- اسم نموذج فيديو متاح لحسابك على Replicate

قد تُحتسب تكلفة على التوليد بحسب النموذج والمزوّد. راجع السعر وشروط النموذج قبل الاستخدام. لا تضع مفتاح API في الواجهة أو في Git.

## الإعداد والتشغيل

```bash
cd Backend/AI_Video_Generator
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

انسخ `.env.example` إلى `.env` ثم عيّن القيم:

```dotenv
REPLICATE_API_TOKEN=r8_...
REPLICATE_MODEL=owner/model
REPLICATE_INPUT_TEMPLATE_JSON={"prompt":"{{prompt}}","aspect_ratio":"{{aspect_ratio}}","duration":{{duration}}
```

عدّل قالب `REPLICATE_INPUT_TEMPLATE_JSON` ليتطابق تمامًا مع أسماء وأنواع الحقول التي يقبلها نموذجك. مثال: بعض النماذج لا تقبل `duration` أو `aspect_ratio`؛ احذف الحقول غير المدعومة. القيم المتاحة للاستبدال هي `{{prompt}}` و`{{aspect_ratio}}` و`{{duration}}`، ويمكن تضمين القالب في JSON. لا ترفع `.env` إلى المستودع.

ثم شغّل الخادم:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

افتح http://127.0.0.1:8000

## سير العمل والواجهات

- `POST /api/videos` ينشئ مهمة لدى Replicate ويرجع معرّفها.
- `GET /api/videos/{id}` يعيد الحالة والرابط عند انتهاء المهمة.
- `GET /docs` واجهة توثيق API.

تُرسل حالة المهمة مباشرة إلى Replicate ولا تحفظ قاعدة بيانات محلية. احتفظ برابط الإخراج قبل انتهاء صلاحية ملفات المزود. إعداد النموذج وحقول الإدخال يختلفان من نموذج لآخر.

## أمان وتشغيل الإنتاج

استخدم HTTPS، خزّن الرمز في مدير أسرار للبيئة المستضيفة، وأضف مصادقة وحدود معدل وقيود ميزانية قبل فتح التطبيق للعامة. لا تُعرّض الخادم على الإنترنت بإعداد التطوير `--reload`.
