#!/bin/sh
# Initial Author = Thamme Gowda tg@isi.edu
# Created Date = Dec 1, 2017
# Purpose =  CoreNLP Sentence Splitter
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
[[ -n $CORENLP ]] || { echo "Download, extract and set CORENLP variable to its path. See https://stanfordnlp.github.io/CoreNLP/history.html "; exit 1; }
[[ -d $CORENLP ]] || { echo "CORENLP=$CORENLP doesnot exist"; exit 2; }
CLASSPATH=$(echo $CORENLP//*.jar |tr ' ' ':')
which scala > /dev/null 2>&1 || { echo 'scala not found. Download and add it to PATH. See https://www.scala-lang.org/download/'; exit 3; }
which java &> /dev/null 2>&1 || { echo 'java not found. Download and add it to PATH'; exit 4; }
exec scala -classpath ".:${CLASSPATH}" -savecompiled "$0" "$@"
!#

import java.io.{File, PrintWriter}

import collection.JavaConverters._
import scala.io.Source
import edu.stanford.nlp.pipeline._
import edu.stanford.nlp.ling.CoreAnnotations
import edu.stanford.nlp.util.{CoreMap, PropertiesUtils}


//  Up stream to read input
val input = Source.stdin
// Down Stream to consume output
var output = new PrintWriter(System.out)
val props = PropertiesUtils.asProperties(
  "annotators", "tokenize,ssplit,truecase",
  "ssplit.isOneSentence", "true")
val corenlp = new StanfordCoreNLP(props)

for (line <- input.getLines()) {
  if (!line.trim.isEmpty) {
    val doc = new Annotation(line)
    corenlp.annotate(doc)
    val sentences = doc.get(classOf[CoreAnnotations.SentencesAnnotation]).asScala
    for (sent: CoreMap <- sentences) {
      val toks = sent.get(classOf[CoreAnnotations.TokensAnnotation])
      val res = toks.asScala.map(t => t.get(classOf[CoreAnnotations.TrueCaseTextAnnotation]))
      output.println(res.mkString(" "))
    }
    //output.println() // empty line between records
  }
}

// output.flush()
output.close()

