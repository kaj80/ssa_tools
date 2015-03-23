#!/bin/bash

mpirun -np 17 --host  dev-r-vrt-037,dev-r-vrt-038,dev-r-vrt-039,dev-r-vrt-040,dev-r-vrt-041,dev-r-vrt-042,dev-r-vrt-043,dev-r-vrt-044,dev-r-vrt-045,dev-r-vrt-046,dev-r-vrt-047,r-ufm199,r-ufm200,r-ufm201,r-ufm202,r-ufm203,r-ufm211  --allow-run-as-root --mca btl openib,self --mca btl_openib_cpc_include rdmacm /tmp/ompi_release/imb/src/IMB-MPI1 SendRecv
