while [ 1 ]
do
    echo starting process
    python postprocess/resource_fulltext_process.py process &
    sleep 10m
    pkill -f 'resource_fulltext_process.py'
    echo killed process
done
