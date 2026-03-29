from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="kreativ_theme",
    version="1.0.0",
    description="Tema Premium TDS/UFT para Frappe LMS — Identidade Visual IPEX/UFT/MDS",
    author="IPEX / UFT",
    author_email="ti@ipexdesenvolvimento.cloud",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
