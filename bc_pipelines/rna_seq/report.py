from pathlib import Path
from ..base.report import BaseSummaryHomeStage, BaseReport
from ..base.fastqc import FastQCStage
from . import RNASeqStageMixin, here
from .star import STARStage
from .cufflinks import CufflinksStage


class RNASeqFastQCStage(RNASeqStageMixin, FastQCStage):
    template_entrances = ['rna_seq/fastqc.html']


class RNASeqSummaryHomeStage(RNASeqStageMixin, BaseSummaryHomeStage):
    template_entrances = ['rna_seq/index.html']


class RNASeqReport(BaseReport):
    stage_classes = [
        RNASeqSummaryHomeStage,
        RNASeqFastQCStage,
        STARStage,
        CufflinksStage,
    ]
    static_roots = [
        here / 'static',
        *BaseReport.static_roots,
    ]
