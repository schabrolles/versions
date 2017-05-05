%global commit          %{?git_commit_id}
%global shortcommit     %(c=%{commit}; echo ${c:0:7})
%global gitcommittag    .git%{shortcommit}

# Fakeroot only: this package is useful for development in fakeroots. It is not
# available as a base package, though it may be delivered with an approved PCR.
# We redefine base dist here to help this package stand out as fakeroot-only.
#{lua:
#  curdist = rpm.expand("%{?dist}")
#  if string.sub(curdist, 1, 4) == ".mcp" then
#    frootdist = string.gsub(curdist, ".mcp", ".froot")
#    rpm.define("dist "..frootdist)
#  end
#}

# build-time settings that support --with or --without:
#
# = kvmonly =
# Build only KVM-enabled QEMU targets, on KVM-enabled architectures.
#
# Disabled by default.
#
# = exclusive_x86_64 =
# ExclusiveArch: x86_64
#
# Disabled by default, except on RHEL.  Only makes sense with kvmonly.
#
# = rbd =
# Enable rbd support.
#
# Enable by default, except on RHEL.
#
# = separate_kvm =
# Do not build and install stuff that would colide with separately packaged KVM.
#
# Disabled by default, except on EPEL.

%if 0%{?rhel}
# RHEL-specific defaults:
%bcond_without kvmonly          # enabled
%bcond_without exclusive_x86_64 # enabled
%bcond_without rbd              # enabled
%bcond_without spice            # enabled
%bcond_without seccomp          # enabled
%bcond_with    xfsprogs         # enabled
%bcond_with    separate_kvm     # disabled - for EPEL
#bcond_without gtk              # disabled
%else
# General defaults:
%bcond_without kvmonly          # disabled
%bcond_with    exclusive_x86_64 # disabled
%bcond_without rbd              # enabled
%bcond_without spice            # enabled
%bcond_without seccomp          # enabled
%bcond_without xfsprogs         # enabled
%bcond_with    separate_kvm     # disabled
%bcond_without gtk              # enabled
%endif

%global SLOF_gittagdate 20160525

# pkvm wants seccomp
%global have_seccomp 1

%global kvm_archs ppc64 ppc64le
%if %{without separate_kvm}
%global kvm_archs ppc64 ppc64le s390x
%else
%global kvm_archs ppc64 ppc64le s390x
%endif
%if %{with exclusive_x86_64}
%global kvm_archs x86_64 ppc64le
%endif


%global have_usbredir 1

%ifarch %{ix86} x86_64
%if %{with seccomp}
%global have_seccomp 1
%endif
%if %{with spice}
%global have_spice   1
%endif
%else
%if 0%{?rhel}
%global have_usbredir 0
%endif
%endif

%global need_qemu_kvm %{with kvmonly}
%global need_kvm_modfile 0

# These values for system_xyz are overridden below for non-kvmonly builds.
# Instead, these values for kvm_package are overridden below for kvmonly builds.
# Somewhat confusing, but avoids complicated nested conditionals.

%ifarch %{ix86}
%global system_x86    kvm
%global kvm_package   system-x86
%global kvm_target    i386
%global need_qemu_kvm 1
%endif
%ifarch x86_64
%global system_x86    kvm
%global kvm_package   system-x86
%global kvm_target    x86_64
%global need_qemu_kvm 1
%endif
%ifarch ppc64 ppc64le
%global system_ppc    kvm
%global kvm_package   system-ppc
%global kvm_target    ppc64
%global need_kvm_modfile 1
%global need_qemu_kvm 1
%endif
%ifarch s390x
%global system_s390x  kvm
%global kvm_package   system-s390x
%global kvm_target    s390x
%global need_kvm_modfile 1
%endif
%ifarch armv7hl
%global system_arm    kvm
%global kvm_package   system-arm
%global kvm_target    arm
%endif

%if %{with kvmonly}
# If kvmonly, put the qemu-kvm binary in the qemu-kvm package
%global kvm_package   kvm
%else
# If not kvmonly, build all packages and give them normal names. qemu-kvm
# is a simple wrapper package and is only build for archs that support KVM.
%global user          user
%global system_alpha  system-alpha
%global system_arm    system-arm
%global system_cris   system-cris
%global system_lm32   system-lm32
%global system_m68k   system-m68k
%global system_microblaze   system-microblaze
%global system_mips   system-mips
%global system_or32   system-or32
%global system_ppc    system-ppc
%global system_s390x  system-s390x
%global system_sh4    system-sh4
%global system_sparc  system-sparc
%global system_x86    system-x86
%global system_xtensa   system-xtensa
%global system_unicore32   system-unicore32
%global system_moxie   system-moxie
%endif

%undefine user
%undefine system_alpha
%undefine system_arm
%undefine system_cris
%undefine system_lm32
%undefine system_m68k
%undefine system_microblaze
%undefine system_mips
%undefine system_or32
%undefine system_s390x
%undefine system_sh4
%undefine system_sparc
%undefine system_xtensa
%undefine system_unicore32
%undefine system_moxie

# libfdt is only needed to build ARM, Microblaze or PPC emulators
%if 0%{?rhel}
%global need_fdt      0
%else
%if 0%{?system_arm:1}%{?system_microblaze:1}%{?system_ppc:1}
%global need_fdt      1
%endif
%endif

%if 0%{?rhel}
%define with_xen 0
%else
# Xen is available only on i386 x86_64 (from libvirt spec)
%ifnarch %{ix86} x86_64
%define with_xen 0
%else
%define with_xen 1
%endif
%endif

Summary: QEMU is a FAST! processor emulator
Name: qemu
Version: 2.8.0
Release: 8%{gitcommittag}%{?dist}
Epoch: 15
License: GPLv2+ and LGPLv2+ and BSD
Group: Development/Tools
URL: http://www.qemu.org/
# RHEL will build Qemu only on x86_64:
%if %{with kvmonly}
ExclusiveArch: %{kvm_archs}
%endif

# OOM killer breaks builds with parallel make on s390(x)
%ifarch s390 s390x
%define _smp_mflags %{nil}
%endif

Source0:     %{name}.tar.gz

#Source1: qemu.binfmt

# Loads kvm kernel modules at boot
Source2: kvm.modules

# Creates /dev/kvm
Source3: 80-kvm.rules

# KSM control scripts
Source4: ksm.service
Source5: ksm.sysconfig
Source6: ksmctl.c
Source7: ksmtuned.service
Source8: ksmtuned
Source9: ksmtuned.conf

Source10: qemu-guest-agent.service
Source11: 99-qemu-guest-agent.rules
Source12: bridge.conf

# qemu-kvm back compat wrapper
Source13: qemu-kvm-ppc64.sh

BuildRequires: numactl-devel, numactl-libs

