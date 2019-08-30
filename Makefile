# Copyright (c) 2019 King's College London
# Created by the Software Development Team <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT
# or http://opensource.org/licenses/MIT>, or the UPL-1.0 license
# <http://opensource.org/licenses/UPL> at your option. This file may not be
# copied, modified, or distributed except according to those terms.

FETCH=wget

RENAISSANCE_V=0.9.0
RENAISSANCE_JAR=renaissance-gpl-${RENAISSANCE_V}.jar

GRAALCE_V=1.0.0-rc16
GRAALCE_DIR=graalvm-ce-${GRAALCE_V}
GRAALCE_TGZ=graalvm-ce-${GRAALCE_V}-linux-amd64.tar.gz

setup: ${RENAISSANCE_JAR} ${GRAALCE_DIR}

${RENAISSANCE_JAR}:
	${FETCH} https://github.com/renaissance-benchmarks/renaissance/releases/download/v${RENAISSANCE_V}/${RENAISSANCE_JAR}

${GRAALCE_TGZ}:
	${FETCH} https://github.com/oracle/graal/releases/download/vm-${GRAALCE_V}/${GRAALCE_TGZ}

${GRAALCE_DIR}: ${GRAALCE_TGZ}
	tar xfz ${GRAALCE_TGZ}

run-standalone: setup
	sh run_benchmarks.sh

.PHONY: clean
clean:
	rm -rf ${RENAISSANCE_JAR} ${GRAALCE_TGZ} ${GRAALCE_DIR}
