# vim: set ft=bash sw=3 ts=3 expandtab:

help_vplan() {
   echo "- run vplan: Run the vplan client against localhost:8080"
}

task_vplan() {
   poetry run vplan --config config/local/vplan/client/application.yaml "$@"
}

