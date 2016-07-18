import ast
from datetime import datetime
from pathlib import Path
from seaborn.palettes import husl_palette
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

    NUM_READ_METRICS = [
        'Number of input reads',
        'Uniquely mapped reads number',
        'Number of reads mapped to multiple loci',
        'Number of reads mapped to too many loci',
        'Number of reads unmapped: too many mismatches',
        'Number of reads unmapped: too short',
        'Number of reads unmapped: other',
        'Number of chimeric reads',
    ]

    PERCENT_METRICS = [
        'Uniquely mapped reads %',
        '% of reads mapped to multiple loci',
        '% of reads mapped to too many loci',
        '% of reads unmapped: too many mismatches',
        '% of reads unmapped: too short',
        '% of reads unmapped: other',
        '% of chimeric reads',
    ]

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

    def get_context_data(self, data_info):
        context = super().get_context_data(data_info)
        context['NUM_READ_METRICS'] = self.NUM_READ_METRICS
        context['PERCENT_METRICS'] = self.PERCENT_METRICS

        METRICS_DISPLAY = [
            'unique',
            'mulit-map (multiple loci)',
            'multi-map (too many loci)',
            'unmapped (too many mismatches)',
            'unmapped (too short)',
            'unmapped (other)',
            'chimeric',
        ]

        # Prepare data for plotting
        analysis_info = self.report.analysis_info
        plot_num_read_data = []
        for metric, metric_display in zip(
            reversed(self.NUM_READ_METRICS[1:]),
            reversed(METRICS_DISPLAY),
        ):
            plot_num_read_data.append({
                'name': metric_display,
                'data': [
                    data_info['align_stat'][sample][metric]
                    for sample in analysis_info.samples
                ],
            })

        # Compute the color for condition plot bands
        condition_bands = []
        condition_counter = 0
        for (condition, samples), color in zip(
            analysis_info.conditions.items(),
            husl_palette(len(analysis_info.conditions), l=0.8, s=0.6),
        ):
            condition_bands.append({
                'from': condition_counter - 0.5,
                'to': condition_counter + len(samples) - 0.5,
                'color': 'rgba({:d}, {:d}, {:d}, 0.4)'.format(
                    *[int(c * 255) for c in color]
                ),
                'label': {
                    'text': condition,
                    'align': 'right',
                    'x': -5,
                }
            })
            condition_counter += len(samples)

        context['plot_num_read'] = {
            'data': plot_num_read_data,
            'condition_bands': condition_bands,
        }

        return context

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
