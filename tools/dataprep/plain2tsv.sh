
while read f;
do
    i=$(echo $f | sed 's/.*_\([0-9]\+\).txt$/\1/');
    cat -b $f | sed 's/^\s*//' | awk -F '\t' -v i="$i" 'NF >= 2 {print i"_"$1"\t"$2}' ;
done
