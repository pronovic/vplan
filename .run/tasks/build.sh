# vim: set ft=bash sw=3 ts=3 expandtab:
# runscript: customized=true

help_build() {
   echo "- run build: Build artifacts in the dist/ directory"
}

task_build() {
   local version

   run_command poetrybuild

   version=$(poetry version | sed 's/^.* //g')
   tar zcf dist/vplan-config-$version.tar.gz -C config/installed --mode="go-rwx" --owner=github --group=github .
   if [ $? != 0 ]; then
      echo "*** Config bundle step failed."
      exit 1
   fi
}

