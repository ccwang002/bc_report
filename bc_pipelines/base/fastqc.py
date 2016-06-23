from collections import OrderedDict
import decimal
import io
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
from bc_report.info import AnalysisInfo
from bc_report import create_logger
from .report import BaseStage

D = decimal.Decimal
logger = create_logger(__name__)


class OverSeq:
    def __init__(self, seq, count, percentage, possible_source):
        self.seq = seq
        self.count = D(count)
        self.percentage = D(percentage).quantize(D("0.01"))
        self.possible_source = possible_source


def parse_fastqc_data(data_f):
    qc_info = OrderedDict()
    qc_data = {}
    qc_desc = None
    next(data_f)  # FastQC version info
    for line in data_f:
        new_sec = line.startswith('>>')
        sec_end = line.startswith('>>END_MODULE')
        if new_sec and not sec_end:
            qc_desc, qc_status = line.rstrip()[2:].rsplit('\t', 1)
            qc_info[qc_desc] = qc_status
            qc_data[qc_desc] = []
        elif not new_sec and not sec_end:
            qc_data[qc_desc].append(line.rstrip('\n').split('\t'))
    return qc_info, qc_data


class FastQCStage(BaseStage):
    template_entrances = ['base/fastqc.html']
    result_folder_name = 'fastqc'

    MODULES = OrderedDict([
        ('Basic Statistics', None),
        ('Per base sequence quality', 'per_base_quality.png'),
        ('Per tile sequence quality', None),
        ('Per sequence quality scores', 'per_sequence_quality.png'),
        ('Per sequence GC content', 'per_sequence_gc_content.png'),
        ('Per base N content', 'per_base_n_content.png'),
        ('Sequence Length Distribution', 'sequence_length_distribution.png'),
        ('Sequence Duplication Levels', 'duplication_levels.png'),
        ('Overrepresented sequences', None),
        ('Adapter Content', None),
        ('Kmer Content', None),
    ])

    STATUS_TO_ICON_CLASS = {
        'pass': 'fa-check',
        'fail': 'fa-times',
        'warn': 'fa-exclamation',
    }

    def accepted_data_sources(self, data_sources) -> OrderedDict:
        filtered_sources = OrderedDict()
        for source_name, source in data_sources.items():
            if source.file_type in ['FASTA', 'FASTQ']:
                filtered_sources[Path(source_name)] = source
        return filtered_sources

    def parse_per_base_quality(self, data_info, source_p, qc_data):
        perbase_q = qc_data['Per base sequence quality']
        df = (
            pd.DataFrame(perbase_q[1:], columns=perbase_q[0])
                .assign(**{
                    # '#Base': lambda x: x['#Base'].astype(np.int),
                    'Mean': lambda x: x['Mean'].astype(np.float),
                })
        )
        data_info['per_base_quality'].append({
            'name': source_p.stem,
            'data': list(df[ 'Mean'].values),
            'pointStart': 1,
        })

    def parse(self, analysis_info: AnalysisInfo):
        data_info = super().parse(analysis_info)
        data_info['qc_info'] = OrderedDict()
        data_info['qc_data'] = {}
        result_root = analysis_info.result_root / self._locate_result_folder()
        accepted_sources = self.accepted_data_sources(
            analysis_info.data_sources
        )
        for source_p, source in accepted_sources.items():
            fastqc_zip_pth = Path(
                result_root,
                source_p.stem, '{}_fastqc.zip'.format(source_p.stem)
            )
            logger.debug('Parsing FastQC zip file %s' % fastqc_zip_pth.as_posix())
            with zipfile.ZipFile(fastqc_zip_pth.as_posix(), 'r') as zipf:
                fastqc_data_pth = '{}/fastqc_data.txt'.format(fastqc_zip_pth.stem)
                with io.TextIOWrapper(zipf.open(fastqc_data_pth), encoding='utf8') as f:
                    qc_info, qc_data = parse_fastqc_data(f)
                    data_info['qc_info'][source_p.name] = qc_info
                    data_info['qc_data'][source_p.name] = qc_data

        # Parse FastQC per base quality
        data_info['per_base_quality'] = []
        for source_p, source in accepted_sources.items():
            self.parse_per_base_quality(
                data_info, source_p, data_info['qc_data'][source.name]
            )
        return data_info

    def get_context_data(self, data_info):
        context = super().get_context_data(data_info)
        context.update({
            'MODULES': self.MODULES,
            'STATUS_TO_ICON_CLASS': self.STATUS_TO_ICON_CLASS,
        })
        return context
