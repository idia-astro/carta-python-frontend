import os
import re
import subprocess
import glob
import setuptools
from distutils.command.build_py import build_py as build_py_orig

class BuildProto(setuptools.Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        proto_files = glob.glob('carta-protobuf/*/*.proto')
        proto_dirs = set(os.path.dirname(f) for f in proto_files)
        includes = [f"-I{d}" for d in proto_dirs]
        subprocess.run([
            'protoc',
            *includes,
            '--python_out=cartaicdproto/',
            *proto_files,
        ])
        
        # There seriously isn't a better way to fix this relative import as of time of writing
        for pb2_file in glob.glob('cartaicdproto/*_pb2.py'):
            with open(pb2_file) as f:
                data = f.read()
            data = re.sub("^(import .*_pb2)", r"from . \1", data, flags=re.MULTILINE)
            with open(pb2_file, 'w') as f:
                f.write(data)

        
class BuildPy (build_py_orig):
    def run(self):
        self.run_command('build_proto')
        super(BuildPy, self).run()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="carta_frontend",
    version="0.0.1",
    author="Adrianna Pińska",
    author_email="adrianna.pinska@gmail.com",
    description="Python interface to the CARTA backend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/idia-astro/carta-python-frontend",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    cmdclass={
        "build_py": BuildPy,
        "build_proto": BuildProto,
    },
)
