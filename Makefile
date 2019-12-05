# Copyright (c) 2019 King's College London
# Created by the Software Development Team <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT
# or http://opensource.org/licenses/MIT>, or the UPL-1.0 license
# <http://opensource.org/licenses/UPL> at your option. This file may not be
# copied, modified, or distributed except according to those terms.

FETCH=wget

RENAISSANCE_V=0.10.0
RENAISSANCE_JAR=renaissance-gpl-${RENAISSANCE_V}.jar

# For the VMs, we use the latest versions that target JDK11 at the time of writing.
GRAALCE_V=19.3.0
GRAALCE_DIR=graalvm-ce-java11-${GRAALCE_V}
GRAALCE_TGZ=graalvm-ce-java11-linux-amd64-${GRAALCE_V}.tar.gz

J9_V=0.17.0
J9_TGZ=OpenJDK11U-jdk_x64_linux_openj9_11.0.5_10_openj9-${J9_V}.tar.gz
J9_DIR=OpenJDK11U-jdk_x64_linux_openj9_11.0.5_10_openj9-${J9_V}

PATHS_SH=paths.sh

TOP_DIR=`pwd`

setup: ${RENAISSANCE_JAR} ${GRAALCE_DIR} ${J9_DIR}
	echo OPENJ9_DIR=${TOP_DIR}/${J9_DIR} > ${PATHS_SH}
	echo GRAALCE_DIR=${TOP_DIR}/${GRAALCE_DIR} >> ${PATHS_SH}
	echo RENAISSANCE_JAR=${TOP_DIR}/${RENAISSANCE_JAR} >> ${PATHS_SH}

${RENAISSANCE_JAR}:
	${FETCH} https://github.com/renaissance-benchmarks/renaissance/releases/download/v${RENAISSANCE_V}/${RENAISSANCE_JAR}

${GRAALCE_TGZ}:
	${FETCH} https://github.com/graalvm/graalvm-ce-builds/releases/download/vm-${GRAALCE_V}/${GRAALCE_TGZ}

${GRAALCE_DIR}: ${GRAALCE_TGZ}
	tar xfz ${GRAALCE_TGZ}

${J9_TGZ}:
	${FETCH} https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.5%2B10_openj9-${J9_V}/${J9_TGZ}

${J9_DIR}: ${J9_TGZ}
	tar xzf ${J9_TGZ}
	mv jdk-11.0.5+10 ${J9_DIR}

run-standalone: setup
	sh run_benchmarks.sh

.PHONY: clean
clean:
	rm -rf ${RENAISSANCE_JAR} ${GRAALCE_TGZ} ${GRAALCE_DIR} ${J9_TGZ} ${J9_DIR}
