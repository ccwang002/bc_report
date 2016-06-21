import importlib
import logging
from pathlib import Path
import shutil
import sys
import click

from . import create_logger

logger = create_logger(__name__)

CAVEAT_MESSAGE = '''\
New output result is under {!s}.

The folder can be downloaded and viewed locally.
Quick remainder for serving current folder through http:

    $ python3 -m http.server
    # Serving HTTP on 0.0.0.0 port 8000 ...
'''


def create_log_format(log_time, color):
    color_log_fmt = (
        '%(log_color)s%(levelname)-7s%(reset)s %(cyan)s%(name)-8s%(reset)s '
        '%(log_color)s[%(funcName)s]%(reset)s %(message)s'
    )
    log_fmt = '[%(levelname)-7s][%(name)-8s][%(funcName)-8s] %(message)s'

    if log_time:
        color_log_fmt = '%(asctime)s ' + color_log_fmt
        log_fmt = '[%(asctime)s]' + log_fmt

    if color:
        try:
            import colorlog
            log_formatter = colorlog.ColoredFormatter(
                color_log_fmt,
                '%Y-%m-%d %H:%M:%S',
                log_colors=colorlog.default_log_colors
            )
            return log_formatter
        except ImportError:
            logger.warning(
                "Color logs require colorlog, "
                "try pip install colorlog or colorlog[windows] on Windows"
            )

    log_formatter = logging.Formatter(
        log_fmt,
        '%Y-%m-%d %H:%M:%S'
    )
    return log_formatter


ReadableAbsoluteFolderPath = click.Path(
    exists=True,
    dir_okay=True, file_okay=False,
    readable=True,
    resolve_path=True
)


@click.command(context_settings={
    'help_option_names': ['-h', '--help']
})
@click.option(
    '-v', '--verbose', count=True,
    help='Increase verbosity (noiser when more -v)',
)
@click.option(
    '--log-time/--no-log-time', default=False,
    help='Add time stamp in log',
)
@click.option(
    '--color/--no-color', default=True,
    help='Produce colorful logs',
)
@click.option(
    '-f', '--force/--no-force', default=False,
    help='Overwrite the output folder if it exists',
)
@click.option(
    '-p', '--pipeline',
    metavar='bc_pipelines.mypipeline.report.Report',
    help='Full path to the pipeline class',
    required=True,
)
@click.argument('job_dir', type=ReadableAbsoluteFolderPath)
@click.argument('out_dir', type=click.Path(), default='./output')
def generate_report_cli(
    pipeline, job_dir, out_dir,
    verbose, log_time, color, force,
):
    # Setup console logging
    console = logging.StreamHandler()
    all_loggers = logging.getLogger()
    all_loggers.addHandler(console)

    # Decide the logging level
    if verbose == 1:
        loglevel = logging.INFO
    elif verbose >= 2:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARNING
    all_loggers.setLevel(loglevel)

    # Set log format
    console.setFormatter(create_log_format(log_time, color))
    logger.debug(
        'Using pipeline: {} to parse job folder {} and generate report at {}.'
        .format(pipeline, job_dir, out_dir)
    )

    # Get and import the pipeline class
    logger.debug(
        'Importing pipeline report class {pipeline:s} ...'
        .format(pipeline=pipeline)
    )
    pipe_module_name, pipe_class_name = pipeline.rsplit('.', 1)
    pipe_module = importlib.import_module(pipe_module_name)
    pipeline_report_cls = getattr(pipe_module, pipe_class_name)

    # Processing the job and output folders
    job_dir_p, out_dir_p = Path(job_dir), Path(out_dir)
    if out_dir_p.exists():
        if not force:
            sys.exit(
                "Cannot overwrite output folder (force overwriting by passing "
                "--force option). Current operation has been aborted."
            )
        logger.warning(
            "Report output folder {:s} has already existed! ..."
            .format(out_dir_p.as_posix())
        )
        # remove the output folder completely
        shutil.rmtree(out_dir_p.as_posix())
    # Create the output folder
    out_dir_p.mkdir(parents=True)

    # Initiate the report class
    report = pipeline_report_cls(job_dir_p)

    # Generate the report
    report.generate(out_dir_p)

    logger.info("Job successfully end. Print message")
    print(CAVEAT_MESSAGE.format(out_dir))
