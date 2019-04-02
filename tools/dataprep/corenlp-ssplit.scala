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

import collection.JavaConverters._
import scala.io.Source
import edu.stanford.nlp.pipeline._
import edu.stanford.nlp.ling.{CoreAnnotations}
import edu.stanford.nlp.util.{CoreMap, PropertiesUtils}


val props = PropertiesUtils.asProperties(
  "annotators", "tokenize,ssplit",
  "ssplit.isOneSentence", "false")
val corenlp = new StanfordCoreNLP(props)

val minLen = 20

val multiFile = !args.toSet.contains("-tsv")  // TSV and multiFile are exclusive, default is multiFile

  def splitFile(path:String){
    var count = 0
    val lines:Iterator[String] = Source.fromFile(path.trim).getLines()
    val fname = path.trim.split("/").last
    for (line <- lines) {
      if (!line.trim.isEmpty){
        count += 1
        val doc = new Annotation(line)
        corenlp.annotate(doc)
        val sentences = doc.get(classOf[CoreAnnotations.SentencesAnnotation]).asScala
        for (sent: CoreMap <- sentences) {
          print(s"$fname:$count\t")
          println(sent.toString.replace("\t", " "))
        }
      }
    }
  }

  def splitTSV(line:String){
    /*Uses same ID for all the splits */
    val parts = line.split("\t")
    if (parts.length < 2) {
       // error: skip
       return;
    }
     
    val id = parts(0)
    val text = parts(1)
    if (text.split(" +").length > minLen ) {
        val doc = new Annotation(text)
        corenlp.annotate(doc)
        val sentences = doc.get(classOf[CoreAnnotations.SentencesAnnotation]).asScala
        for (sent: CoreMap <- sentences) {
            print(id + "\t")
            println(sent.toString.replace("\t", " "))
        }
    } else {
        println(id + '\t' + text.trim())
    }
  }

for (rec <- Source.stdin.getLines()) {
  if (multiFile) {
    splitFile(rec)
  } else {
    splitTSV(rec)
  }
}

Console.flush()
