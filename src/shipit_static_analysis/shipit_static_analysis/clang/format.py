import os
import subprocess
from cli_common.log import get_logger

logger = get_logger(__name__)


class ClangFormat(object):
    '''
    Clang Format direct Runner
    List potential issues on modified files
    from a patch
    '''
    def __init__(self, work_dir, mozreview):
        assert os.path.isdir(work_dir)

        self.work_dir = work_dir
        self.mozreview = mozreview

    def run(self, modified_files):
        '''
        Run clang-format on those modified files
        '''
        for path in modified_files:
            full_path = os.path.join(self.work_dir, path)
            assert os.path.exists(full_path), \
                'Modified file not found {}'.format(full_path)

            self.run_clang_format(full_path)


    def run_clang_format(self, path):
        '''
        Clang-format is very fast, no need for a worker queue here
        '''

        # Build command line for a filename
        cmd = [
            # Use system clang format
            'clang-format',

            # Use style from directories
            '-style=file',

            path,
        ]
        logger.info('Running clang-format', cmd=' '.join(cmd))

        # Run command
        clang_output = subprocess.check_output(cmd, cwd=self.work_dir)

        print('raw', clang_output)

        # Compare output with original file
        src_lines = [x.rstrip('\n') for x in open(path).readlines()]
        clang_lines = clang_output.decode('utf-8').split('\n')


        import difflib
        diff = difflib.SequenceMatcher(
            a=src_lines,
            b=clang_lines,
        )
        for tag, i1, i2, j1, j2 in diff.get_opcodes():

            # Check that i1:i2 is in modified lines

            if tag == 'equal':
                continue
            elif tag == 'replace':
                # a[i1:i2] should be replaced by b[j1:j2].
            # delete: a[i1:i2] should be deleted.
            # insert: b[j1:j2] should be inserted at a[i1:i1].

            print(tag, i1, i2, j1, j2)



        print(src_lines)
        print(clang_lines)

        return []


        for i in range(len(src_lines)):
            src_line = src_lines[i]
            clang_line = clang_lines[i]

            if src_line != clang_line:
                print('woops', clang_line)



        print('CLANG OUTPUT', clang_output)


        return []
