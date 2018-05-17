
TOOLS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export SCALA_HOME=~/libs/scala-2.12.4
export JAVA_HOME=~/libs/jdk1.8.0_151
export CORENLP=~/libs/stanford-corenlp-full-2017-06-09
export PATH=$TOOLS:$JAVA_HOME/bin:$SCALA_HOME/bin/:$PATH
