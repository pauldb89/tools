#!/usr/bin/python

from optparse import OptionParser
import subprocess
import os

def list_phrases(sentence):
  sentence = sentence.split()
  for l in range(1, 5):
    for i in range(len(sentence) - l + 1):
      yield tuple(sentence[i: i+l])

def extract_common_phrases(reference, translation):
  reference_phrases = set([phrase for phrase in list_phrases(reference)])

  common_phrases = []
  for phrase in list_phrases(translation):
    if phrase in reference_phrases:
      common_phrases.append(phrase)

  return common_phrases

def decode_sentences(key_type, key, entries):
  devnull = open(os.devnull, "w")
  root_exp = "data/wmt09/en-de/clean/experiments/"

  subprocess.call("rm -r evals/" + key_type + "-" + key + "*", shell=True)

  tmp_file = "evals/" + key_type + "-" + key + ".sgm"
  subprocess.call(
      ["head", "-n", str(entries),
       root_exp + key_type + "-" + key + "-grammars.sgm"],
      stdout=open(tmp_file, "w"))

  subprocess.call(
      ["workspace/cdec/training/utils/decode-and-evaluate.pl",
       "-j", "3",
       "-d", "evals",
       "-c", root_exp + "cdec.ini",
       "-w", root_exp + "mira-" + key + "/weights.final",
       "-i", tmp_file],
      stdout=devnull, stderr=devnull)

  root_dir = "evals/" + key_type + "-" + key
  subprocess.call(
      "mv evals/eval." + key_type + "-" + key + ".* " + root_dir, shell=True)

  refs_file = "evals/refs.txt"
  trans_file = "evals/input.txt"
  bleu_scores = open(key_type + "-" + key + ".bleu", "w")
  common_phrases = open(key_type + "-" + key + ".phrases", "w")
  for reference, translation in zip(open(root_dir + "/test.refs"), open(root_dir + "/test.trans")):
    open(refs_file, "w").write(reference)
    open(trans_file, "w").write(translation)
    p = subprocess.Popen(
        ["workspace/cdec/mteval/fast_score", "-i", trans_file, "-r", refs_file],
        stderr=devnull, stdout=subprocess.PIPE)
    p.wait()

    bleu_scores.write(p.communicate()[0])
    common_phrases.write(str(extract_common_phrases(reference, translation)) + "\n")

def main():
  parser = OptionParser()
  parser.add_option("--key_type", dest="key_type", default="dev",
                    help="Type of test set: dev/devtest")
  parser.add_option("--key", dest="key",
                    help="Key to identify grammar and weights file")
  parser.add_option("--entries", dest="entries",
                    help="Number of entries for which to compute BLEU")
  (options, args) = parser.parse_args()

  decode_sentences(options.key_type, options.key, int(options.entries))

if __name__ == "__main__":
  main()
