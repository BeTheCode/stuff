import setuptools

setuptools.setup(
    name="iot_ml_demo",
    version="0.0.1",
    description="IoT ML Demo Infrastructure",
    author="author",
    package_dir={"": "stacks"},
    packages=setuptools.find_packages(where="stacks"),
    install_requires=[
        "aws-cdk-lib>=2.0.0",
        "constructs>=10.0.0,<11.0.0",
    ],
)