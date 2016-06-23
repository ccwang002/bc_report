from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
from . import create_logger

logger = create_logger(__name__)


def tojson(a, *args, **kw):
    """Convert the value to JSON"""
    return json.dumps(a, *args, **kw)


def humanfmt(
        value, places=0, curr='', sep=',', dp='.',
        pos='', neg='-', trailneg=''
):
    """Convert Decimal to a money formatted string.

    This function is an example from Official :mod:`decimal`.

    Attributes
    ----------
    places:
        required number of places after the decimal point
    curr:
        optional currency symbol before the sign (may be blank)
    sep:
        optional grouping separator (comma, period, space, or blank)
    dp:
        decimal point indicator (comma or period)
        only specify as blank when places is zero
    pos:
        optional sign for positive numbers: '+', space or blank
    neg:
        optional sign for negative numbers: '-', '(', space or blank
    trailneg:
        optional trailing minus indicator:  '-', ')', space or blank

    Examples
    --------

        >>> d = Decimal('-1234567.8901')
        >>> humanfmt(d, curr='$')
        '-$1,234,567.89'
        >>> humanfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
        '1.234.568-'
        >>> humanfmt(d, curr='$', neg='(', trailneg=')')
        '($1,234,567.89)'
        >>> humanfmt(Decimal(123456789), sep=' ')
        '123 456 789.00'
        >>> humanfmt(Decimal('-0.02'), neg='<', trailneg='>')
        '<0.02>'

    """
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))


def open(path_like, *args, **kwargs):
    """Custom open() that accepts :py:class:`pathlib.Path` object.

    All the parameters will be passed to original :py:func:`python:open`.

    Examples
    --------

        >>> with open(Path('say'), 'w') as f:
        ...     f.write('hi')

    """
    logger.debug(
        "File {0!s} is open by custom open() function "
        "with extra arguments: args={1} kwargs={2}"
        .format(path_like, args, kwargs)
    )
    if isinstance(path_like, Path):
        return path_like.open(*args, **kwargs)
    else:
        return open(path_like, *args, **kwargs)


def copy(src_path_like, dst_path_like, metadata=False, **kwargs):
    """pathlib support for path-like objects.

    Internally use either :py:func:`shutil.copy` or :py:func:`shutil.copy2`
    based on `metadata` value.
    """
    if metadata:
        _copy_cmd = shutil.copy2  # copy2 perserves metadata
    else:
        _copy_cmd = shutil.copy

    # TODO: use system command for large file
    _copy_cmd(
        strify_path(src_path_like), strify_path(dst_path_like), **kwargs
    )


def discover_file_by_patterns(path_like, file_patterns="*"):
    """Discover files under certain path based on given patterns.

    Support both ``**`` and ``*`` globbing syntax.
    Call :py:func:`pathlib.Path.glob` internally.

    Parameters
    ----------
    path_like : path-like object
    file_patterns : str or iterable
        glob-style file pattern

    Returns
    -------
    List of :py:class:`pathlib.Path` object.

    Examples
    --------

        >>> discover_file_by_patterns("report", "**/_*.html")
        [PosixPath('report/templates/_nav.html'),
         PosixPath('report/templates/_footer.html'),
         PosixPath('report/templates/_stage_pipe.html')]
        >>> discover_file_by_patterns("report", ["**/_*.html", "**/*.js"])
        [PosixPath('report/templates/_nav.html'),
         PosixPath('report/templates/_footer.html'),
         PosixPath('report/templates/_stage_pipe.html'),
         PosixPath('report/static/vendor/bootstrap-3.1.1/js/bootstrap.min.js'),
         PosixPath('report/static/vendor/bootstrap-3.1.1/js/bootstrap.js')]

    """
    # if input is str
    if isinstance(file_patterns, str):
        found_file_list = list(Path(path_like).glob(file_patterns))
        logger.info(
            "{2} file matching single pattern {1} under {0!s}"
            .format(path_like, file_patterns, len(found_file_list))
        )

    # if input is iterable
    try:
        discovered_file_list = []
        for pattern in file_patterns:
            if not isinstance(pattern, str):
                raise TypeError(
                    "File pattern should be str, not {}".format(file_patterns)
                )
            file_list = list(Path(path_like).glob(pattern))
            logger.debug(
                "... {} file found by {}"
                .format(len(file_list), pattern)
            )
            discovered_file_list.extend(file_list)
        logger.info(
            "{2} file matching patterns {1!r} under {0!s}"
            .format(path_like, file_patterns, len(discovered_file_list))
        )
        return discovered_file_list
    except TypeError as te:
        raise ValueError(
            "Unexpect file_patterns: {}, "
            "should be str or iterable of str elements."
            .format(file_patterns)
        ) from te


def merged_copytree(src_list, dst):
    dst_p = Path(dst)
    if not dst_p.exists():
        dst_p.mkdir()
    for src in src_list:
        src_p = Path(src)
        for current_root, dirs, files in os.walk(strify_path(src)):
            current_p = Path(current_root)
            rel_to_src_root = current_p.relative_to(src_p)
            dst_current_d = dst_p / rel_to_src_root
            if not dst_current_d.exists():
                dst_current_d.mkdir()
            else:
                logger.debug(
                    "Dest. dir: {!s} existed, keeping its files"
                    .format(dst_current_d)
                )
            logger.debug(
                '{2} files: {0!s} -> {1!s}'
                .format(current_p, dst_current_d, len(files))
            )
            for f in files:
                src_f = current_p / f
                try:
                    dst_f = dst_current_d / f
                    if dst_f.exists():
                        logger.warning(
                            "File {} existed, overwritten by {}"
                            .format(dst_f, src_f)
                        )
                        dst_f.unlink()
                    copy(src_f, dst_current_d)
                except Exception as e:
                    logger.warn(
                        "Copying {} caught error {!r}, skipped"
                        .format(src_f, e)
                    )


def strify_path(path_like):
    """Normalized path-like object to POSIX style str.

    Examples
    --------

        >>> strify_path(Path('ngcloud') / 'hi.py'))
        "ngcloud/hi.py"
        >>> strify_path('ngcloud/hi.py')
        "ngcloud/hi.py"

    """
    if isinstance(path_like, Path):
        return path_like.as_posix()
    elif isinstance(path_like, str):
        return path_like
    else:
        raise TypeError(
            "Unknown type {} for path-like object".format(type(path_like))
        )


def is_pathlike(path_like):
    """Helper function to determine is pathlike object."""
    if isinstance(path_like, Path) or isinstance(path_like, str):
        return True
    else:
        return False
