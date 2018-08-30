
#!/usr/bin/env bash
# Splits plain text
#   (by using the tool meant for splitting TSV file,
#   introduces pseudo id and discards it)

tr '\t' ' ' |\
    awk -F '\t' -v OFS='\t' 'NF >= 1 {print NR,$1}' |\
    corenlp-ssplit.scala  -tsv |\
    cut -f2
