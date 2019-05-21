#! /bin/sh

# Copyright (c) 2019 King's College London created by the Software Development Team
# <http://soft-dev.org/>
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0>, or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, or the UPL-1.0 license <http://opensource.org/licenses/UPL>
# at your option. This file may not be copied, modified, or distributed except according to those
# terms.

# This script fetches binary releases of the VM and the benchmarks.

set -e

RENAISSANCE_V="0.9.0"
GRAALCE_V="1.0.0-rc16"

if [ ! -f renaissance-gpl-${RENAISSANCE_V}.jar ]; then
    wget https://github.com/renaissance-benchmarks/renaissance/releases/download/v${RENAISSANCE_V}/renaissance-gpl-${RENAISSANCE_V}.jar
fi

if [ ! -d graalvm-ce-${GRAALCE_V} ]; then
    wget https://github.com/oracle/graal/releases/download/vm-${GRAALCE_V}/graalvm-ce-${GRAALCE_V}-linux-amd64.tar.gz
    tar xfz graalvm-ce-${GRAALCE_V}-linux-amd64.tar.gz
fi
