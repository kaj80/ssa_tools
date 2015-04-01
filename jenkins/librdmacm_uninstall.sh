#!/bin/bash

install_dir=$1

if [ -z $install_dir ]; then
	echo "No install dir specified. Exiting ..."
	exit 1
fi

rm -rf $install_dir/bin/cmtime
rm -rf $install_dir/bin/mckey
rm -rf $install_dir/bin/rcopy
rm -rf $install_dir/bin/rdma_*
rm -rf $install_dir/bin/riostream
rm -rf $install_dir/bin/rping
rm -rf $install_dir/bin/rstream
rm -rf $install_dir/bin/ucmatose
rm -rf $install_dir/bin/udaddy
rm -rf $install_dir/bin/udpong
rm -rf $install_dir/include/infiniband/ib.h
rm -rf $install_dir/include/rdma/rdma_cma_abi.h
rm -rf $install_dir/include/rdma/rdma_cma.h
rm -rf $install_dir/include/rdma/rdma_verbs.h
rm -rf $install_dir/include/rdma/rsocket.h
rm -rf $install_dir/lib/librdmacm.*
rm -rf $install_dir/lib/rsocket
rm -rf $install_dir/share/man/man1/mckey.1
rm -rf $install_dir/share/man/man1/rcopy.1
rm -rf $install_dir/share/man/man1/rdma_client.1
rm -rf $install_dir/share/man/man1/rdma_server.1
rm -rf $install_dir/share/man/man1/rdma_xclient.1
rm -rf $install_dir/share/man/man1/rdma_xserver.1
rm -rf $install_dir/share/man/man1/riostream.1
rm -rf $install_dir/share/man/man1/rping.1
rm -rf $install_dir/share/man/man1/rstream.1
rm -rf $install_dir/share/man/man1/ucmatose.1
rm -rf $install_dir/share/man/man1/udaddy.1
rm -rf $install_dir/share/man/man3/rdma_accept.3
rm -rf $install_dir/share/man/man3/rdma_ack_cm_event.3
rm -rf $install_dir/share/man/man3/rdma_bind_addr.3
rm -rf $install_dir/share/man/man3/rdma_connect.3
rm -rf $install_dir/share/man/man3/rdma_create_ep.3
rm -rf $install_dir/share/man/man3/rdma_create_event_channel.3
rm -rf $install_dir/share/man/man3/rdma_create_id.3
rm -rf $install_dir/share/man/man3/rdma_create_qp.3
rm -rf $install_dir/share/man/man3/rdma_create_srq.3
rm -rf $install_dir/share/man/man3/rdma_dereg_mr.3
rm -rf $install_dir/share/man/man3/rdma_destroy_ep.3
rm -rf $install_dir/share/man/man3/rdma_destroy_event_channel.3
rm -rf $install_dir/share/man/man3/rdma_destroy_id.3
rm -rf $install_dir/share/man/man3/rdma_destroy_qp.3
rm -rf $install_dir/share/man/man3/rdma_destroy_srq.3
rm -rf $install_dir/share/man/man3/rdma_disconnect.3
rm -rf $install_dir/share/man/man3/rdma_event_str.3
rm -rf $install_dir/share/man/man3/rdma_free_devices.3
rm -rf $install_dir/share/man/man3/rdma_getaddrinfo.3
rm -rf $install_dir/share/man/man3/rdma_get_cm_event.3
rm -rf $install_dir/share/man/man3/rdma_get_devices.3
rm -rf $install_dir/share/man/man3/rdma_get_dst_port.3
rm -rf $install_dir/share/man/man3/rdma_get_local_addr.3
rm -rf $install_dir/share/man/man3/rdma_get_peer_addr.3
rm -rf $install_dir/share/man/man3/rdma_get_recv_comp.3
rm -rf $install_dir/share/man/man3/rdma_get_request.3
rm -rf $install_dir/share/man/man3/rdma_get_send_comp.3
rm -rf $install_dir/share/man/man3/rdma_get_src_port.3
rm -rf $install_dir/share/man/man3/rdma_join_multicast.3
rm -rf $install_dir/share/man/man3/rdma_leave_multicast.3
rm -rf $install_dir/share/man/man3/rdma_listen.3
rm -rf $install_dir/share/man/man3/rdma_migrate_id.3
rm -rf $install_dir/share/man/man3/rdma_notify.3
rm -rf $install_dir/share/man/man3/rdma_post_read.3
rm -rf $install_dir/share/man/man3/rdma_post_readv.3
rm -rf $install_dir/share/man/man3/rdma_post_recv.3
rm -rf $install_dir/share/man/man3/rdma_post_recvv.3
rm -rf $install_dir/share/man/man3/rdma_post_send.3
rm -rf $install_dir/share/man/man3/rdma_post_sendv.3
rm -rf $install_dir/share/man/man3/rdma_post_ud_send.3
rm -rf $install_dir/share/man/man3/rdma_post_write.3
rm -rf $install_dir/share/man/man3/rdma_post_writev.3
rm -rf $install_dir/share/man/man3/rdma_reg_msgs.3
rm -rf $install_dir/share/man/man3/rdma_reg_read.3
rm -rf $install_dir/share/man/man3/rdma_reg_write.3
rm -rf $install_dir/share/man/man3/rdma_reject.3
rm -rf $install_dir/share/man/man3/rdma_resolve_addr.3
rm -rf $install_dir/share/man/man3/rdma_resolve_route.3
rm -rf $install_dir/share/man/man3/rdma_set_option.3
rm -rf $install_dir/share/man/man7/rdma_cm.7
rm -rf $install_dir/share/man/man7/rsocket.7

echo "Finished uninstalling librdmacm."
