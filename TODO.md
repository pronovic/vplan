Remaining work:

- Rethink the ownership relationship between account and plan - just have a token table or something (too confusing)
- finish implementing API endpoints 
- unit test API endpoints, hopefully against live in-memory database
- implement SmartThings client code
- unit test client code against captured data from Insomnia
- maybe write round trip acceptance tests with live server?
- do manual local testing with client and server on Macbook
- test what happens with invalid devices, etc. and figure out how users are supposed to debug it
- adjust build/release process to release wheel and config template to GitHub
- upgrade to Python 3.10 and re-test there
