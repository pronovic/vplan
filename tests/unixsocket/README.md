## Forked Code

This code was forked from requests-unixsocket, with source taken from [v0.3.0 on PyPI](https://pypi.org/project/requests-unixsocket/0.3.0/#files).  The original source code is on GitHub at [msabramo/requests-unixsocket](https://github.com/msabramo/requests-unixsocket), but v0.3.0 doesn't appear in the tags there.  This code is licensed under Apache v2, so this is permitted use.

I forked the code because it's incompatible with urllib 2.x, which requests moved to as of [v2.30.0](https://github.com/psf/requests/releases/tag/v2.30.0).  We need to be on requests [>= v2.31.0](https://github.com/psf/requests/releases/tag/v2.31.0) due to [CVE-2023-32681](https://nvd.nist.gov/vuln/detail/CVE-2023-32681).  The problem with requests-unixsocket is tracked in [issue #70](https://github.com/msabramo/requests-unixsocket/issues/70) and fixed in [PR #69](https://github.com/msabramo/requests-unixsocket/pull/69).  However, as of this writing, the requests-unixsocket maintainer hasn't responded to either the issue or the PR.  Given how small the code is, it seems safer and simpler to just pull it in rather than waiting for a new package to be released on PyPI.