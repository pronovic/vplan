# vim: set ft=bash sw=3 ts=3 expandtab:

help_rmdb() {
   echo "- run rmdb: Remove the sqlite database files used for local testing"
}

task_rmdb() {
   echo -n "Removing local database..."
   rm -f config/local/vplan/server/db/*.sqlite
   echo "done"
}

