import os
import sys
import livereload
import subprocess

HERE = os.path.dirname(__file__)

server = livereload.Server()
server.watch(
    os.path.join(HERE, '*.rst'),
    livereload.shell('make html'),
)
server.watch(
    os.path.join(HERE, '*', '*.rst'),
    livereload.shell('make html'),
)
server.watch(
    os.path.join(HERE, 'shipit_signoffs', '*.rst'),
    livereload.shell('make html'),
)

subprocess.call('make html', shell=True)

server.serve(
    port=os.environ.get('PORT', 5000),
    host=os.environ.get('HOST', 'localhost'),
    root=os.path.join(HERE, 'build/html'),
)
