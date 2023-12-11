#!/bin/bash

#for n in 1.1.1.1 2.2.2.2
do
  scp_cmd="-i ~/.ssh/key $1 root@$n:/root/src/";
  echo $scp_cmd;
  scp $scp_cmd;
done
