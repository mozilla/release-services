import subprocess
from cli_common.log import get_logger

logger = get_logger(__name__)


def run_command(cmd, work_dir):
    """
    Run a command through subprocess
    """
    logger.info('Running command', cmd=' '.join(cmd))
    proc = subprocess.Popen(
        cmd,
        cwd=work_dir,
        stdin=subprocess.DEVNULL,  # no interactions
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, err = proc.communicate()

    if proc.returncode != 0:
        logger.critical('Proc', output=output, error=err)
        raise Exception('Invalid exit code for command {}: {}'.format(cmd, proc.returncode))  # noqa

    return output

def run_gecko_command(cmd, work_dir):
    """
    Run a command through subprocess
    using gecko build environnment
    """
    cmd = ['gecko-env', ] + cmd
    return run_command(cmd, work_dir)
