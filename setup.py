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
        
        for proto_dir in proto_dirs:
            includes = [f"-I{d}" for d in proto_dirs]
            destination = os.path.join("cartaicdproto", os.path.basename(proto_dir))
            proto_files = glob.glob(os.path.join(proto_dir, "*.proto"))
        
            subprocess.run([
                'protoc',
                *includes,
                f'--python_out={destination}',
                *proto_files,
            ])

        
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