%if 0%{?rhel}
BuildRequires: SDL-devel
%else
BuildRequires: SDL2-devel
%endif
BuildRequires: zlib-devel
BuildRequires: which
BuildRequires: chrpath
BuildRequires: texi2html
BuildRequires: gnutls-devel
BuildRequires: cyrus-sasl-devel
BuildRequires: libtool
BuildRequires: libaio-devel
BuildRequires: rsync
BuildRequires: pciutils-devel
BuildRequires: pulseaudio-libs-devel
BuildRequires: libiscsi-devel
BuildRequires: ncurses-devel
BuildRequires: libattr-devel
%if 0%{?have_usbredir:1}
BuildRequires: usbredir-devel >= 0.5.2
%endif
BuildRequires: texinfo
# for /usr/bin/pod2man
%if 0%{?fedora} > 18
BuildRequires: perl-podlators
%endif
%if 0%{?have_spice:1}
BuildRequires: spice-protocol >= 0.12.2
BuildRequires: spice-server-devel >= 0.12.0
%endif
%if 0%{?have_seccomp:1}
BuildRequires: libseccomp-devel >= 2.1.0
%endif
# For network block driver
BuildRequires: libcurl-devel
%if %{with rbd}
# For rbd block driver
#BuildRequires: ceph-devel >= 0.61
BuildRequires: librbd1-devel
BuildRequires: librados2-devel
%endif
# We need both because the 'stap' binary is probed for by configure
BuildRequires: systemtap
BuildRequires: systemtap-sdt-devel
# For smartcard NSS support
BuildRequires: nss-devel
# For XFS discard support in raw-posix.c
%if %{with xfsprogs}
BuildRequires: xfsprogs-devel
%endif
# For VNC JPEG support
BuildRequires: libjpeg-devel
# For VNC PNG support
BuildRequires: libpng-devel
# For uuid generation
BuildRequires: libuuid-devel
# For BlueZ device support
BuildRequires: bluez-libs-devel
# For Braille device support
BuildRequires: brlapi-devel
%if 0%{?need_fdt:1}
# For FDT device tree support
BuildRequires: libfdt-devel
%endif
# For virtfs
BuildRequires: libcap-devel
# Hard requirement for version >= 1.3
BuildRequires: pixman-devel
%if 0%{?fedora} > 18
# For gluster support
BuildRequires: glusterfs-devel >= 3.4.0
BuildRequires: glusterfs-api-devel >= 3.4.0
%endif
# Needed for usb passthrough for qemu >= 1.5
BuildRequires: libusbx-devel
# SSH block driver
%if 0%{?fedora} >= 20
BuildRequires: libssh2-devel
%endif
%if %{with gtk}
# GTK frontend
BuildRequires: gtk3-devel
BuildRequires: vte3-devel
%endif
# GTK translations
BuildRequires: gettext
# RDMA migration
%ifnarch s390 s390x
BuildRequires: librdmacm-devel
%endif
# For sanity test
%if 0%{?fedora} >= 20
BuildRequires: qemu-sanity-check-nodeps
BuildRequires: kernel
%endif
%if %{with_xen}
BuildRequires: xen-devel
%endif

%if 0%{?user:1}
Requires: %{name}-%{user} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_alpha:1}
Requires: %{name}-%{system_alpha} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_arm:1}
Requires: %{name}-%{system_arm} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_cris:1}
Requires: %{name}-%{system_cris} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_lm32:1}
Requires: %{name}-%{system_lm32} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_m68k:1}
Requires: %{name}-%{system_m68k} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_microblaze:1}
Requires: %{name}-%{system_microblaze} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_mips:1}
Requires: %{name}-%{system_mips} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_or32:1}
Requires: %{name}-%{system_or32} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_ppc:1}
Requires: %{name}-%{system_ppc} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_s390x:1}
Requires: %{name}-%{system_s390x} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_sh4:1}
Requires: %{name}-%{system_sh4} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_sparc:1}
Requires: %{name}-%{system_sparc} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_unicore32:1}
Requires: %{name}-%{system_unicore32} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_x86:1}
Requires: %{name}-%{system_x86} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_xtensa:1}
Requires: %{name}-%{system_xtensa} = %{epoch}:%{version}-%{release}
%endif
%if 0%{?system_moxie:1}
Requires: %{name}-%{system_moxie} = %{epoch}:%{version}-%{release}
%endif
%if %{without separate_kvm}
Requires: %{name}-img = %{epoch}:%{version}-%{release}
%else
Requires: %{name}-img
%endif

%define qemudocdir %{_docdir}/%{name}

# ensures we're always chosen over qemu-kvm-ev
%define provide_rhev() \
Provides: %1-rhev = %{epoch}:%{version}-%{release}

%description
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation. QEMU has two operating modes:

 * Full system emulation. In this mode, QEMU emulates a full system (for
   example a PC), including a processor and various peripherials. It can be
   used to launch different Operating Systems without rebooting the PC or
   to debug system code.
 * User mode emulation. In this mode, QEMU can launch Linux processes compiled
   for one CPU on another CPU.

As QEMU requires no host kernel patches to run, it is safe and easy to use.

%if %{without kvmonly}
%ifarch %{kvm_archs}
%package kvm
Summary: QEMU metapackage for KVM support
Group: Development/Tools
Requires: qemu-%{kvm_package} = %{epoch}:%{version}-%{release}
Obsoletes: qemu-kvm-ev
%provide_rhev qemu-kvm

%description kvm
This is a meta-package that provides a qemu-system-<arch> package for native
architectures where kvm can be enabled. For example, in an x86 system, this
will install qemu-system-x86
%endif
%endif

%package  img
Summary: QEMU command line tool for manipulating disk images
Group: Development/Tools
Obsoletes: qemu-img-ev
%provide_rhev qemu-img

%description img
This package provides a command line tool for manipulating disk images

%package  common
Summary: QEMU common files needed by all QEMU targets
Group: Development/Tools
Obsoletes: qemu-kvm-common-ev
%if %{with separate_kvm}
Requires: qemu-kvm-common
%endif
Requires(post): /usr/bin/getent
Requires(post): /usr/sbin/groupadd
Requires(post): /usr/sbin/useradd
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%description common
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the common files needed by all QEMU targets

%package guest-agent
Summary: QEMU guest agent
Group: System Environment/Daemons
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%description guest-agent
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides an agent to run inside guests, which communicates
with the host over a virtio-serial channel named "org.qemu.guest_agent.0"

This package does not need to be installed on the host OS.

%post guest-agent
%systemd_post qemu-guest-agent.service

%preun guest-agent
%systemd_preun qemu-guest-agent.service

%postun guest-agent
%systemd_postun_with_restart qemu-guest-agent.service


%package -n ksm
Summary: Kernel Samepage Merging services
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires(post): systemd-units
Requires(postun): systemd-units
%description -n ksm
Kernel Samepage Merging (KSM) is a memory-saving de-duplication feature,
that merges anonymous (private) pages (not pagecache ones).

This package provides service files for disabling and tuning KSM.


%if 0%{?user:1}
%package %{user}
Summary: QEMU user mode emulation of qemu targets
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires(post): systemd-units
Requires(postun): systemd-units
%description %{user}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the user mode emulation of qemu targets
%endif

%if 0%{?system_x86:1}
%package %{system_x86}
Summary: QEMU system emulator for x86
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Provides: kvm = 85
Obsoletes: kvm < 85
Requires: seavgabios-bin
# First version that ships bios-256k.bin
#Requires: seabios-bin >= 1.7.4-3
Requires: sgabios-bin
#Requires: ipxe-roms-qemu >= 20130517-2.gitc4bce43
Requires: ipxe-roms-qemu
%if 0%{?have_seccomp:1}
Requires: libseccomp >= 1.0.0
%endif

%description %{system_x86}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for x86. When being run in a x86
machine that supports it, this package also provides the KVM virtualization
platform.
%endif

%if 0%{?system_alpha:1}
%package %{system_alpha}
Summary: QEMU system emulator for Alpha
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_alpha}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for Alpha systems.
%endif

%if 0%{?system_arm:1}
%package %{system_arm}
Summary: QEMU system emulator for ARM
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_arm}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for ARM boards.
%endif

%if 0%{?system_mips:1}
%package %{system_mips}
Summary: QEMU system emulator for MIPS
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_mips}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for MIPS boards.
%endif

%if 0%{?system_cris:1}
%package %{system_cris}
Summary: QEMU system emulator for CRIS
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_cris}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for CRIS boards.
%endif

%if 0%{?system_lm32:1}
%package %{system_lm32}
Summary: QEMU system emulator for LatticeMico32
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_lm32}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for LatticeMico32 boards.
%endif

%if 0%{?system_m68k:1}
%package %{system_m68k}
Summary: QEMU system emulator for ColdFire (m68k)
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_m68k}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for ColdFire boards.
%endif

%if 0%{?system_microblaze:1}
%package %{system_microblaze}
Summary: QEMU system emulator for Microblaze
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_microblaze}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for Microblaze boards.
%endif

%if 0%{?system_or32:1}
%package %{system_or32}
Summary: QEMU system emulator for OpenRisc32
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_or32}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for OpenRisc32 boards.
%endif

%if 0%{?system_s390x:1}
%package %{system_s390x}
Summary: QEMU system emulator for S390
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_s390x}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for S390 systems.
%endif

%if 0%{?system_sh4:1}
%package %{system_sh4}
Summary: QEMU system emulator for SH4
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_sh4}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for SH4 boards.
%endif

%if 0%{?system_sparc:1}
%package %{system_sparc}
Summary: QEMU system emulator for SPARC
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires: openbios
%description %{system_sparc}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for SPARC and SPARC64 systems.
%endif

