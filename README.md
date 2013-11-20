tools
-----

Scripts which may prove useful in the future. Fancy coding not guaranteed.

#### merge_corpora.py

Merges a sentence aligned parallel corpus into a single file separating the
sentences with `|||`. Usage:

	python merge_corpora.py input_file1 input_file2 output_file

#### split_corpora.py

Splits a sentence aligned parallel corpus into two files eliminating the `|||`
separator. Usage:

	python split_corpora.py input_file output_file1 output_file2

#### crossing_alignments.py

Counts the number of crossing alignments in an alignment file. Usage:

  python crossing_alignments.py alignment_file
