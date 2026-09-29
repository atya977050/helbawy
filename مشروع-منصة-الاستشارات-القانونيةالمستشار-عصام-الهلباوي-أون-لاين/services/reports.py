from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReportResult:
    title: str
    generated_at: str
    data: dict


class ReportsService:
    """خدمة التقارير المتقدمة الاختيارية للمشروع الناتج."""

    def generate(self, title, data=None):
        title = str(title or "").strip()

        if not title:
            raise ValueError("عنوان التقرير مطلوب.")

        return ReportResult(
            title=title,
            generated_at=datetime.now().isoformat(),
            data=data or {},
        )


def generate_report(title, data=None):
    return ReportsService().generate(title, data)
