# Copyright (c) 2019 King's College London
# Created by the Software Development Team <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT
# or http://opensource.org/licenses/MIT>, or the UPL-1.0 license
# <http://opensource.org/licenses/UPL> at your option. This file may not be
# copied, modified, or distributed except according to those terms.

FETCH=wget
PYTHON=python3

RENAISSANCE_V=0.10.0
RENAISSANCE_JAR=renaissance-gpl-${RENAISSANCE_V}.jar

DACAPO_V=9.12
DACAPO_JAR=dacapo-${DACAPO_V}-MR1-bach.jar

SPEC_INSTALL_JAR=SPECjvm2008_1_01_setup.jar
SPEC_DIR=SPECjvm2008_1_01
SPEC_JAR=SPECjvm2008.jar

# For the VMs, we use the latest versions that target JDK11 at the time of writing.
GRAALCE_V=19.3.0
GRAALCE_DIR=graalvm-ce-java11-${GRAALCE_V}
GRAALCE_TGZ=graalvm-ce-java11-linux-amd64-${GRAALCE_V}.tar.gz

J9_V=0.17.0
J9_TGZ=OpenJDK11U-jdk_x64_linux_openj9_11.0.5_10_openj9-${J9_V}.tar.gz
J9_DIR=OpenJDK11U-jdk_x64_linux_openj9_11.0.5_10_openj9-${J9_V}

PATHS_SH=paths.sh

TOP_DIR=`pwd`

setup: ${GRAALCE_DIR} ${J9_DIR} ${RENAISSANCE_JAR} ${DACAPO_JAR} ${SPEC_DIR}/${SPEC_JAR}
	echo OPENJ9_DIR=${TOP_DIR}/${J9_DIR} > ${PATHS_SH}
	echo GRAALCE_DIR=${TOP_DIR}/${GRAALCE_DIR} >> ${PATHS_SH}
	echo RENAISSANCE_JAR=${TOP_DIR}/${RENAISSANCE_JAR} >> ${PATHS_SH}
	echo DACAPO_JAR=${DACAPO_JAR} >> ${PATHS_SH}
	echo SPEC_JAR=${TOP_DIR}/${SPEC_DIR}/${SPEC_JAR} >> ${PATHS_SH}
	echo SPEC_DIR=${TOP_DIR}/${SPEC_DIR} >> ${PATHS_SH}

${RENAISSANCE_JAR}:
	${FETCH} https://github.com/renaissance-benchmarks/renaissance/releases/download/v${RENAISSANCE_V}/${RENAISSANCE_JAR}

${DACAPO_JAR}:
	${FETCH} https://downloads.sourceforge.net/project/dacapobench/${DACAPO_V}-bach-MR1/${DACAPO_JAR}

${SPEC_INSTALL_JAR}:
	${FETCH} http://spec.cs.miami.edu/downloads/osg/java/${SPEC_INSTALL_JAR}

${SPEC_DIR}/${SPEC_JAR}: ${SPEC_INSTALL_JAR}
	# We are downloading from a mirror, as spec.org uses magic to obfuscate
	# their FTP link. To be sure it's the same JAR, we check the md5 hash.
	[ "`md5sum ${SPEC_INSTALL_JAR} | awk '{print $$1}'`" = "144fc07007fc099befd3d51d5992cbcf" ]
	${GRAALCE_DIR}/bin/java -jar SPECjvm2008_1_01_setup.jar \
		-DUSER_INSTALL_DIR=${SPEC_DIR} -i silent
	# To prevent make re-running the installer.
	# (installer extracts with a datestamp from 2009).
	touch ${SPEC_DIR}/${SPEC_JAR}

${GRAALCE_TGZ}:
	${FETCH} https://github.com/graalvm/graalvm-ce-builds/releases/download/vm-${GRAALCE_V}/${GRAALCE_TGZ}

${GRAALCE_DIR}: ${GRAALCE_TGZ}
	tar xfz ${GRAALCE_TGZ}

${J9_TGZ}:
	${FETCH} https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.5%2B10_openj9-${J9_V}/${J9_TGZ}

${J9_DIR}: ${J9_TGZ}
	tar xzf ${J9_TGZ}
	mv jdk-11.0.5+10 ${J9_DIR}

run-standalone: run-renaissance-standalone run-dacapo-standalone run-spec-standalone

run-renaissance-standalone: setup
	sh run_renaissance.sh

run-dacapo-standalone: setup
	${PYTHON} run_dacapo.py

run-spec-standalone: setup
	${PYTHON} run_spec.py

.PHONY: clean
clean:
	rm -rf ${RENAISSANCE_JAR} ${GRAALCE_TGZ} ${GRAALCE_DIR} ${J9_TGZ} \
		${J9_DIR} ${SPEC_DIR} ${SPEC_INSTALL_JAR}
