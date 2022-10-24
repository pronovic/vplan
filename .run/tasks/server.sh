# vim: set ft=bash sw=3 ts=3 expandtab:

help_server() {
   echo "- run server: Run the vplan REST server at localhost:8080"
   echo "- run server -r: Run the vplan REST server, removing the database first"
}

task_server() {
   local OPTIND OPTARG option remove

   remove="no"

   while getopts ":r" option; do
     case $option in
       r)
         remove="yes"
         ;;
       ?)
         echo "invalid option -$OPTARG"
         exit 1
         ;;
     esac
   done

   shift $((OPTIND -1))  # pop off the options consumed by getopts

   if [ $remove == "yes" ]; then
      run_task rmdb
   fi

   poetry_run uvicorn vplan.engine.server:API \
      --port 8080 \
      --app-dir src --reload \
      --log-config config/local/vplan/server/logging.yaml \
      --env-file config/local/vplan/server/server.env
}

