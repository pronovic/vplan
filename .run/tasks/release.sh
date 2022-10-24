# vim: set ft=bash sw=3 ts=3 expandtab:

help_release() {
   echo "- run release: Release a specific version and tag the code"
}

task_release() {
   local version

   run_command tagrelease "$@"
   run_task build

   version=$(poetry version | sed 's/^.* //g')
   echo ""
   echo "*** Version v$version has been released and committed"
   echo ""
   echo "Next, push: git push --follow-tags"
   echo ""
   echo "Then go to: https://github.com/pronovic/vplan/releases/tag/v$version"
   echo ""
   echo "Convert the tag to a release and attach build artifacts:"
   ls -l dist
   echo ""
}

