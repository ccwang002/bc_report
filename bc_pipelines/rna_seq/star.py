from pathlib import Path
from bc_report.info import AnalysisInfo
from bc_report import create_logger
from ..base.report import BaseStage
from . import RNASeqStageMixin

logger = create_logger(__name__)


class STARStage(RNASeqStageMixin, BaseStage):
    template_entrances = ['rna_seq/star.html']
    result_folder_name = 'STAR'

