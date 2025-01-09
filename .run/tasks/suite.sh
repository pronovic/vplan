# vim: set ft=bash sw=3 ts=3 expandtab:

help_suite() {
   echo "- run suite: Run the complete test suite, as for the GitHub Actions CI build"
}

task_suite() {
   run_command pythonversion --short
   run_task install
   run_task checks
   run_task build
   run_task test -c
   run_command pythonversion
}

