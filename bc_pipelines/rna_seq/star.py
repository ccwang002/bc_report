from pathlib import Path
from bc_report.info import AnalysisInfo
from bc_report import create_logger
from ..base.report import BaseStage
from . import RNASeqStageMixin

logger = create_logger(__name__)


class STARStage(RNASeqStageMixin, BaseStage):
    template_entrances = ['rna_seq/star.html']
    result_folder_name = 'STAR'

    def parse(self, analysis_info: AnalysisInfo):
        data_info = super().parse(analysis_info)
        data_info['raw_output'] = self.collect_raw_output(analysis_info)
        return data_info

    def collect_raw_output(self, analysis_info: AnalysisInfo):
        raw_output_filenames = [
            'Aligned.sortedByCoord.out.bam',
            'Aligned.sortedByCoord.out.bam.bai',
            'Log.final.out',
            'Log.out',
            'Log.progress.out',
            'SJ.out.tab',
        ]
        actual_output_dir = self._locate_result_folder().name
        raw_output_links = {}
        for sample in analysis_info.samples:
            raw_output_links[sample] = {
                filename: '../result/{output_dir}/{sample}/{filename}'.format(
                    output_dir=actual_output_dir,
                    sample=sample,
                    filename=filename
                )
                for filename in raw_output_filenames
            }

        return raw_output_links
