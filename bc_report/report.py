from pathlib import Path
from typing import List
from . import create_logger
from .info import JobInfo
from .utils import merged_copytree

logger = create_logger(__name__)


class Stage:
    def __init__(self, report):
        self.report = report

    def parse(self, job_info):
        data_info = {}
        return data_info

    def render(self, data_info, report_root):
        pass


class SummaryStage(Stage):
    def render(self, joint_data_info, report_root):
        pass


class Report:

    stage_classes = []
    """(List of class name) Store the sequence of stages in use."""

    static_roots = []

    def __init__(self, job_dir: Path):
        """Initiate a new report based on given job result."""
        logger.debug(
            "New report {} object has been initiated"
            .format(type(self).__name__)
        )
        self.job_info = JobInfo(job_dir)
        self.out_root = None
        self.report_root = None
        self._stages = self.initiate_stages()
        self.data_info = {
            type(stage).__name__: None
            for stage in self.tool_stages
        }

    def initiate_stages(self) -> List[Stage]:
        return [
            stage_cls(self)
            for stage_cls in self.stage_classes
        ]

    def parse(self):
        for stage in self.tool_stages:
            stage_name = type(stage).__name__
            self.data_info[stage_name] = stage.parse(self.job_info)

    def generate(self, out_dir: Path):
        self.out_root = out_dir
        self.report_root = out_dir / 'report'
        self.report_root.mkdir()
        self.render_report()
        self.copy_static()

    def render_report(self):
        """Render and output the report"""
        for stage in self.tool_stages:
            stage_name = type(stage).__name__
            stage.render(self.data_info[stage_name], self.report_root)

        for stage in self.summary_stages:
            stage.render(self.data_info, self.report_root)

    def copy_static(self):
        merged_copytree(self.static_roots, self.report_root / 'static')
        for stage in self.all_stages:
            stage.copy_static()

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
