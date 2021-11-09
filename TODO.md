Remaining work:

- unit tests for CLI (with mock client)
- implement client interface
- unit tests for client interface
- implement API endpoints in terms of stubbed database and client code
- unit test API endpoints  (with mock client and database)
- implement database code
- unit test database code against live in-memory database
- implement SmartThings client code
- unit test client code against captured data from Insomnia
- do manual local testing with client and server on Macbook
- establish the correct process for setting up to use systemd on Linux
- strip out readthedocs stuff and doc directory
- strip out references to PyPI in all of the documentation and pyproject.toml
- adjust build/release process to release wheel and config template to GitHub
- write user documentation into README.md
- review DEVELOPER.md and remove stuff that's not applicable
- upgrade to Python 3.10 and re-test there
