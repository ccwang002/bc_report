from pathlib import Path
from ..base.report import BaseSummaryHomeStage, BaseReport

here = Path(__file__).parent


class RNASeqSummaryHomeStage(BaseSummaryHomeStage):
    template_find_paths = [
        here / 'templates',
        *BaseSummaryHomeStage.template_find_paths,
    ]
    template_entrances = ['rna_seq/index.html']


class RNASeqReport(BaseReport):
    stage_classes = [RNASeqSummaryHomeStage]
    static_roots = [
        here / 'static',
        *BaseReport.static_roots,
    ]
