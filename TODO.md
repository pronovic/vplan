Remaining work:

- validate rules on create/update and provide feedback
- fix imports to be consistent usage
- refactor to make sure stuff is in the right place (not shared inappropriately)
- handle the AlreadyExistsError sitation - right now we don't ever throw it (??)
- do manual local testing with client and server on Macbook
- test what happens with invalid devices, etc. and figure out how users are supposed to debug it
- adjust build/release process to release wheel and config template to GitHub
- put back coveralls once project is public