%if 0%{?system_ppc:1}
%package %{system_ppc}
Summary: QEMU system emulator for PPC
Group: Development/Tools
Obsoletes: qemu-kvm-common-ev
Requires: %{name}-common = %{epoch}:%{version}-%{release}
#Requires: openbios
#Requires: SLOF >= 0.1.git%{SLOF_gittagdate}
%description %{system_ppc}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for PPC and PPC64 systems.
%endif

%if 0%{?system_xtensa:1}
%package %{system_xtensa}
Summary: QEMU system emulator for Xtensa
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_xtensa}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for Xtensa boards.
%endif

%if 0%{?system_unicore32:1}
%package %{system_unicore32}
Summary: QEMU system emulator for Unicore32
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_unicore32}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for Unicore32 boards.
%endif

%if 0%{?system_moxie:1}
%package %{system_moxie}
Summary: QEMU system emulator for Moxie
Group: Development/Tools
Requires: %{name}-common = %{epoch}:%{version}-%{release}
%description %{system_moxie}
QEMU is a generic and open source processor emulator which achieves a good
emulation speed by using dynamic translation.

This package provides the system emulator for Moxie boards.
%endif

%ifarch %{kvm_archs}
%package kvm-tools
Summary: KVM debugging and diagnostics tools
Group: Development/Tools

%description kvm-tools
This package contains some diagnostics and debugging tools for KVM.
%endif

%if %{without separate_kvm}
%package -n libcacard
Summary:        Common Access Card (CAC) Emulation
Group:          Development/Libraries

%description -n libcacard
Common Access Card (CAC) emulation library.

%package -n libcacard-tools
Summary:        CAC Emulation tools
Group:          Development/Libraries
Requires:       libcacard = %{epoch}:%{version}-%{release}

%description -n libcacard-tools
CAC emulation tools.

%package -n libcacard-devel
Summary:        CAC Emulation devel
Group:          Development/Libraries
Requires:       libcacard = %{epoch}:%{version}-%{release}

%description -n libcacard-devel
CAC emulation development files.
%endif


%prep
%setup -q -n %{name}



%build
%if %{with kvmonly}
    buildarch="%{kvm_target}-softmmu"
%else
#    buildarch="i386-softmmu x86_64-softmmu alpha-softmmu arm-softmmu \
#    cris-softmmu lm32-softmmu m68k-softmmu microblaze-softmmu \
#    microblazeel-softmmu mips-softmmu mipsel-softmmu mips64-softmmu \
#    mips64el-softmmu or32-softmmu \
#%if 0%{?system_ppc:1}
#    ppc-softmmu ppcemb-softmmu ppc64-softmmu \
#%endif
#    s390x-softmmu sh4-softmmu sh4eb-softmmu \
#%if 0%{?system_sparc:1}
#    sparc-softmmu sparc64-softmmu \
#%endif
#    xtensa-softmmu xtensaeb-softmmu unicore32-softmmu moxie-softmmu \
#    i386-linux-user x86_64-linux-user aarch64-linux-user alpha-linux-user \
#    arm-linux-user armeb-linux-user cris-linux-user m68k-linux-user \
#    microblaze-linux-user microblazeel-linux-user mips-linux-user \
#    mipsel-linux-user mips64-linux-user mips64el-linux-user \
#    mipsn32-linux-user mipsn32el-linux-user \
#    or32-linux-user ppc-linux-user ppc64-linux-user \
#    ppc64abi32-linux-user s390x-linux-user sh4-linux-user sh4eb-linux-user \
#    sparc-linux-user sparc64-linux-user sparc32plus-linux-user \
#    unicore32-linux-user"
    buildarch="ppc64-softmmu"
%endif

# --build-id option is used for giving info to the debug packages.
extraldflags="-Wl,--build-id";
buildldflags="VL_LDFLAGS=-Wl,--build-id"

%ifarch s390
# drop -g flag to prevent memory exhaustion by linker
%global optflags %(echo %{optflags} | sed 's/-g//')
sed -i.debug 's/"-g $CFLAGS"/"$CFLAGS"/g' configure
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --sysconfdir=%{_sysconfdir} \
    --interp-prefix=%{_prefix}/qemu-%%M \
    --localstatedir=%{_localstatedir} \
    --libexecdir=%{_libexecdir} \
    --disable-strip \
    --extra-ldflags="$extraldflags -pie -Wl,-z,relro -Wl,-z,now" \
    --extra-cflags="%{optflags} -fPIE -DPIE -mtune=power8 -mcpu=power8" \
    --disable-werror \
    --target-list="$buildarch" \
    --audio-drv-list=pa,sdl,alsa,oss \
    --enable-kvm \
    --disable-xen \
    --enable-numa \
    --enable-seccomp \
%if 0%{?have_spice:1}
    --enable-spice \
%endif
%if %{without rbd}
    --disable-rbd \
%endif
    --enable-curl \
    "$@"

echo "config-host.mak contents:"
echo "==="
cat config-host.mak
echo "==="

make V=1 %{?_smp_mflags} $buildldflags

gcc %{SOURCE6} -O2 -g -o ksmctl

# Check the binary runs (see eg RHBZ#998722).
#%ifarch %{kvm_archs}
#b="./x86_64-softmmu/qemu-system-x86_64"
#if [ -x "$b" ]; then "$b" -help; fi
#%endif


%install

%define _udevdir /lib/udev/rules.d

install -D -p -m 0744 %{SOURCE4} $RPM_BUILD_ROOT/lib/systemd/system/ksm.service
install -D -p -m 0644 %{SOURCE5} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ksm
install -D -p -m 0755 ksmctl $RPM_BUILD_ROOT/lib/systemd/ksmctl

install -D -p -m 0744 %{SOURCE7} $RPM_BUILD_ROOT/lib/systemd/system/ksmtuned.service
install -D -p -m 0755 %{SOURCE8} $RPM_BUILD_ROOT%{_sbindir}/ksmtuned
install -D -p -m 0644 %{SOURCE9} $RPM_BUILD_ROOT%{_sysconfdir}/ksmtuned.conf

%ifarch %{kvm_archs}
%if 0%{?need_kvm_modfile}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/modules
install -m 0755 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/modules/kvm.modules
%endif

mkdir -p $RPM_BUILD_ROOT%{_bindir}/
mkdir -p $RPM_BUILD_ROOT%{_udevdir}

install -m 0644 %{SOURCE3} $RPM_BUILD_ROOT%{_udevdir}
%endif

make DESTDIR=$RPM_BUILD_ROOT install

#find_lang %{name}

%if 0%{?need_qemu_kvm}
install -m 0755 %{SOURCE13} $RPM_BUILD_ROOT%{_bindir}/qemu-kvm
%endif

%if %{with kvmonly}
rm $RPM_BUILD_ROOT%{_bindir}/qemu-system-%{kvm_target}
rm $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/qemu-system-%{kvm_target}.stp
%endif

