#!/bin/bash -Ex

. $(dirname $0)/common.sh

export PATH=/hpc/local/bin:$PATH

export jenkins_test_check="yes"
for label in $NODE_LABELS
do
	if [ $label == "SLES12" ]; then
	export jenkins_test_check="no"
        break
    fi
done

install_type=$(get_node_label)

export extra_conf="--enable-openib-rdmacm-ibaddr --enable-mpirun-prefix-by-default --disable-openib-connectx-xrc --with-verbs=/usr/local"

if [ $install_type == "UPSTR" ]; then
	export extra_conf="$extra_conf --with-verbs=/usr/local"
	echo $extra_conf
	cd  $WORKSPACE/ompi

	./autogen.sh && ./configure $extra_conf && make -j && sudo make install
	rc=$?
	if [[ $rc != 0 ]]; then
	       echo "ERROR: OMPI compilation failed"
	       exit $rc
	fi
elif [ $install_type == "MOFED" ]; then
	export extra_conf="$extra_conf --with-verbs=/usr"
	echo $extra_conf

	pkg="openmpi"
	os="sles12sp0"
	arch="x86_64"
	version="3.0"

	pkg_old="`rpm -qa | grep $pkg`"
	if [[ "$pkg_old" ]]; then
		echo "Old version of $pkg was detected ($pkg_old). Uninstalling..."
			sudo rpm -e $pkg_old
		rc=$?
		if [[ $rc != 0 ]]; then
			echo "ERROR: OMPI previous version ($pkg_old) uninstall failed"
			exit $rc
		else
			echo "Finished uninistall"
		fi
	fi

	mofed_dir="/mswg/release/MLNX_OFED/latest-$version"
	mofed_src="`ls $mofed_dir | grep $os | grep $arch$`"
	archive="$mofed_dir/$mofed_src/src/*.tgz"
	rm -rf $WORKSPACE/MLNX_OFED_*
	tar zxvf $archive -C $WORKSPACE

	srpm_name="`ls $WORKSPACE/MLNX_OFED_SRC*/SRPMS/ | grep $pkg`"
	srpm="$WORKSPACE/MLNX_OFED_SRC*/SRPMS/$srpm_name"

	if [[ -z "$srpm" ]]; then
		echo "ERROR: OMPI SRPM extraction failed"
		exit 1
	else
		echo "Source RPM: $srpm"
	fi

	rpmbuild --rebuild --define "_topdir $WORKSPACE/rpmbuild" \
		       --define 'dist %{nil}' --target $arch \
			   --define "_name $pkg" \
			   --define 'mpi_selector /usr/bin/mpi-selector' \
			   --define 'use_mpi_selector 1' \
			   --define 'install_shell_scripts 1' \
			   --define 'shell_scripts_basename mpivars' \
			   --define '_usr /usr' \
			   --define 'ofed 0' \
			   --define '_prefix /usr/local' \
			   --define '_defaultdocdir /usr/local' \
			   --define '_mandir %{_prefix}/share/man' \
			   --define '_datadir %{_prefix}/share' \
			   --define 'mflags -j 4' \
			   --define "configure_options --with-fca=/opt/mellanox/fca \
						       --with-hcoll=/opt/mellanox/hcoll \
						       --with-mxm=/opt/mellanox/mxm \
						       --with-knem=/opt/knem-1.1.2.90mlnx \
						       --with-platform=contrib/platform/mellanox/optimized $extra_conf " \
			   --define 'use_default_rpm_opt_flags 1' $srpm
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "ERROR: OMPI RPM build failed"
		exit $rc
	fi

	export old_rpm="`ofed_info | grep $pkg | grep -v src\.rpm$ | grep $arch$`"
	if [[ "$old_rpm" ]]; then
		sudo rpm -e $old_rpm
	else
		echo "NO $pkg INSTALLED"
	fi

	sudo rpm -i --force $WORKSPACE/rpmbuild/RPMS/$arch/$pkg*.rpm
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "ERROR: OMPI RPM installation failed"
		exit $rc
	fi

	export jenkins_test_build="no"
else
	echo "Node with unknown labels ($NODE_NAME : $NODE_LABELS)"
fi

#cd $WORKSPACE/opensm
#./autogen.sh && ./configure && make -j && sudo make install
#rc=$?
#if [[ $rc != 0 ]]; then
#       echo "ERROR: opensm compilation failed"
#       exit $rc
#fi


jenkins_test_check="no" $WORKSPACE/jenkins_scripts/jenkins/ompi/ompi_jenkins.sh
rc=$?
if [[ $rc != 0 ]]; then
	echo "ERROR: OMPI test failed"
	exit $rc
fi

