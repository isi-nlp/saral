#!/bin/sh
# Initial Author = Thamme Gowda tg@isi.edu
# Created Date = May 12, 2018
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLASSPATH=`echo $DIR $DIR/stanford-corenlp-full-*/* |tr ' ' ':'`
export PATH="${PATH}:`echo $DIR/scala-*/bin`"
which scala > /dev/null; [[ $? -eq 0 ]] || echo 'scala not found. Download and add it to PATH. See https://www.scala-lang.org/download/'
exec scala -J-Xmx2g -classpath ".:$CLASSPATH" -savecompiled "$0" "$@"
!#

import java.io.{File, PrintWriter}
import collection.JavaConversions._
import scala.io.Source
import edu.stanford.nlp.pipeline._
import edu.stanford.nlp.util.PropertiesUtils

val input = Source.stdin
var out = System.out

val props = PropertiesUtils.asProperties(
  "annotators", "tokenize, ssplit, pos, lemma, ner",
  "ner.model", "edu/stanford/nlp/models/ner/english.conll.4class.distsim.crf.ser.gz",
  "ner.useSUTime", "false",
  "ssplit.isOneSentence", "true")

val nlp = new StanfordCoreNLP(props)
try {
  for (line <- input.getLines()) {
    if (line.trim.isEmpty) {
      println()
    } else {
      val doc = new CoreDocument(line);
      nlp.annotate(doc)
      val sents = doc.sentences()
      assert(sents.size() == 1)
      val sent = sents.get(0)
      val coreToks = sent.tokens()
      val toks = new Array[String](coreToks.size())
      val nerTags = new Array[String](coreToks.size())
      for ((ct, i) <- coreToks.view.zipWithIndex) {
        toks(i) = ct.originalText()
        nerTags(i) = ct.ner()
      }
      out.println(toks.mkString(" ") + "\t" + nerTags.mkString(" "))
    }
  }
} finally {
  out.flush()
}