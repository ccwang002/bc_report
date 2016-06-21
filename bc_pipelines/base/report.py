from pathlib import Path
from bc_report.report import Report, Stage, SummaryStage

here = Path(__file__).parent


class BaseSummaryHomeStage(SummaryStage):
    template_entrances = ['index.html']
    template_find_paths = [
        here / 'templates',
    ]


class BaseReport(Report):
    stage_classes = [BaseSummaryHomeStage]
    static_roots = [
        here / 'static',
    ]
