from pathlib import Path
from typing import List
import re
import jinja2

from . import create_logger
from .info import AnalysisInfo
from .utils import (
    merged_copytree,
    discover_file_by_patterns,
    copy,
    strify_path, humanfmt, tojson
)

logger = create_logger(__name__)


class Stage:

    template_entrances = ['stage.html']
    template_find_paths = ['templates']
    embed_result_joint = []
    embed_result_per_condition = []
    embed_result_per_sample = []

    result_folder_name = ''

    def __init__(self, report: 'Report'):
        self.report = report
        self._setup_jinja2()

    def parse(self, analysis_info: AnalysisInfo):
        data_info = {}
        return data_info

    def get_context_data(self, data_info):
        return dict(
            data_info=data_info,
            analysis_info=self.report.analysis_info,
        )

    def render(self, data_info, report_root):
        for tpl_name in self.template_entrances:
            tpl = self._env.get_template(tpl_name)
            html = tpl.render(self.get_context_data(data_info))
            # remove folder structure in template name
            tpl_report_path = report_root / tpl_name.rsplit('/', 1)[1]
            logger.debug('writing template to %s' % tpl_report_path.as_posix())
            with tpl_report_path.open('w') as f:
                f.write(html)

    def copy_static(self, report_root):
        result_dir = self._locate_result_folder()
        self.copy_static_per_sample(result_dir, report_root)
        self.copy_static_per_condition(result_dir, report_root)
        self.copy_static_joint(result_dir, report_root)

    @property
    def name(self):
        return self.__class__.__name__

    def _setup_jinja2(self):
        _template_paths = [
            strify_path(p) for p in self.template_find_paths
        ]
        logger.debug(
            "Jinja2 reads templates from {}".format(_template_paths)
        )
        self._report_loader = jinja2.FileSystemLoader(_template_paths)
        self._env = jinja2.Environment(
            loader=self._report_loader,
            extensions=['jinja2.ext.with_'],
        )
        self._env.globals['static'] = self._template_static_path
        self._env.globals['humanfmt'] = humanfmt
        self._env.filters['tojson'] = tojson

    def _template_static_path(self, *path_parts):
        return Path('static', *path_parts).as_posix()

    def _locate_result_folder(self):
        if not self.result_folder_name:
            raise ValueError("Stage {:s} does not have result_folder_name set")

        folder_pattern = r"^(\d+_|){}$".format(self.result_folder_name)
        logger.debug(
            "Result folder name regex pattern: {}".format(folder_pattern))
        valid_name = re.compile(folder_pattern).match

        stage_result_path = [
            p for p in self.report.analysis_info.result_root.iterdir()
            if valid_name(p.name)
        ]
        if not stage_result_path:
            raise ValueError(
                "No matched folder name found for pattern {}"
                .format(folder_pattern)
            )
        if len(stage_result_path) > 1:
            raise ValueError(
                "Duplicated stage result folders found: {} of pattern {}"
                .format(stage_result_path, self.result_folder_name)
            )
        return stage_result_path[0]

    def copy_static_joint(self, result_dir, report_root):
        for desc in self.embed_result_joint:
            src_root = result_dir / desc['src']
            dest_root = report_root / 'static' / desc['dest']
            if not dest_root.exists():
                dest_root.mkdir(parents=True)

            file_list = discover_file_by_patterns(src_root, desc['patterns'])
            for fp in file_list:
                copy(fp, dest_root)

    @staticmethod
    def copy_static_grouped(
        result_root, report_root,
        src_rel_pth, dest_rel_pth, file_patterns, groups
    ):
        all_src_root = result_root / src_rel_pth
        all_dest_root = report_root / dest_rel_pth
        for grp in groups:
            grp_src_root = all_src_root / grp
            grp_dest_root = all_dest_root / dest_rel_pth / grp
            grp_dest_root.mkdir(parents=True)

            file_list = discover_file_by_patterns(grp_src_root, file_patterns)
            for fp in file_list:
                copy(fp, grp_dest_root)

    @staticmethod
    def batch_copy_static_grouped(
        result_dir, report_root, desc_sources, groups=None
    ):
        for desc in desc_sources:
            Stage.copy_static_grouped(
                result_dir, report_root,
                desc['src'], desc['dest'], groups
            )

    def copy_static_per_condition(self, result_dir, report_root):
        self.batch_copy_static_grouped(
            result_dir, report_root,
            desc_sources=self.embed_result_per_condition,
            groups=self.report.analysis_info.conditions.keys()
        )

    def copy_static_per_sample(self, result_dir, report_root):
        self.batch_copy_static_grouped(
            result_dir, report_root,
            desc_sources=self.embed_result_per_sample,
            groups=self.report.analysis_info.samples.keys()
        )


class SummaryStage(Stage):

    def get_context_data(self, data_info):
        context = super().get_context_data(data_info)
        context['joint_data_info'] = context['data_info']
        del context['data_info']
        return context

    def _locate_result_folder(self):
        return self.report.analysis_info.result_root


class Report:

    stage_classes = []
    """(List of class name) Store the sequence of stages in use."""

    static_roots = []

    def __init__(self, analysis_dir):
        """Initiate a new report based on given job result."""
        logger.debug(
            "New report {} object has been initiated"
            .format(type(self).__name__)
        )
        self.analysis_info = AnalysisInfo(analysis_dir)
        self.out_root = None
        self.report_root = None
        self._stages = self.initiate_stages()
        self.data_info = {
            stage.name: None
            for stage in self.tool_stages
        }

    def initiate_stages(self) -> List[Stage]:
        return [
            stage_cls(self)
            for stage_cls in self.stage_classes
        ]

    def parse(self, analysis_info: AnalysisInfo):
        for stage in self.tool_stages:
            logger.info('Parsing stage %s' % stage.name)
            self.data_info[stage.name] = stage.parse(analysis_info)

    def generate(self, out_dir: Path):
        self.out_root = out_dir
        self.report_root = out_dir / 'report'
        self.report_root.mkdir()
        logger.info('Parsing result')
        self.parse(self.analysis_info)
        logger.info('Rendering report')
        self.render_report()
        logger.info('Copying static files')
        self.copy_static()

    def render_report(self):
        """Render and output the report"""
        for stage in self.tool_stages:
            stage.render(self.data_info[stage.name], self.report_root)

        for stage in self.summary_stages:
            stage.render(self.data_info, self.report_root)

    def copy_static(self):
        merged_copytree(self.static_roots, self.report_root / 'static')
        for stage in self.all_stages:
            stage.copy_static(self.report_root)

    @property
    def all_stages(self) -> List[Stage]:
        return self._stages

    @property
    def tool_stages(self) -> List[Stage]:
        return (
            stage for stage in self._stages
            if not isinstance(stage, SummaryStage)
        )

    @property
    def summary_stages(self) -> List[Stage]:
        return (
            stage for stage in self._stages
            if isinstance(stage, SummaryStage)
        )
