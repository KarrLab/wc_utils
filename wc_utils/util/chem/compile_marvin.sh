#!/usr/bin/env bash
pushd wc_utils/util/chem/
javac GetMajorMicroSpecies.java
javac DrawMolecule.java
jar -cvf GetMajorMicroSpecies.jar GetMajorMicroSpecies.class
jar -cvf DrawMolecule.jar DrawMolecule.class
popd