chmod -x ${RPM_BUILD_ROOT}%{_mandir}/man1/*
install -D -p -m 0644 -t ${RPM_BUILD_ROOT}%{qemudocdir} Changelog README COPYING COPYING.LIB LICENSE
for emu in $RPM_BUILD_ROOT%{_bindir}/qemu-system-*; do
    ln -sf qemu.1.gz $RPM_BUILD_ROOT%{_mandir}/man1/$(basename $emu).1.gz
done
%if 0%{?need_qemu_kvm}
ln -sf qemu.1.gz $RPM_BUILD_ROOT%{_mandir}/man1/qemu-kvm.1.gz
%endif

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/qemu
install -D -p -m 0644 qemu.sasl $RPM_BUILD_ROOT%{_sysconfdir}/sasl2/qemu.conf
#install -D -p -m 0644 qemu.sasl $RPM_BUILD_ROOT%{_sysconfdir}/qemu/qemu.conf
#install -D -p -m 0644 qemu.sasl $RPM_BUILD_ROOT%{_sysconfdir}/qemu.conf

# Provided by package openbios
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/openbios-ppc
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/openbios-sparc32
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/openbios-sparc64
# Provided by package SLOF
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/slof.bin

# Remove possibly unpackaged files.  Unlike others that are removed
# unconditionally, these firmware files are still distributed as a binary
# together with the qemu package.  We should try to move at least s390-zipl.rom
# to a separate package...  Discussed here on the packaging list:
# https://lists.fedoraproject.org/pipermail/packaging/2012-July/008563.html
%if 0%{!?system_alpha:1}
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/palcode-clipper
%endif
%if 0%{!?system_microblaze:1}
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/petalogix*.dtb
%endif
%if 0%{!?system_ppc:1}
rm -f ${RPM_BUILD_ROOT}%{_datadir}/%{name}/bamboo.dtb
rm -f ${RPM_BUILD_ROOT}%{_datadir}/%{name}/ppc_rom.bin
rm -f ${RPM_BUILD_ROOT}%{_datadir}/%{name}/spapr-rtas.bin
%endif
%if 0%{!?system_s390x:1}
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/s390-zipl.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/s390-ccw.img
%endif
%if 0%{!?system_sparc:1}
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/QEMU,tcx.bin
%endif
%if 0%{!?system_x86:1}
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi-e1000.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi-eepro100.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi-ne2k_pci.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi-pcnet.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi-rtl8139.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi-virtio.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/target-x86_64.conf
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/acpi-dsdt.aml
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/kvmvapic.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/linuxboot.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/multiboot.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/q35-acpi-dsdt.aml
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/qemu-icon.bmp
rm -rf ${RPM_BUILD_ROOT}%{_sysconfdir}/%{name}/target-x86_64.conf
%endif

# Provided by package ipxe
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/pxe*rom
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi*rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/pxe-eepro100.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi-eepro100.rom
# Provided by package seavgabios
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/vgabios*bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/vgabios-virtio.bin
# Provided by package seabios
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/bios.bin
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/bios-256k.bin
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/acpi-dsdt.aml
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/q35-acpi-dsdt.aml
# Provided by package sgabios
#rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/sgabios.bin

%if 0%{?system_x86:1}
# the pxe gpxe images will be symlinks to the images on
# /usr/share/ipxe, as QEMU doesn't know how to look
# for other paths, yet.
pxe_link() {
  ln -s ../ipxe/$2.rom %{buildroot}%{_datadir}/%{name}/pxe-$1.rom
  ln -s ../ipxe.efi/$2.rom %{buildroot}%{_datadir}/%{name}/efi-$1.rom
}

#pxe_link e1000 8086100e
#pxe_link ne2k_pci 10ec8029
#pxe_link pcnet 10222000
#pxe_link rtl8139 10ec8139
#pxe_link virtio 1af41000

rom_link() {
    ln -s $1 %{buildroot}%{_datadir}/%{name}/$2
}

#rom_link ../seavgabios/vgabios-isavga.bin vgabios.bin
#rom_link ../seavgabios/vgabios-cirrus.bin vgabios-cirrus.bin
#rom_link ../seavgabios/vgabios-qxl.bin vgabios-qxl.bin
#rom_link ../seavgabios/vgabios-stdvga.bin vgabios-stdvga.bin
#rom_link ../seavgabios/vgabios-vmware.bin vgabios-vmware.bin
#rom_link ../seabios/bios.bin bios.bin
#rom_link ../seabios/bios-256k.bin bios-256k.bin
#rom_link ../seabios/acpi-dsdt.aml acpi-dsdt.aml
#rom_link ../seabios/q35-acpi-dsdt.aml q35-acpi-dsdt.aml
#rom_link ../sgabios/sgabios.bin sgabios.bin
%endif

%if 0%{?user:1}
mkdir -p $RPM_BUILD_ROOT%{_exec_prefix}/lib/binfmt.d
for i in dummy \
%ifnarch %{ix86} x86_64
    qemu-i386 \
%endif
%ifnarch alpha
    qemu-alpha \
%endif
%ifnarch %{arm}
    qemu-arm \
%endif
    qemu-armeb \
    qemu-cris \
    qemu-microblaze qemu-microblazeel \
%ifnarch mips
    qemu-mips qemu-mips64 \
%endif
%ifnarch mipsel
    qemu-mipsel qemu-mips64el \
%endif
%ifnarch m68k
    qemu-m68k \
%endif
%ifnarch ppc ppc64 ppc64le
    qemu-ppc qemu-ppc64abi32 qemu-ppc64 \
%endif
%ifnarch sparc sparc64
    qemu-sparc qemu-sparc32plus qemu-sparc64 \
%endif
%ifnarch s390 s390x
    qemu-s390x \
%endif
%ifnarch sh4
    qemu-sh4 \
%endif
    qemu-sh4eb \
; do
  test $i = dummy && continue
  grep /$i:\$ qemu.binfmt > $RPM_BUILD_ROOT%{_exec_prefix}/lib/binfmt.d/$i.conf
  chmod 644 $RPM_BUILD_ROOT%{_exec_prefix}/lib/binfmt.d/$i.conf
done < qemu.binfmt
%endif

# For the qemu-guest-agent subpackage install the systemd
# service and udev rules.
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
mkdir -p $RPM_BUILD_ROOT%{_udevdir}
install -m 0644 %{SOURCE10} $RPM_BUILD_ROOT%{_unitdir}
install -m 0644 %{SOURCE11} $RPM_BUILD_ROOT%{_udevdir}

# Install rules to use the bridge helper with libvirt's virbr0
install -m 0644 %{SOURCE12} $RPM_BUILD_ROOT%{_sysconfdir}/qemu
chmod u+s $RPM_BUILD_ROOT%{_libexecdir}/qemu-bridge-helper

find $RPM_BUILD_ROOT -name '*.la' -or -name '*.a' | xargs rm -f
find $RPM_BUILD_ROOT -name "libcacard.so*" -exec chmod +x \{\} \;

%if %{with separate_kvm}
rm -f $RPM_BUILD_ROOT%{_bindir}/kvm_stat
rm -f $RPM_BUILD_ROOT%{_bindir}/qemu-kvm
rm -f $RPM_BUILD_ROOT%{_bindir}/qemu-img
rm -f $RPM_BUILD_ROOT%{_bindir}/qemu-io
rm -f $RPM_BUILD_ROOT%{_bindir}/qemu-nbd
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/qemu-img.1*
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/qemu-kvm.1*
rm -f $RPM_BUILD_ROOT%{_mandir}/man8/qemu-nbd.8*

rm -f $RPM_BUILD_ROOT%{_sbindir}/ksmtuned
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ksmtuned.conf
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ksm
rm -f $RPM_BUILD_ROOT/lib/systemd/ksmctl
rm -f $RPM_BUILD_ROOT/lib/systemd/system/ksm.service
rm -f $RPM_BUILD_ROOT/lib/systemd/system/ksmtuned.service

rm -f $RPM_BUILD_ROOT%{_bindir}/qemu-ga
rm -f $RPM_BUILD_ROOT%{_unitdir}/qemu-guest-agent.service
rm -f $RPM_BUILD_ROOT%{_udevdir}/99-qemu-guest-agent.rules
rm -f $RPM_BUILD_ROOT%{_udevdir}/80-kvm.rules

rm -f $RPM_BUILD_ROOT%{_bindir}/vscclient
rm -f $RPM_BUILD_ROOT%{_libdir}/libcacard*
rm -f $RPM_BUILD_ROOT%{_libdir}/pkgconfig/libcacard.pc
rm -rf $RPM_BUILD_ROOT%{_includedir}/cacard

rm -f $RPM_BUILD_ROOT%{_libexecdir}/qemu-bridge-helper
%endif

# When building using 'rpmbuild' or 'fedpkg local', RPATHs can be left in
# the binaries and libraries (although this doesn't occur when
# building in Koji, for some unknown reason). Some discussion here:
#
# https://lists.fedoraproject.org/pipermail/devel/2013-November/192553.html
#
# In any case it should always be safe to remove RPATHs from
# the final binaries:
#for f in $RPM_BUILD_ROOT%{_bindir}/* $RPM_BUILD_ROOT%{_libdir}/* \
#         $RPM_BUILD_ROOT%{_libexecdir}/*; do
#  if file $f | grep -q ELF; then chrpath --delete $f; fi
#done

#check
# Disabled on aarch64 where it fails with several errors.  Will
# investigate and fix when we have access to real hardware - RWMJ.
# 2014-03-24: Suddenly failing on arm32 as well - crobinso
#ifnarch aarch64 armv7hl
#make check
#endif

# Sanity-check current kernel can boot on this qemu.
# The results are advisory only.
#if 0%{?fedora} >= 20
#ifarch %{arm}
#hostqemu=arm-softmmu/qemu-system-arm
#endif
#ifarch %{ix86}
#hostqemu=i386-softmmu/qemu-system-i386
#endif
#ifarch x86_64
#hostqemu=x86_64-softmmu/qemu-system-x86_64
#endif
#if test -f "$hostqemu"; then qemu-sanity-check --qemu=$hostqemu ||: ; fi
#endif

%ifarch %{kvm_archs}
%post %{kvm_package}
# load kvm modules now, so we can make sure no reboot is needed.
# If there's already a kvm module installed, we don't mess with it
sh %{_sysconfdir}/sysconfig/modules/kvm.modules &> /dev/null || :
setfacl --remove-all /dev/kvm &> /dev/null || :
udevadm trigger --subsystem-match=misc --sysname-match=kvm --action=add || :
%endif

%if %{without separate_kvm}
%post common
getent group kvm >/dev/null || groupadd -g 36 -r kvm
getent group qemu >/dev/null || groupadd -g 107 -r qemu
getent passwd qemu >/dev/null || \
  useradd -r -u 107 -g qemu -G kvm -d / -s /sbin/nologin \
    -c "qemu user" qemu

%post -n ksm
%systemd_post ksm.service
%systemd_post ksmtuned.service
%preun -n ksm
%systemd_preun ksm.service
%systemd_preun ksmtuned.service
%postun -n ksm
%systemd_postun_with_restart ksm.service
%systemd_postun_with_restart ksmtuned.service
%endif

%if %{without separate_kvm}
%post -n libcacard -p /sbin/ldconfig
%postun -n libcacard -p /sbin/ldconfig
%endif

%if 0%{?user:1}
%post %{user}
/bin/systemctl --system try-restart systemd-binfmt.service &>/dev/null || :

%postun %{user}
/bin/systemctl --system try-restart systemd-binfmt.service &>/dev/null || :
%endif

%global kvm_files \
%if 0%{?need_kvm_modfile} \
%{_sysconfdir}/sysconfig/modules/kvm.modules \
%endif \
%{_udevdir}/80-kvm.rules

%if 0%{?need_qemu_kvm}
%global qemu_kvm_files \
%{_bindir}/qemu-kvm \
%{_mandir}/man1/qemu-kvm.1*
%endif

%files
%defattr(-,root,root)

%if %{without separate_kvm}
%ifarch %{kvm_archs}
%files kvm
%defattr(-,root,root)
%endif
%endif

%files common
%defattr(-,root,root)
/etc/qemu
/usr/bin/ivshmem-client
/usr/bin/ivshmem-server
/usr/share/man/man8/qemu-ga.8.gz
%dir %{qemudocdir}
%doc %{qemudocdir}/Changelog
%doc %{qemudocdir}/README
%doc %{qemudocdir}/qemu-doc.html
%doc %{qemudocdir}/COPYING
%doc %{qemudocdir}/COPYING.LIB
%doc %{qemudocdir}/LICENSE
%dir %{_datadir}/%{name}/
#{_datadir}/%{name}/qemu-icon.bmp
%{_datadir}/%{name}/qemu_logo_no_text.svg
%{_datadir}/%{name}/trace-events-all
%{_datadir}/%{name}/keymaps/
%{_mandir}/man1/qemu.1*
%{_mandir}/man1/virtfs-proxy-helper.1*
%{_bindir}/virtfs-proxy-helper
%if %{without separate_kvm}
%attr(4755, root, root) %{_libexecdir}/qemu-bridge-helper
%endif
%config(noreplace) %{_sysconfdir}/sasl2/qemu.conf
#%config(noreplace) %{_sysconfdir}/qemu/qemu.conf
#%config(noreplace) %{_sysconfdir}/qemu.conf
%dir %{_sysconfdir}/qemu
%config(noreplace) %{_sysconfdir}/qemu/bridge.conf
/lib/udev/rules.d/80-kvm.rules

%if %{without separate_kvm}
%files -n ksm
/lib/systemd/system/ksm.service
/lib/systemd/ksmctl
%config(noreplace) %{_sysconfdir}/sysconfig/ksm
/lib/systemd/system/ksmtuned.service
%{_sbindir}/ksmtuned
%config(noreplace) %{_sysconfdir}/ksmtuned.conf
%endif

%if %{without separate_kvm}
%files guest-agent
%defattr(-,root,root,-)
%doc COPYING README
%{_bindir}/qemu-ga
%{_unitdir}/qemu-guest-agent.service
%{_udevdir}/99-qemu-guest-agent.rules
%endif

%if 0%{?user:1}
%files %{user}
%defattr(-,root,root)
%{_exec_prefix}/lib/binfmt.d/qemu-*.conf
%{_bindir}/qemu-i386
%{_bindir}/qemu-x86_64
%{_bindir}/qemu-aarch64
%{_bindir}/qemu-alpha
%{_bindir}/qemu-arm
%{_bindir}/qemu-armeb
%{_bindir}/qemu-cris
%{_bindir}/qemu-m68k
%{_bindir}/qemu-microblaze
%{_bindir}/qemu-microblazeel
%{_bindir}/qemu-mips
%{_bindir}/qemu-mipsel
%{_bindir}/qemu-mips64
%{_bindir}/qemu-mips64el
%{_bindir}/qemu-mipsn32
%{_bindir}/qemu-mipsn32el
%{_bindir}/qemu-or32
%{_bindir}/qemu-ppc
%{_bindir}/qemu-ppc64
%{_bindir}/qemu-ppc64abi32
%{_bindir}/qemu-s390x
%{_bindir}/qemu-sh4
%{_bindir}/qemu-sh4eb
%{_bindir}/qemu-sparc
%{_bindir}/qemu-sparc32plus
%{_bindir}/qemu-sparc64
%{_bindir}/qemu-unicore32
%{_datadir}/systemtap/tapset/qemu-i386.stp
%{_datadir}/systemtap/tapset/qemu-x86_64.stp
%{_datadir}/systemtap/tapset/qemu-aarch64.stp
%{_datadir}/systemtap/tapset/qemu-alpha.stp
%{_datadir}/systemtap/tapset/qemu-arm.stp
%{_datadir}/systemtap/tapset/qemu-armeb.stp
%{_datadir}/systemtap/tapset/qemu-cris.stp
%{_datadir}/systemtap/tapset/qemu-m68k.stp
%{_datadir}/systemtap/tapset/qemu-microblaze.stp
%{_datadir}/systemtap/tapset/qemu-microblazeel.stp
%{_datadir}/systemtap/tapset/qemu-mips.stp
%{_datadir}/systemtap/tapset/qemu-mipsel.stp
%{_datadir}/systemtap/tapset/qemu-mips64.stp
%{_datadir}/systemtap/tapset/qemu-mips64el.stp
%{_datadir}/systemtap/tapset/qemu-mipsn32.stp
%{_datadir}/systemtap/tapset/qemu-mipsn32el.stp
%{_datadir}/systemtap/tapset/qemu-or32.stp
%{_datadir}/systemtap/tapset/qemu-ppc.stp
%{_datadir}/systemtap/tapset/qemu-ppc64.stp
%{_datadir}/systemtap/tapset/qemu-ppc64abi32.stp
%{_datadir}/systemtap/tapset/qemu-s390x.stp
%{_datadir}/systemtap/tapset/qemu-sh4.stp
%{_datadir}/systemtap/tapset/qemu-sh4eb.stp
%{_datadir}/systemtap/tapset/qemu-sparc.stp
%{_datadir}/systemtap/tapset/qemu-sparc32plus.stp
%{_datadir}/systemtap/tapset/qemu-sparc64.stp
%{_datadir}/systemtap/tapset/qemu-unicore32.stp
%endif

%if 0%{?system_x86:1}
%files %{system_x86}
%defattr(-,root,root)
#%if %{without kvmonly}
#%{_bindir}/qemu-system-i386
#%{_bindir}/qemu-system-x86_64
#%{_datadir}/systemtap/tapset/qemu-system-i386.stp
#%{_datadir}/systemtap/tapset/qemu-system-x86_64.stp
#%{_mandir}/man1/qemu-system-i386.1*
#%{_mandir}/man1/qemu-system-x86_64.1*
#%endif
%{_datadir}/%{name}/acpi-dsdt.aml
#%{_datadir}/%{name}/q35-acpi-dsdt.aml
%{_datadir}/%{name}/bios.bin
%{_datadir}/%{name}/bios-256k.bin
%{_datadir}/%{name}/sgabios.bin
%{_datadir}/%{name}/linuxboot.bin
%{_datadir}/%{name}/multiboot.bin
%{_datadir}/%{name}/kvmvapic.bin
%{_datadir}/%{name}/vgabios.bin
%{_datadir}/%{name}/vgabios-cirrus.bin
%{_datadir}/%{name}/vgabios-qxl.bin
%{_datadir}/%{name}/vgabios-stdvga.bin
%{_datadir}/%{name}/vgabios-vmware.bin
%{_datadir}/%{name}/pxe-e1000.rom
%{_datadir}/%{name}/efi-e1000.rom
%{_datadir}/%{name}/pxe-virtio.rom
%{_datadir}/%{name}/efi-virtio.rom
%{_datadir}/%{name}/pxe-pcnet.rom
%{_datadir}/%{name}/efi-pcnet.rom
%{_datadir}/%{name}/pxe-rtl8139.rom
%{_datadir}/%{name}/efi-rtl8139.rom
%{_datadir}/%{name}/pxe-ne2k_pci.rom
%{_datadir}/%{name}/efi-ne2k_pci.rom
#%config(noreplace) %{_sysconfdir}/qemu/target-x86_64.conf
%{_datadir}/%{name}/qemu-icon.bmp
%if %{without separate_kvm}
%ifarch %{ix86} x86_64
%{?kvm_files:}
%{?qemu_kvm_files:}
%endif
%endif
%endif

%if %{without separate_kvm}
%ifarch %{kvm_archs}
%files kvm-tools
%defattr(-,root,root,-)
%endif
%endif

%if 0%{?system_alpha:1}
%files %{system_alpha}
%defattr(-,root,root)
%{_bindir}/qemu-system-alpha
%{_datadir}/systemtap/tapset/qemu-system-alpha.stp
%{_mandir}/man1/qemu-system-alpha.1*
%{_datadir}/%{name}/palcode-clipper
%endif

%if 0%{?system_arm:1}
%files %{system_arm}
%defattr(-,root,root)
%{_bindir}/qemu-system-arm
%{_datadir}/systemtap/tapset/qemu-system-arm.stp
%{_mandir}/man1/qemu-system-arm.1*
%if %{without separate_kvm}
%ifarch armv7hl
%{?kvm_files:}
%{?qemu_kvm_files:}
%endif
%endif

%endif

%if 0%{?system_mips:1}
%files %{system_mips}
%defattr(-,root,root)
%{_bindir}/qemu-system-mips
%{_bindir}/qemu-system-mipsel
%{_bindir}/qemu-system-mips64
%{_bindir}/qemu-system-mips64el
%{_datadir}/systemtap/tapset/qemu-system-mips.stp
%{_datadir}/systemtap/tapset/qemu-system-mipsel.stp
%{_datadir}/systemtap/tapset/qemu-system-mips64el.stp
%{_datadir}/systemtap/tapset/qemu-system-mips64.stp
%{_mandir}/man1/qemu-system-mips.1*
%{_mandir}/man1/qemu-system-mipsel.1*
%{_mandir}/man1/qemu-system-mips64el.1*
%{_mandir}/man1/qemu-system-mips64.1*
%endif

%if 0%{?system_cris:1}
%files %{system_cris}
%defattr(-,root,root)
%{_bindir}/qemu-system-cris
%{_datadir}/systemtap/tapset/qemu-system-cris.stp
%{_mandir}/man1/qemu-system-cris.1*
%endif

%if 0%{?system_lm32:1}
%files %{system_lm32}
%defattr(-,root,root)
%{_bindir}/qemu-system-lm32
%{_datadir}/systemtap/tapset/qemu-system-lm32.stp
%{_mandir}/man1/qemu-system-lm32.1*
%endif

%if 0%{?system_m68k:1}
%files %{system_m68k}
%defattr(-,root,root)
%{_bindir}/qemu-system-m68k
%{_datadir}/systemtap/tapset/qemu-system-m68k.stp
%{_mandir}/man1/qemu-system-m68k.1*
%endif

%if 0%{?system_microblaze:1}
%files %{system_microblaze}
%defattr(-,root,root)
%{_bindir}/qemu-system-microblaze
%{_bindir}/qemu-system-microblazeel
%{_datadir}/systemtap/tapset/qemu-system-microblaze.stp
%{_datadir}/systemtap/tapset/qemu-system-microblazeel.stp
%{_mandir}/man1/qemu-system-microblaze.1*
%{_mandir}/man1/qemu-system-microblazeel.1*
%{_datadir}/%{name}/petalogix*.dtb
%endif

%if 0%{?system_or32:1}
%files %{system_or32}
%defattr(-,root,root)
%{_bindir}/qemu-system-or32
%{_datadir}/systemtap/tapset/qemu-system-or32.stp
%{_mandir}/man1/qemu-system-or32.1*
%endif

%if 0%{?system_s390x:1}
%files %{system_s390x}
%defattr(-,root,root)
%{_bindir}/qemu-system-s390x
%{_datadir}/systemtap/tapset/qemu-system-s390x.stp
%{_mandir}/man1/qemu-system-s390x.1*
%{_datadir}/%{name}/s390-zipl.rom
%{_datadir}/%{name}/s390-ccw.img
%ifarch s390x
%{?kvm_files:}
%{?qemu_kvm_files:}
%endif
%endif

%if 0%{?system_sh4:1}
%files %{system_sh4}
%defattr(-,root,root)
%{_bindir}/qemu-system-sh4
%{_bindir}/qemu-system-sh4eb
%{_datadir}/systemtap/tapset/qemu-system-sh4.stp
%{_datadir}/systemtap/tapset/qemu-system-sh4eb.stp
%{_mandir}/man1/qemu-system-sh4.1*
%{_mandir}/man1/qemu-system-sh4eb.1*
%endif

%if 0%{?system_sparc:1}
%files %{system_sparc}
%defattr(-,root,root)
%{_bindir}/qemu-system-sparc
%{_bindir}/qemu-system-sparc64
%{_datadir}/systemtap/tapset/qemu-system-sparc.stp
%{_datadir}/systemtap/tapset/qemu-system-sparc64.stp
%{_mandir}/man1/qemu-system-sparc.1*
%{_mandir}/man1/qemu-system-sparc64.1*
%{_datadir}/%{name}/QEMU,tcx.bin
%{_datadir}/%{name}/QEMU,cgthree.bin
%else
%exclude %{_datadir}/%{name}/QEMU,cgthree.bin
%endif

%if 0%{?system_ppc:1}
%files %{system_ppc}
%defattr(-,root,root)
%if %{without kvmonly}
#{_bindir}/qemu-system-ppc
%{_bindir}/qemu-system-ppc64
#{_bindir}/qemu-system-ppcemb
#{_datadir}/systemtap/tapset/qemu-system-ppc.stp
#{_datadir}/systemtap/tapset/qemu-system-ppc64.stp
#{_datadir}/systemtap/tapset/qemu-system-ppcemb.stp
#{_mandir}/man1/qemu-system-ppc.1*
%{_mandir}/man1/qemu-system-ppc64.1*
#{_mandir}/man1/qemu-system-ppcemb.1*
%endif
%{_datadir}/%{name}/bamboo.dtb
%{_datadir}/%{name}/ppc_rom.bin
%{_datadir}/%{name}/spapr-rtas.bin
#{_datadir}/%{name}/openbios-ppc
#{_datadir}/%{name}/slof.bin
%{_datadir}/%{name}/u-boot.e500
%ifarch ppc64 ppc64le
%{?kvm_files:}
%{?qemu_kvm_files:}
%endif
%endif

%if 0%{?system_unicore32:1}
%files %{system_unicore32}
%defattr(-,root,root)
%{_bindir}/qemu-system-unicore32
%{_datadir}/systemtap/tapset/qemu-system-unicore32.stp
%{_mandir}/man1/qemu-system-unicore32.1*
%endif

%if 0%{?system_xtensa:1}
%files %{system_xtensa}
%defattr(-,root,root)
%{_bindir}/qemu-system-xtensa
%{_bindir}/qemu-system-xtensaeb
%{_datadir}/systemtap/tapset/qemu-system-xtensa.stp
%{_datadir}/systemtap/tapset/qemu-system-xtensaeb.stp
%{_mandir}/man1/qemu-system-xtensa.1*
%{_mandir}/man1/qemu-system-xtensaeb.1*
%endif

%if 0%{?system_moxie:1}
%files %{system_moxie}
%defattr(-,root,root)
%{_bindir}/qemu-system-moxie
%{_datadir}/systemtap/tapset/qemu-system-moxie.stp
%{_mandir}/man1/qemu-system-moxie.1*
%endif

%if %{without separate_kvm}
%files img
%defattr(-,root,root)
%{_bindir}/qemu-img
%{_bindir}/qemu-io
%{_bindir}/qemu-nbd
%{_mandir}/man1/qemu-img.1*
%{_mandir}/man8/qemu-nbd.8*


%files -n libcacard
%defattr(-,root,root,-)
#%{_libdir}/libcacard.so.*

%files -n libcacard-tools
%defattr(-,root,root,-)
#%{_bindir}/vscclient

%files -n libcacard-devel
%defattr(-,root,root,-)
#%{_includedir}/cacard
#%{_libdir}/libcacard.so
#%{_libdir}/pkgconfig/libcacard.pc
%endif

%changelog
* Wed Mar 29 2017 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 15:2.8.0-8.git
- Updating to 1216973 spapr: fix off-by-one error in spapr_ovec_populate_dt()

* Thu Mar 23 2017 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 15:2.8.0-7.git
- Updating to 2c99cbf spapr: Workaround for broken radix guests

* Wed Mar 15 2017 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 15:2.8.0-6.git27ddb62
- 27ddb62b6526f44c9eff0797ba49b1b14f122f07 numa: make -numa parser dynamically
  allocate CPUs masks

* Wed Mar 08 2017 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 15:2.8.0-5.git733b1b5
- 733b1b5e4c1e5be1fdefa4c7d0933e18e3289fe1 spapr/pci: populate PCI DT in reverse
  order

* Wed Mar 01 2017 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 15:2.8.0-4.gita6ef3e6
- a6ef3e6d8783a5feb1dbb9d5c4c68c2552cdea4b memory: Introduce DEVICE_HOST_ENDIAN for ram device
- 988829739e415805e9cc2642110f92c6cd43350a sysemu: support up to 1024 vCPUs

* Tue Feb 28 2017 Murilo Opsfelder Araújo <muriloo@linux.vnet.ibm.com> - 15:2.8.0-3.gitbb80805
- Obsolete qemu-kvm-common-ev in qemu-common and qemu-system-ppc subpackages

* Mon Feb 27 2017 Murilo Opsfelder Araújo <muriloo@linux.vnet.ibm.com> - 15:2.8.0-2.gitbb80805
- Obsolete qemu-kvm-ev in qemu-kvm subpackage

* Tue Feb 14 2017 Olav Philipp Henschel <olavph@linux.vnet.ibm.com> - 15:2.8.0-1.gitbb80805
- Version update
- Removed files qemu-tech.html and qmp-commands.txt that are not generated anymore
- bb80805d7d5b14e886e769b5938b459a3592d882 vfio/pci: Add support for mmapping MSI-X table
- 9feef08e90c83ee1a0174702e7275e6bdde7dd47 Merge tag v2.8.0 into hostos-devel
- f23c070fbdaa6c594bf4ff70c81e5a59ae64f8b3 Revert spapr_pci: Add numa node id
- 8211cc28de6f87aac44b2d23eeab9bd28216fe3e Revert RAMBlocks: Store page size
- df8977f5ad5511d65bc04844280fd67b9067a0b7 Revert migration/postcopy: Explicitly disallow huge pages
- b55d4399dd23e7ad6f51f96acd509bfc0a17ffb6 Revert virtio-pci: error out when both legacy and modern modes are disabled
- 5560283f5f1aeb846eabe03e7fe9b7c7bce5ad26 Revert vfio: Add support for mmapping sub-page MMIO BARs
- 8261d330398931852c80da9b6ceef455f4785260 Revert spapr_pci: advertise explicit numa IDs even when theres 1 node
- beefae50a9dbdc5f268edec0718dd6416481a4e6 Revert vhost: adapt vhost_verify_ring_mappings() to virtio 1 ring layout
- 76d98639598c7cde6f728642c26596c96361df1a Revert vhost: drop legacy vring layout bits
- 36cffb0c3b91c5da64487d168df9a378ea320a03 Revert virtio: drop virtio_queue_get_ring_{size, addr}()
- 652d3f7579b4a34194dc2fcd4808322353d855fd Revert vfio/pci: Add support for mmapping MSI-X table

* Wed Jan 25 2017 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 15:2.7.0-9
- 169a53efae579f51022612577e7b17c8aead237c vfio/pci: Add support for mmapping
  MSI-X table

* Wed Jan 18 2017 Murilo Opsfelder Araújo <muriloo@linux.vnet.ibm.com> - 15:2.7.0-8
- Obsolete qemu-img-ev in qemu-img subpackage

* Wed Dec 28 2016 Fabiano Rosas <farosas@linux.vnet.ibm.com> - 15:2.7.0-7
- Bump epoch to avoid obsolescence by qemu-kvm-ev in CentOS

* Wed Dec 21 2016 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 11:2.7.0-6
- 18559e1b90ef9b1eb5cd240a80aacf20db50b0bf virtio: drop virtio_queue_get_ring_{size, addr}()
- b0905bf402ff9f65bfa0862a6f6db7a61584cbdb vhost: drop legacy vring layout bits
- ed4c1429e43b1d628ce483a277b773df2a3b5568 vhost: adapt vhost_verify_ring_mappings() to virtio 1 ring layout
- 697c0e654945ebe7e2dba6268243a6498b2578ff spapr_pci: advertise explicit numa IDs even when theres 1 node

* Sat Nov 26 2016 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 11:2.7.0-5
- 697c0e654945ebe7e2dba6268243a6498b2578ff spapr_pci: advertise explicit numa IDs even when theres 1 node
- afb0d801d4a670f0f03daea0d410753d7bc06bac vfio: Add support for mmapping sub-page MMIO BARs

* Wed Nov 09 2016 OpenPOWER Host OS Builds Bot <open-power-host-os-builds-bot@users.noreply.github.com> - 11:2.7.0-4
- afb0d80 vfio: Add support for mmapping sub-page MMIO BARs
- 4f0198b virtio-pci: error out when both legacy and modern modes are disabled

* Thu Nov 3 2016 Mauro S. M. Rodrigues <maurosr@linux.vnet.ibm.com> - 11:2.7.0-3
 - Spec cleanup

* Wed Oct 26 2016 Mauro S. M. Rodrigues <maurosr@linux.vnet.ibm.com> - 11:2.7.0-2.3200.0
- 4f0198b virtio-pci: error out when both legacy and modern modes are disabled
ce7dafe migration/postcopy: Explicitly disallow huge pages
bbbbdda RAMBlocks: Store page size
1b11fa6 spapr_pci: Add numa node id

* Thu Sep 29 2016 Olav Philipp Henschel <olavph@linux.vnet.ibm.com> - 11:2.6.93-9.3200.0
- 1dc33ed Update version for v2.7.0 release
12d2c41 Update version for v2.7.0-rc5 release
56f101e 9pfs: handle walk of .. in the root directory
805b5d9 9pfs: forbid . and .. in file names
fff39a7 9pfs: forbid illegal path names
2b294f6 Merge remote-tracking branch remotes/bonzini/tags/for-upstream into staging
336d588 optionrom: cope with multiple -O options
6160183 Revert Change net/socket.c to use socket_*() functions
135a972 translate: early exit in tb_flush if there is no tcg
b69a553 ui: fix refresh of VNC server surface
e00da55 Merge remote-tracking branch remotes/mst/tags/for_upstream into staging
58a83c6 virtio: decrement vq->inuse in virtqueue_discard()
bccdef6 virtio: recalculate vq->inuse after migration
8c1c230 Fix bsd-user build after d915b7bb
d75aa43 Update version for v2.7.0-rc4 release
62680fa Merge remote-tracking branch remotes/jasowang/tags/net-pull-request into staging
e0af5a0 e1000e: remove internal interrupt flag
67f3280 slirp: fix segv when init failed
5f9f818 test-logging: dont hard-code paths in /tmp
5045570 glib: add compatibility implementation for g_dir_make_tmp()
60c6b79 syscall.c: Redefine IFLA_* enums
aee5f8f Revert syscall.c: Fix build with older linux-headers
02b1ad8 Merge remote-tracking branch remotes/stefanha/tags/block-pull-request into staging
156af3a block: fix possible reorder of flush operations
ce83ee5 block: fix deadlock in bdrv_co_flush
5844365 Merge remote-tracking branch remotes/jasowang/tags/net-pull-request into staging
e9e0a58 net/net: properly handle multiple packets in net_fill_rstate()
47882fa net: vmxnet: use g_new for pkt initialisation
4b887ae Merge remote-tracking branch remotes/famz/tags/docker-pull-request into staging
92b6a16 curl: Cast fd to int for DPRINTF
5f0e775 Update version for v2.7.0-rc3 release

* Tue Aug 30 2016 Mauro S. M. Rodrigues <maurosr@linux.vnet.ibm.com> - 11:2.6.93-7.pkvm3_1_1.3100.0
- Build August, 24th, 2016

* Wed Jun 15 2016 <baseuser@ibm.com>
  Log from git:
- 7d4a58ab9de6d2758451d4f5e55f3612ccc8a885 spapr: Ensure all LMBs are represented in ibm, dynamic-memory
- b7aad279e24050736885cfaab25cde2d6ad1149f KVM: use KVM_CAP_MAX_VCPU_ID
- 8429db691c92405b2896beb96a2b6f5eb9fdeebd kvm: API to obtain max supported mem slots
- 2d3798a64fcd79c265e171512594b7d1e6ed173e spapr: Increase hotpluggable memory slots to 256
- 3b0266f331184a4e8bc6d5b205998eb2cfce5b5e Merge branch 'powerkvm-v3.1.1-base' into powerkvm-v3.1.1
- a44e7321749850e33371a5b62ab44159305fb282 PPC/KVM: early validation of vcpu id
- eac59e673c86b2f76661bdf969672749360327d0 Merge branch 'powerkvm-v3.1.1-base' into powerkvm-v3.1.1
- 105f8b0ca743fa013aa065fcfe878a00fc1de793 seccomp: Add support for ppc/ppc64
- 35635663498415c8b84bff8eafee6f6b7a774e3b Merge branch 'powerkvm-v3.1.1-base' into powerkvm-v3.1.1
- 95baab8fd862c729209ca804f917cc4c1f6e81db vfio/pci: Add support for mmapping sub-page MMIO BARs
- 5becafeb656aaf8a3a2dce5a15659a564a9e715c vfio/pci: Add support for mmapping MSI-X table
- 959589dc113bcd265d47ecc5a0ac0e3f563d42ca vfio: Enable sparse mmap capability
- a7bcfa3b2e01991f30d90621870f8afa09a797cf spapr: Get CPU unplug working again
- 08f061537bbbc45af0d82443a0f8f38e8c82174a Merge tag 'v2.6.0' into powerkvm-v3.1.1-base
- bba386f7086801c48411a5f607d139341bd564cd savevm: fail if migration blockers are present
- 872aa56ba2dbe9dc18ddc2cd9ebb660b75f35758 migration: regain control of images when migration fails to complete
- f5e3235e30487f2a34ad66034412ab61735e6903 qemu/kvm_stat: Powerpc related fixes
- cb4d4484439f18b598304a902c5d2c211cffa679 KVM headers: Sync capabilities numbers
- c2653f81e478fbb02ae207e21170552228fd8396 Merge tag 'v2.6.0' into powerkvm-v3.1.1
- bfc766d38e1fae5767d43845c15c79ac8fa6d6af Update version for v2.6.0 release
- 455e58e3b77004d22125ecd8e3f1ad183c5db771 Merge branch 'powerkvm-v3.1.1-base' into powerkvm-v3.1.1
- b9c5e7ba02079f73d7e79050c9981cab40a499b3 spapr: Memory hot-unplug support
- 6a5003944b0b48a315d8537eeb39c806dbaa6098 spapr: ensure device trees are always associated with DRC
- 860a3b34854d8abe9af9f1eb584691de926ce897 Update version for v2.6.0-rc5 release
- 53db932604dfa7bb9241d132e0173894cf54261c Merge remote-tracking branch 'remotes/kraxel/tags/pull-vga-20160509-1' into staging
- 975eb6a547f809608ccb08c221552f666611af25 Update version for v2.6.0-rc4 release
- 1beb99f787ba110a9de44254e7d62a1cb9117de8 Revert "acpi: mark PMTIMER as unlocked"
- fd3c136b3e1482cd0ec7285d6bc2a3e6a62c38d7 vga: make sure vga register setup for vbe stays intact (CVE-2016-3712).
- 2068192dcccd8a80dddfcc8df6164cf9c26e0fc4 vga: update vga register setup on vbe changes
- 7fa5c2c5dc9f9bf878c1e8669eb9644d70a71e71 vga: factor out vga register setup
- bfa0f151a564a83b5a26f3e917da98674bf3cf62 vga: add vbe_enabled() helper
- 3bf1817079bb0d80c0d8a86a7c7dd0bfe90eb82e vga: fix banked access bounds checking (CVE-2016-3710)
- 277abf15a60f7653bfb05ffb513ed74ffdaea1b7 configure: Check if struct fsxattr is available from linux header
- 20b0f5fef66012e12bde32b14eaa64de2b1b9dbe Merge remote-tracking branch 'remotes/mst/tags/for_upstream' into staging
- 1dbfd7892b66c757fdf67f346be40233adbad80e acpi: fix bios linker loadder COMMAND_ALLOCATE on bigendian host
- 47dac82d8b013a5c7dd044a797ae6727b553959a Merge remote-tracking branch 'remotes/kevin/tags/for-upstream' into staging
- 849880978eb2d9043323e34afb46eae8772a5fc6 Merge remote-tracking branch 'remotes/armbru/tags/pull-qapi-2016-04-29' into staging
- d208c50d9dbf98c0eca337723cd6497653ceb743 vvfat: Fix default volume label
- ebb72c9f066e5f85259e1541a6d3fb5bfd6e73ff vvfat: Fix volume name assertion
- 0a40bdab0d48d9ce0c34bc2d319e44e92e0cc942 qapi: Don't pass NULL to printf in string input visitor
- 0d48dfedc5c2beb418ad4c08b78de14e794bb199 slirp: fix guest network access with darwin host
- 8c4bf97580a7556e3e61b7bc41dedb5958f0b2f9 Merge remote-tracking branch 'remotes/lalrae/tags/mips-20160428' into staging
- 736f85d5db701cc9d464a03b583d4a04606a0dd5 Merge remote-tracking branch 'remotes/armbru/tags/pull-error-2016-04-28' into staging
- 61861eff69279e20428c10be269ce1c1bba2c7b1 Merge remote-tracking branch 'remotes/dgibson/tags/ppc-for-2.6-20160426' into staging
- d96391c1ffeb30a0afa695c86579517c69d9a889 target-mips: Fix RDHWR exception host PC
- 51b9b478cc238ad23a78ffd713f9c18bbc3907e6 qom: -object error messages lost location, restore it
- d9d3aaea0b3fbb5028e20316bdb93359487cd01f replay: Fix dangling location bug in replay_configure()
- 37f32349ea43f41ee8b9a253977ce1e46f576fc7 QemuOpts: Fix qemu_opts_foreach() dangling location regression
- 6fe40882b8ff055a2bdc37106403cfc783ec9303 Merge commit 'f419a62' into powerkvm-v3.1.1
- 9fd6073bf7f572f2d1f17158eac9980d12fe9e00 spapr_drc: fix aborts during DRC-count based hotplug
