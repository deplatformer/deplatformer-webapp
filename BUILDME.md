# Deplatformer-installable

[![License: MIT](https://img.shields.io/pypi/l/deplatformer_webapp)]()

Instructions for building Deplatformer into a bundled package for cross-platform local usage.

Compatible with:
* debian based linux (Ubuntu, linux Mint, debian)

Coming soon:
* Windows 7
* Windows 10
* Mac OSX

Instructions:
* Enable your venv
* Build the python bundle with `pyinstaller run.linux.spec`
* cd to the deplatformer-electron directory `cd deplatformer-electron`
* Build the electron bundle with `npm run make`

The output file will be in `deplatformer-electron/out/make/`
