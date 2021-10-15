import io

from setuptools import setup

setup(
    name='blobconverter',
    version='1.2.4',
    description='The tool that allows you to convert neural networks to MyriadX blob',
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url='https://github.com/luxonis/blobconverter',
    keywords="blobconverter blob converter myriadx openvino tensorflow caffe ir",
    author='Luxonis',
    author_email='support@luxonis.com',
    license='MIT',
    packages=['blobconverter'],
    entry_points={
        'console_scripts': [
            'blobconverter=blobconverter.__init__:__run_cli__'
        ],
    },
    install_requires=[
        "requests",
        "PyYAML",
        "boto3"
    ],
    include_package_data=True,
    project_urls={
        "Bug Tracker": "https://github.com/luxonis/blobconverter/issues",
        "Source Code": "https://github.com/luxonis/blobconverter/tree/master/cli",
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
