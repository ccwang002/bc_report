from pathlib import Path
from bc_report.report import Stage
from ..base.report import BaseSummaryHomeStage

here = Path(__file__).parent


class RNASeqStageMixin(Stage):
    template_find_paths = [
        here / 'templates',
        *BaseSummaryHomeStage.template_find_paths,
    ]
