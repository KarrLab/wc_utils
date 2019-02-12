#!/usr/bin/env bash
pushd wc_utils/util/chem/
javac Protonator.java
jar -cvf Protonator.jar Protonator.class
popd
