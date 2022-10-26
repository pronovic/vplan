# vim: set ft=bash sw=3 ts=3 expandtab:
# runscript: customized=true

help_vplan() {
   echo "- run vplan: Run the vplan client against localhost:8080"
}

task_vplan() {
   # Note: not poetry_run because I don't want/need error handling here
   poetry run vplan --config config/local/vplan/client/application.yaml "$@"
}

