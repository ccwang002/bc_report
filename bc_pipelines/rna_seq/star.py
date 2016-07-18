import ast
from datetime import datetime
from pathlib import Path
from bc_report.info import AnalysisInfo
from bc_report import create_logger
from ..base.report import BaseStage
from . import RNASeqStageMixin

logger = create_logger(__name__)


def parse_star_log(log_str: str):
    """Parse STAR's Log.final.out format"""
    align_stat = dict(
        tuple(l.strip().split(' |\t', 1))
        for l in log_str.splitlines()
        if ' |\t' in l
    )
    # Convert to proper data types
    for metric_key, metric_val in align_stat.items():
        if metric_val.endswith('%'):
            # Convert to percentage
            align_stat[metric_key] = float(metric_val[:-1]) / 100
        elif metric_key in [
            'Started job on',
            'Started mapping on',
            'Finished on',
        ]:
            # Convert to datetime
            align_stat[metric_key] = datetime.strptime(
                metric_val, '%b %d %H:%M:%S'
            )
        else:
            # Convert to int or float from str
            #
            #   >>> import ast
            #   >>> type(ast.literal_eval('10.0'))
            #   float
            #   >>> type(ast.literal_eval('10'))
            #   int
            #
            # Ref: http://stackoverflow.com/a/9510585
            align_stat[metric_key] = ast.literal_eval(metric_val)
    # Compute number of unmapped reads
    num_input_reads = align_stat['Number of input reads']
    for percent_metric in [
        '% of reads unmapped: too many mismatches',
        '% of reads unmapped: too short',
        '% of reads unmapped: other',
    ]:
        num_metric = 'Number %s' % percent_metric[len('% '):]
        align_stat[num_metric] = int(
            align_stat[percent_metric] * num_input_reads
        )
    return align_stat


class STARStage(RNASeqStageMixin, BaseStage):
    template_entrances = ['rna_seq/star.html']
    result_folder_name = 'STAR'

    def parse(self, analysis_info: AnalysisInfo):
        data_info = super().parse(analysis_info)

        logger.info('Parsing STAR alignment statistics from log file')
        align_stat = {}
        result_dir = self._locate_result_folder()
        for sample in analysis_info.samples:
            with result_dir.joinpath(sample, 'Log.final.out').open() as f:
                align_stat[sample] = parse_star_log(f.read())
        data_info['align_stat'] = align_stat

        logger.info('Generating raw output file links')
        data_info['raw_output'] = self.collect_raw_output(analysis_info)
        return data_info

    def collect_raw_output(self, analysis_info: AnalysisInfo):
        """Render the link to the raw output files"""
        raw_output_filenames = [
            'Aligned.sortedByCoord.out.bam',
            'Aligned.sortedByCoord.out.bam.bai',
            'Log.final.out',
            'Log.out',
            'Log.progress.out',
            'SJ.out.tab',   # high confidence collapsed splice junction
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
