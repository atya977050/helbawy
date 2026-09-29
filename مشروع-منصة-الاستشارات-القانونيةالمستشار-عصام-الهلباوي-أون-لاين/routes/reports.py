from services.reports import ReportsService


def generate_report(title, data=None):
    return ReportsService().generate(
        title,
        data,
    )
