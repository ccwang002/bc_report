from pathlib import Path
from bc_report.info import AnalysisInfo
from bc_report import create_logger
from ..base.report import BaseStage
from . import RNASeqStageMixin

logger = create_logger(__name__)


class CuffdiffStage(RNASeqStageMixin, BaseStage):
    template_entrances = ['rna_seq/cuffdiff.html']
    result_folder_name = 'cuffdiff'

    def parse(self, analysis_info: AnalysisInfo):
        data_info = super().parse(analysis_info)
        data_info['raw_output'] = self.collect_raw_output(analysis_info)
        return data_info

    def collect_raw_output(self, analysis_info: AnalysisInfo):
        """Render the link to the raw output files"""
        raw_output_filenames = [
            # isoform
            'isoform_exp.diff',
            'isoforms.count_tracking',
            'isoforms.fpkm_tracking',
            'isoforms.read_group_tracking',
            # gene
            'gene_exp.diff',
            'genes.count_tracking',
            'genes.fpkm_tracking',
            'genes.read_group_tracking',
            # cds
            'cds_exp.diff',
            'cds.count_tracking',
            'cds.fpkm_tracking',
            'cds.read_group_tracking',
            # tss
            'tss_group_exp.diff',
            'tss_groups.count_tracking',
            'tss_groups.fpkm_tracking',
            'tss_groups.read_group_tracking',
            # diff
            'cds.diff',
            'promoters.diff',
            'splicing.diff',
            # info
            'run.info',
            'read_groups.info',
            'bias_params.info',
            'var_model.info',
            'run_cuffdiff.log',
        ]
        actual_output_dir = self._locate_result_folder().name
        raw_output_links = {
            filename: '../result/{output_dir}/{filename}'.format(
                output_dir=actual_output_dir,
                filename=filename
            )
            for filename in raw_output_filenames
        }
        return raw_output_links
