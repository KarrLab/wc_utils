#!/usr/bin/env bash
pushd wc_utils/util/chem/
javac GetMajorMicroSpecies.java
jar -cvf GetMajorMicroSpecies.jar GetMajorMicroSpecies.class
popd
