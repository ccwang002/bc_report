from pathlib import Path
from bc_report.report import Stage
from ..base.report import BaseSummaryHomeStage, BaseReport
from ..base.fastqc import FastQCStage

here = Path(__file__).parent


class RNASeqStageMixin(Stage):
    template_find_paths = [
        here / 'templates',
        *BaseSummaryHomeStage.template_find_paths,
    ]


class RNASeqFastQCStage(RNASeqStageMixin, FastQCStage):
    template_entrances = ['rna_seq/fastqc.html']


class RNASeqSummaryHomeStage(RNASeqStageMixin, BaseSummaryHomeStage):
    template_entrances = ['rna_seq/index.html']


class RNASeqReport(BaseReport):
    stage_classes = [RNASeqSummaryHomeStage, RNASeqFastQCStage]
    static_roots = [
        here / 'static',
        *BaseReport.static_roots,
    ]
