
TOOLS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export SCALA_HOME=~tg/libs/scala-2.12.4
export JAVA_HOME=~tg/libs/jdk1.8.0_151
export CORENLP=~tg/libs/stanford-corenlp-full-2017-06-09
export MOSES=~tg/libs/mosesdecoder
export PATH=$TOOLS:$JAVA_HOME/bin:$SCALA_HOME/bin/:$PATH
