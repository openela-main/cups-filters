# build braille subpackage on Fedora, don't do it on CentOS Stream 9 or older
%if 0%{?fedora} || 0%{?rhel} > 9
%bcond_without braille
%else
%bcond_with braille
%endif

# we build CUPS also with relro
%global _hardened_build 1

Summary: OpenPrinting CUPS filters and backends
Name:    cups-filters
Version: 1.20.0
Release: 32%{?dist}

# For a breakdown of the licensing, see COPYING file
# GPLv2:   filters: commandto*, imagetoraster, pdftops, rasterto*,
#                   imagetopdf, pstopdf, texttopdf
#         backends: parallel, serial
# GPLv2+:  filters: gstopxl, textonly, texttops, imagetops, foomatic-rip
# GPLv3:   filters: bannertopdf
# GPLv3+:  filters: urftopdf, rastertopdf
# LGPLv2+:   utils: cups-browsed
# MIT:     filters: gstoraster, pdftoijs, pdftoopvp, pdftopdf, pdftoraster
License: GPLv2 and GPLv2+ and GPLv3 and GPLv3+ and LGPLv2+ and MIT and BSD with advertising

Url:     http://www.linuxfoundation.org/collaborate/workgroups/openprinting/cups-filters
Source0: http://www.openprinting.org/download/cups-filters/cups-filters-%{version}.tar.xz
Source1: testprint
Source2: lftocrlf.ppd
Source3: lftocrlf

Patch01: cups-filters-createall.patch
Patch02: cups-filters-brftopagedbrf-install.patch
# covscan fixes from upstream
Patch03: cups-filters-covscan.patch
# 1626996 - cups-filters: Sticky EOF behavior in glibc breaks descriptor concatenation using dup2
Patch04: cups-filters-cleareof.patch
# 1609264 - links in man page is wrong - it shows 'cups-browsed' in path, but we 
# have 'cups-filters' in path, because it is shipped in 'cups-filters' package
# instead of 'cups-browsed' as Ubuntu does. I can repack the project later,
# so cups-browsed would have separate sub package, so the link would be correct
Patch05: cups-browsed.8.patch
# change in ghostscript broke printing for several printer models, the fix is to use
# different ghostscript option, taken from upstream
# bugzilla https://bugzilla.redhat.com/show_bug.cgi?id=1712814
Patch06: 0001-foomatic-rip-Changed-Ghostscript-call-to-count-pages.patch
# rebuild and patch for FIPS compliance, backported from upstream (#1605101)
Patch07: pdftopdf-nocrypt.patch
# 1776270 - cups-browsed leaks sockets
Patch08: cups-browsed-socket-leak.patch
# 1677731 - error messages when using cups-browsed
Patch09: cups-browsed-error-messages.patch
# 1813229 - cups-browsed leaks memory
Patch10: cups-browsed-memory-leaks.patch
# 1891681 - [RHEL 8] foomatic-rip files up /var/spool/tmp with temporary files
Patch11: foomatic-remove-tmpfile.patch
# 1889798 - Rebuild cups-filters due to rebase of poppler
Patch12: poppler-20.11.0.patch
# 1894543 - Fix '.setfilladjust' usage after gs upgrade to 9.27
Patch13: 0001-gstoraster-Use-.setfilladjust2-PostScript-command-fo.patch
# 1931603 - cups-browsed doesn't save "-default" options
Patch14: 0001-cups-browsed-Always-save-.-default-option-entries-fr.patch
# 1972981 - cups-browsed doesn't renew DBus subscription in time and all printing comes to a halt
Patch15: cups-browsed-renew.patch
# 1981612 - [RHEL 8] pdftopdf doesn't handle "page-range=10-2147483647" correctly
Patch16: 0001-libcupsfilters-Fix-page-range-like-10-in-pdftopdf-fi.patch
# 2185675 - Edges cropped when printing PostScript document
Patch17: gstoraster-margins.patch
# CVE-2023-24805 cups-filters: remote code execution in cups-filters, beh CUPS backend
Patch18: beh-cve2023.patch

%if %{with braille}
Recommends: %{name}-braille%{?_isa} = %{version}-%{release}
%endif

Requires: cups-filters-libs%{?_isa} = %{version}-%{release}

# gcc and gcc-c++ is not in buildroot by default

# gcc for backends (implicitclass, parallel, serial, backend error handling)
# cupsfilters (colord, color manager...), filter (banners, 
# commandto*, braille, foomatic-rip, imagetoraster, imagetopdf, gstoraster e.g.),
# fontembed, cups-browsed
BuildRequires: gcc
# gcc-c++ for pdftoopvp, pdftopdf
BuildRequires: gcc-c++

BuildRequires: cups-devel
BuildRequires: pkgconfig
# pdftopdf
BuildRequires: pkgconfig(libqpdf)
# pdftops
BuildRequires: poppler-utils
# pdftoijs, pdftoopvp, pdftoraster, gstoraster
BuildRequires: pkgconfig(poppler)
BuildRequires: poppler-cpp-devel
BuildRequires: libjpeg-devel
BuildRequires: libtiff-devel
BuildRequires: pkgconfig(libpng)
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(dbus-1)
BuildRequires: ghostscript
# libijs
BuildRequires: pkgconfig(ijs)
BuildRequires: pkgconfig(freetype2)
BuildRequires: pkgconfig(fontconfig)
BuildRequires: pkgconfig(lcms2)
# cups-browsed
BuildRequires: avahi-devel
BuildRequires: pkgconfig(avahi-glib)
BuildRequires: pkgconfig(glib-2.0)
BuildRequires: systemd

# Make sure we get postscriptdriver tags.
BuildRequires: python3-cups

# Testing font for test scripts.
BuildRequires: dejavu-sans-fonts

# autogen.sh
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool

Requires: cups-filesystem
# poppler required for banner printing and with ghostscript needed when project
# is configured with --with-pdftops=hybrid
Requires: poppler-utils
# 1894543 - just to make sure our filter will work if there is a case when cups-filters
# is updated alone and ghostscript isn't updated. This requirement will make sure we will
# bring along a new ghostscript too.
Requires: ghostscript%{?_isa} >= 0:9.27-1

# texttopdf
Requires: liberation-mono-fonts

# pstopdf
Requires: bc grep sed which

# cups-browsed
# it needs cups.service for running
Requires: cups
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

# recommends avahi and cups-ipptool - it is needed for driverless support,
# but it is useless for older devices and cups servers
Recommends: avahi
Recommends: cups-ipptool

# older installations can still have ghostscript-cups and foomatic-filters
# installed, but they are replaced by cups-filters now. We need to obsolete
# them to have them uninstalled (#1632268)
# rpm complains about unversioned Obsoletes - use NVR bigger than is in RHEL7
# to make the upgrade to RHEL8 work even if RHEL7 obsoleted packages
# get an update
Obsoletes: ghostscript-cups < 9.26-1
Obsoletes: foomatic-filters < 4.0.10-1

%package libs
Summary: OpenPrinting CUPS filters and backends - cupsfilters and fontembed libraries
# LGPLv2: libcupsfilters
# MIT:    libfontembed
License: LGPLv2 and MIT

%package devel
Summary: OpenPrinting CUPS filters and backends - development environment
License: LGPLv2 and MIT
Requires: cups-filters-libs%{?_isa} = %{version}-%{release}

%if %{with braille}
%package braille
Summary: OpenPrinting CUPS filters and backends - braille filters and backend
License: GPLv2+ and MIT
BuildRequires: liblouis-devel
Conflicts: cups-filters < 1.28.7-11
# we need classic pdftopdf and other filters as well
Requires: cups-filters%{?_isa} = %{version}-%{release}
# one of lou_translate (from liblouis-utils package) and
# file2brl (from liblouisutdml-utils package) is used for file conversions:
# => prefer lou_translate from liblouis-utils because liblouis-utils are in
# CentOS Stream
# liblouis-utils for lou_translate
Requires: liblouis-utils
%endif

%description
Contains backends, filters, and other software that was
once part of the core CUPS distribution but is no longer maintained by
Apple Inc. In addition it contains additional filters developed
independently of Apple, especially filters for the PDF-centric printing
workflow introduced by OpenPrinting.

%description libs
This package provides cupsfilters and fontembed libraries.

%description devel
This is the development package for OpenPrinting CUPS filters and backends.

%if %{with braille}
%description braille
The package provides filters and cups-brf backend needed for braille printing.
%endif


%prep
%setup -q

%patch01 -p1 -b .createall
# 1572450 - cupsd: Filter "brftopagedbrf" not found.
%patch02 -p1 -b .brftopagedbrf-install
# covscan fixes from upstream
%patch03 -p1 -b .covscan
# 1626996 - cups-filters: Sticky EOF behavior in glibc breaks descriptor concatenation using dup2
%patch04 -p1 -b .cleareof
# 1609264 - man pages: wrong links in man cups-browsed
%patch05 -p1 -b .manpage
# 1712814 - Removed option from Ghostscript causes breakage of printing by foomatic-rip filter
%patch06 -p1 -b .foomatic-rip-crash
# 1605101 - qpdf: should not re-implement crypto
%patch07 -p1 -b .pdftopdf-nocrypt
# 1776270 - cups-browsed leaks sockets
%patch08 -p1 -b .cups-browsed-socket-leak
# 1677731 - error messages when using cups-browsed
%patch09 -p1 -b .cups-browsed-error-messages
# 1813229 - cups-browsed leaks memory
%patch10 -p1 -b .cups-browsed-memory-leak
# 1891681 - [RHEL 8] foomatic-rip files up /var/spool/tmp with temporary files
%patch11 -p1 -b .remove-tmpfile
# 1889798 - Rebuild cups-filters due to rebase of poppler
%patch12 -p1 -b .poppler2011
# 1894543 - Fix '.setfilladjust' usage after gs upgrade to 9.27
%patch13 -p1 -b .setfilladjust
# 1931603 - cups-browsed doesn't save "-default" options
%patch14 -p1 -b .cups-browsed-save-default-options
# 1972981 - cups-browsed doesn't renew DBus subscription in time and all printing comes to a halt
%patch15 -p1 -b .renew
# 1981612 - [RHEL 8] pdftopdf doesn't handle "page-range=10-2147483647" correctly
%patch16 -p1 -b .ranges
# 2185675 - Edges cropped when printing PostScript document
%patch17 -p1 -b .margins
# CVE-2023-24805 cups-filters: remote code execution in cups-filters, beh CUPS backend
%patch18 -p1 -b .cve202324805


%build
# work-around Rpath
./autogen.sh

# --with-pdftops=hybrid - use Poppler's pdftops instead of Ghostscript for
#                         Brother, Minolta, and Konica Minolta to work around
#                         bugs in the printer's PS interpreters
# --with-rcdir=no - don't install SysV init script
# --enable-auto-setup-driverless - enable automatic setup of IPP network printers
#                                  with driverless support
# --enable-driverless - enable PPD generator for driverless printing in 
#                       /usr/lib/cups/driver, it is for manual setup of 
#                       driverless printers with printer setup tool
# --disable-static - do not build static libraries (becuase of Fedora Packaging
#                    Guidelines)
# --enable-dbus - enable DBus Connection Manager's code
# --disable-silent-rules - verbose build output
# --disable-mutool - mupdf is retired in Fedora, use qpdf

%configure --disable-static \
           --disable-silent-rules \
           --with-pdftops=hybrid \
           --enable-dbus \
           --with-rcdir=no \
           --disable-mutool \
           --enable-driverless \
%if %{with braille}
           --enable-braille \
%else
           --disable-braille \
%endif
           --enable-auto-setup-driverless

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

# Add textonly driver back, but as lftocrlf
# part of 2118406 - texttotext filter strips ESC causing PCL files to be printed improperly
install -p -m 0755 %{SOURCE3} %{buildroot}%{_cups_serverbin}/filter/lftocrlf
install -p -m 0644 %{SOURCE2} %{buildroot}%{_datadir}/ppd/cupsfilters/lftocrlf.ppd

# Don't ship libtool la files.
rm -f %{buildroot}%{_libdir}/lib*.la

# Not sure what is this good for.
rm -f %{buildroot}%{_bindir}/ttfread

rm -f %{buildroot}%{_pkgdocdir}/INSTALL
mkdir -p %{buildroot}%{_pkgdocdir}/fontembed/
cp -p fontembed/README %{buildroot}%{_pkgdocdir}/fontembed/

# systemd unit file
mkdir -p %{buildroot}%{_unitdir}
install -p -m 644 utils/cups-browsed.service %{buildroot}%{_unitdir}

# LSB3.2 requires /usr/bin/foomatic-rip,
# create it temporarily as a relative symlink
ln -sf %{_cups_serverbin}/filter/foomatic-rip %{buildroot}%{_bindir}/foomatic-rip

# Don't ship urftopdf for now (bug #1002947).
rm -f %{buildroot}%{_cups_serverbin}/filter/urftopdf
sed -i '/urftopdf/d' %{buildroot}%{_datadir}/cups/mime/cupsfilters.convs

# Don't ship pdftoopvp for now (bug #1027557).
rm -f %{buildroot}%{_cups_serverbin}/filter/pdftoopvp
rm -f %{buildroot}%{_sysconfdir}/fonts/conf.d/99pdftoopvp.conf

# use pregenerated PDF for test page to workaround the broken bannertopdf filter
# for printers requesting PDF document format (bz#2064606)
install -p -m 644 %{SOURCE1} %{buildroot}%{_datadir}/cups/data/testprint


%check
make check

%post
%systemd_post cups-browsed.service

%preun
%systemd_preun cups-browsed.service

%postun
%systemd_postun_with_restart cups-browsed.service 

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig


%files
%{_pkgdocdir}/README
%{_pkgdocdir}/AUTHORS
%{_pkgdocdir}/NEWS
%config(noreplace) %{_sysconfdir}/cups/cups-browsed.conf
%attr(0755,root,root) %{_cups_serverbin}/backend/parallel
# Serial backend needs to run as root (bug #212577#c4).
%attr(0700,root,root) %{_cups_serverbin}/backend/serial
%attr(0755,root,root) %{_cups_serverbin}/backend/implicitclass
%attr(0755,root,root) %{_cups_serverbin}/backend/beh
%attr(0755,root,root) %{_cups_serverbin}/filter/bannertopdf
%attr(0755,root,root) %{_cups_serverbin}/filter/commandtoescpx
%attr(0755,root,root) %{_cups_serverbin}/filter/commandtopclx
%attr(0755,root,root) %{_cups_serverbin}/filter/foomatic-rip
%attr(0755,root,root) %{_cups_serverbin}/filter/gstopdf
%attr(0755,root,root) %{_cups_serverbin}/filter/gstopxl
%attr(0755,root,root) %{_cups_serverbin}/filter/gstoraster
%attr(0755,root,root) %{_cups_serverbin}/filter/imagetopdf
%attr(0755,root,root) %{_cups_serverbin}/filter/imagetops
%attr(0755,root,root) %{_cups_serverbin}/filter/imagetoraster
# Add textonly driver back, but as lftocrlf
# part of 2118406 - texttotext filter strips ESC causing PCL files to be printed improperly
%attr(0755,root,root) %{_cups_serverbin}/filter/lftocrlf
%attr(0755,root,root) %{_cups_serverbin}/filter/pdftopdf
%attr(0755,root,root) %{_cups_serverbin}/filter/pdftops
%attr(0755,root,root) %{_cups_serverbin}/filter/pdftoraster
%attr(0755,root,root) %{_cups_serverbin}/filter/rastertoescpx
%attr(0755,root,root) %{_cups_serverbin}/filter/rastertopclm
%attr(0755,root,root) %{_cups_serverbin}/filter/rastertopclx
%attr(0755,root,root) %{_cups_serverbin}/filter/rastertopdf
%attr(0755,root,root) %{_cups_serverbin}/filter/rastertops
%attr(0755,root,root) %{_cups_serverbin}/filter/sys5ippprinter
%attr(0755,root,root) %{_cups_serverbin}/filter/texttopdf
%attr(0755,root,root) %{_cups_serverbin}/filter/texttops
%attr(0755,root,root) %{_cups_serverbin}/filter/texttotext
%{_bindir}/foomatic-rip
%{_bindir}/driverless
%{_cups_serverbin}/backend/driverless
%{_cups_serverbin}/driver/driverless
%{_datadir}/cups/banners
%{_datadir}/cups/charsets
%{_datadir}/cups/data/*
# this needs to be in the main package because of cupsfilters.drv
%{_datadir}/cups/ppdc/pcl.h
%{_datadir}/cups/drv/cupsfilters.drv
%{_datadir}/cups/mime/cupsfilters.types
%{_datadir}/cups/mime/cupsfilters.convs
%{_datadir}/cups/mime/cupsfilters-ghostscript.convs
%{_datadir}/cups/mime/cupsfilters-poppler.convs
%{_datadir}/ppd/cupsfilters
%{_sbindir}/cups-browsed
%{_unitdir}/cups-browsed.service
%{_mandir}/man8/cups-browsed.8.gz
%{_mandir}/man5/cups-browsed.conf.5.gz
%{_mandir}/man1/foomatic-rip.1.gz
%{_mandir}/man1/driverless.1.gz

%files libs
%dir %{_pkgdocdir}/
%{_pkgdocdir}/COPYING
%{_pkgdocdir}/fontembed/README
%{_libdir}/libcupsfilters.so.*
%{_libdir}/libfontembed.so.*

%files devel
%{_includedir}/cupsfilters
%{_includedir}/fontembed
%{_datadir}/cups/ppdc/escp.h
%{_libdir}/pkgconfig/libcupsfilters.pc
%{_libdir}/pkgconfig/libfontembed.pc
%{_libdir}/libcupsfilters.so
%{_libdir}/libfontembed.so

%if %{with braille}
%files braille
# cups-brf needs to be run as root, otherwise it leaves error messages
# in journal
%attr(0700,root,root) %{_cups_serverbin}/backend/cups-brf
%attr(0755,root,root) %{_cups_serverbin}/filter/brftoembosser
%attr(0755,root,root) %{_cups_serverbin}/filter/brftopagedbrf
%attr(0755,root,root) %{_cups_serverbin}/filter/imagetobrf
%attr(0755,root,root) %{_cups_serverbin}/filter/imageubrltoindexv3
%attr(0755,root,root) %{_cups_serverbin}/filter/imageubrltoindexv4
%attr(0755,root,root) %{_cups_serverbin}/filter/musicxmltobrf
%attr(0755,root,root) %{_cups_serverbin}/filter/textbrftoindexv3
%attr(0755,root,root) %{_cups_serverbin}/filter/texttobrf
%attr(0755,root,root) %{_cups_serverbin}/filter/vectortobrf
%attr(0755,root,root) %{_cups_serverbin}/filter/vectortopdf
%{_cups_serverbin}/filter/cgmtopdf
%{_cups_serverbin}/filter/cmxtopdf
%{_cups_serverbin}/filter/emftopdf
%{_cups_serverbin}/filter/imagetoubrl
%{_cups_serverbin}/filter/svgtopdf
%{_cups_serverbin}/filter/textbrftoindexv4
%{_cups_serverbin}/filter/vectortoubrl
%{_cups_serverbin}/filter/xfigtopdf
%{_cups_serverbin}/filter/wmftopdf
%{_datadir}/cups/braille
%{_datadir}/cups/drv/generic-brf.drv
%{_datadir}/cups/drv/generic-ubrl.drv
%{_datadir}/cups/drv/indexv3.drv
%{_datadir}/cups/drv/indexv4.drv
%{_datadir}/cups/ppdc/braille.defs
%{_datadir}/cups/ppdc/fr-braille.po
%{_datadir}/cups/ppdc/imagemagick.defs
%{_datadir}/cups/ppdc/index.defs
%{_datadir}/cups/ppdc/liblouis.defs
%{_datadir}/cups/ppdc/liblouis1.defs
%{_datadir}/cups/ppdc/liblouis2.defs
%{_datadir}/cups/ppdc/liblouis3.defs
%{_datadir}/cups/ppdc/liblouis4.defs
%{_datadir}/cups/ppdc/media-braille.defs
%{_datadir}/cups/mime/braille.convs
%{_datadir}/cups/mime/braille.types
%endif

%changelog
* Tue Aug 08 2023 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-32
- 2118406 - texttotext filter strips ESC causing PCL files to be printed improperly

* Wed Jun 07 2023 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-31
- CVE-2023-24805 cups-filters: remote code execution in cups-filters, beh CUPS backend

* Thu Apr 13 2023 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-30
- 2185675 - Edges cropped when printing PostScript document

* Thu Sep 22 2022 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-29
- 2128539 - build braille subpackage only on Fedora and CentOS Stream > 9

* Thu Jun 16 2022 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-28
- 2064606 - [RHEL8.5] Test page is not working if the destination document format is PDF

* Tue Jul 13 2021 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-27
- 1981612 - [RHEL 8] pdftopdf doesn't handle "page-range=10-2147483647" correctly

* Mon Jun 21 2021 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-26
- 1972981 - cups-browsed doesn't renew DBus subscription in time and all printing comes to a halt

* Thu Jun 03 2021 Richard Lescak <zdohnal@redhat.com> - 1.20.0-25
- 1931603 - cups-browsed doesn't save "*-default" options

* Mon Dec 14 2020 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-24
- require the explicit gs version

* Tue Dec 08 2020 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-23
- 1894543 - Fix '.setfilladjust' usage after gs upgrade to 9.27

* Wed Nov 18 2020 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-22
- 1889798 - Rebuild cups-filters due to rebase of poppler

* Tue Oct 27 2020 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-21
- 1891681 - [RHEL 8] foomatic-rip files up /var/spool/tmp with temporary files

* Wed Apr 08 2020 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-20
- 1813229 - cups-browsed leaks memory

* Mon Apr 06 2020 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-20
- 1677731 - error messages when using cups-browsed
- 1776230 - missing dependency for ippfind

* Mon Nov 25 2019 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-19
- 1776270 - cups-browsed leaks sockets

* Mon Sep 02 2019 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-18
- 1605101 - qpdf: should not re-implement crypto

* Wed Aug 07 2019 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-17
- 1738533 - rpm -V failed for /etc/cups/cups-browsed.conf

* Fri Jun 28 2019 Marek Kasik <mkasik@redhat.com> - 1.20.0-16
- Rebuild due to soname bump in poppler-0.66.0-21
- Resolves: #1715836

* Thu May 23 2019 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-15
- 1712814 - Removed option from Ghostscript causes breakage of printing by foomatic-rip filter

* Mon Nov 12 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-14
- 1609264 - man pages: wrong links in man cups-browsed

* Fri Sep 21 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-13
- 1602470 - covscan fixes from upstream
- 1632268 - cups-filters needs to obsolete ghostscript-cups and foomatic-filters
- 1626996 - cups-filters: Sticky EOF behavior in glibc breaks descriptor concatenation using dup2

* Tue Jul 24 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-12
- correcting license

* Thu Jul 12 2018 Marek Kasik <mkasik@redhat.com> - 1.20.0-11
- Rebuild for poppler-0.66.0

* Tue Jun 12 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-10
- requires ghostscript and poppler-utils 

* Tue Jun 12 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-9
- cups-browsed needs cups.service to run

* Fri Apr 27 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-8
- 1572450 - cupsd: Filter "brftopagedbrf" not found.

* Thu Apr 05 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-7
- dependency on poppler-utils is now only recommended

* Mon Feb 19 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-6
- gcc and gcc-c++ is no longer in buildroot by default

* Wed Feb 14 2018 David Tardon <dtardon@redhat.com> - 1.20.0-5
- rebuild for poppler 0.62.0

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1.20.0-4
- Escape macros in %%changelog

* Thu Feb 08 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-3
- remove old stuff https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/thread/MRWOMRZ6KPCV25EFHJ2O67BCCP3L4Y6N/

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.20.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 30 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.20.0-1
- Rebase to 1.20.0

* Sat Jan 20 2018 Björn Esser <besser82@fedoraproject.org> - 1.19.0-2
- Rebuilt for switch to libxcrypt

* Tue Jan 16 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.19.0-1
- Rebase to 1.19.0

* Thu Jan 11 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.9-5
- adding build dependency on ghostscript because of its package changes

* Tue Jan 02 2018 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.9-4
- 1529680 - set CreateIPPPrintQueues to ALL and LocalRemoteCUPSQueueNaming to RemoteName

* Mon Nov 20 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.9-3
- fixing patch for upstream issue 1413

* Wed Nov 08 2017 David Tardon <dtardon@redhat.com> - 1.17.9-2
- rebuild for poppler 0.61.0

* Wed Oct 18 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.9-1
- rebase to 1.17.9

* Mon Oct 09 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.8-4
- removing Provides ghostscript-cups and foomatic-filters

* Fri Oct 06 2017 David Tardon <dtardon@redhat.com> - 1.17.8-3
- rebuild for poppler 0.60.1

* Fri Oct 06 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.8-2
- upstream 1413 - Propagation of location doesn't work

* Tue Oct 03 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.8-1
- rebase to 1.17.8

* Tue Sep 19 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.7-1
- rebase to 1.17.7

* Fri Sep 08 2017 David Tardon <dtardon@redhat.com> - 1.17.2-2
- rebuild for poppler 0.59.0

* Wed Sep 06 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.17.2-1
- rebase to 1.17.2

* Tue Aug 22 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.16.3-1
- rebase to 1.16.3

* Mon Aug 14 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.16.1-1
- rebase to 1.16.1

* Thu Aug 10 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.16.0-2
- rebuilt for qpdf-libs

* Mon Aug 07 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.16.0-1
- rebase to 1.16.0

* Thu Aug 03 2017 David Tardon <dtardon@redhat.com> - 1.14.1-5
- rebuild for poppler 0.57.0

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.14.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.14.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jul 03 2017 Jonathan Wakely <jwakely@redhat.com> - 1.14.1-2
- Rebuilt for Boost 1.64

* Fri Jun 30 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.14.1-1
- rebase to 1.14.1

* Thu Jun 29 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.14.0-3
- update python Requires/BuildRequires accordingly to Fedora Guidelines for Python (python-cups -> python3-cups)

* Wed May 31 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.14.0-2
- removing BuildRequires: mupdf

* Wed May 17 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.14.0-1
- rebase to 1.14.0

* Fri Apr 28 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.13.5-1
- rebase to 1.13.5

* Tue Mar 28 2017 David Tardon <dtardon@redhat.com> - 1.13.4-2
- rebuild for poppler 0.53.0

* Fri Feb 24 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.13.4-1
- rebase to 1.13.4
- 1426567 - Added queues are not marked as remote ones

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.13.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Jan 27 2017 Jonathan Wakely <jwakely@redhat.com> - 1.13.3-3
- Rebuilt for Boost 1.63

* Fri Jan 27 2017 Jonathan Wakely <jwakely@redhat.com> - 1.13.3-2
- Rebuilt for Boost 1.63

* Thu Jan 19 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.13.3-1
- rebase to 1.13.3

* Mon Jan 02 2017 Zdenek Dohnal <zdohnal@redhat.com> - 1.13.2-1
- rebase to 1.13.2

* Mon Dec 19 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.13.1-1
- rebase to 1.13.1

* Fri Dec 16 2016 David Tardon <dtardon@redhat.com> - 1.13.0-2
- rebuild for poppler 0.50.0

* Mon Dec 12 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.13.0-1
- rebase to 1.13.0

* Fri Dec 02 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.12.0-2
- adding new sources

* Fri Dec 02 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.12.0-1
- rebase to 1.12.0

* Wed Nov 23 2016 David Tardon <dtardon@redhat.com> - 1.11.6-2
- rebuild for poppler 0.49.0

* Fri Nov 11 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.11.6-1
- rebase to 1.11.6

* Mon Oct 31 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.11.5-1
- rebase to 1.11.5

* Fri Oct 21 2016 Marek Kasik <mkasik@redhat.com> - 1.11.4-2
- Rebuild for poppler-0.48.0

* Tue Sep 27 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.11.4-1
- rebase to 1.11.4 

* Tue Sep 20 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.11.3-1
- rebase to 1.11.3

* Tue Aug 30 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.11.2-1
- rebase to 1.11.2, adding cupsfilters-poppler.convs and cupsfilters-mupdf.convs into package

* Wed Aug 03 2016 Jiri Popelka <jpopelka@redhat.com> - 1.10.0-3
- %%{_defaultdocdir}/cups-filters/ -> %%{_pkgdocdir}

* Mon Jul 18 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.10.0-2
- adding new sources cups-filters-1.10.0 

* Mon Jul 18 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.10.0-1
- rebase 1.10.0, include missing ppd.h

* Mon Jul 18 2016 Marek Kasik <mkasik@redhat.com> - 1.9.0-2
- Rebuild for poppler-0.45.0

* Fri Jun 10 2016 Jiri Popelka <jpopelka@redhat.com> - 1.9.0-1
- 1.9.0

* Tue May  3 2016 Marek Kasik <mkasik@redhat.com> - 1.8.3-2
- Rebuild for poppler-0.43.0

* Thu Mar 24 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.8.3-1
- Update to 1.8.3, adding cupsfilters-ghostscript.convs to %%files

* Fri Feb 12 2016 Jiri Popelka <jpopelka@redhat.com> - 1.8.2-1
- 1.8.2

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Jan 22 2016 Marek Kasik <mkasik@redhat.com> - 1.8.1-2
- Rebuild for poppler-0.40.0

* Fri Jan 22 2016 Jiri Popelka <jpopelka@redhat.com> - 1.8.1-1
- 1.8.1

* Thu Jan 21 2016 Jiri Popelka <jpopelka@redhat.com> - 1.8.0-1
- 1.8.0

* Tue Jan 19 2016 Jiri Popelka <jpopelka@redhat.com> - 1.7.0-1
- 1.7.0

* Fri Jan 15 2016 Jonathan Wakely <jwakely@redhat.com> - 1.6.0-2
- Rebuilt for Boost 1.60

* Thu Jan 14 2016 Jiri Popelka <jpopelka@redhat.com> - 1.6.0-1
- 1.6.0

* Fri Dec 18 2015 Jiri Popelka <jpopelka@redhat.com> - 1.5.0-1
- 1.5.0

* Tue Dec 15 2015 Jiri Popelka <jpopelka@redhat.com> - 1.4.0-1
- 1.4.0

* Wed Dec 09 2015 Jiri Popelka <jpopelka@redhat.com> - 1.3.0-1
- 1.3.0

* Fri Nov 27 2015 Jiri Popelka <jpopelka@redhat.com> - 1.2.0-1
- 1.2.0

* Wed Nov 11 2015 Peter Robinson <pbrobinson@fedoraproject.org> 1.1.0-2
- Rebuild (qpdf-6)

* Tue Oct 27 2015 Jiri Popelka <jpopelka@redhat.com> - 1.1.0-1
- 1.1.0 (version numbering change: minor version = feature, revision = bugfix)

* Sun Sep 13 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.76-1
- 1.0.76

* Tue Sep 08 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.75-1
- 1.0.75

* Thu Aug 27 2015 Jonathan Wakely <jwakely@redhat.com> - 1.0.74-2
- Rebuilt for Boost 1.59

* Wed Aug 26 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.74-1
- 1.0.74

* Wed Aug 19 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.73-1
- 1.0.73 - new implicitclass backend

* Fri Jul 24 2015 David Tardon <dtardon@redhat.com> - 1.0.71-3
- rebuild for Boost 1.58 to fix deps

* Thu Jul 23 2015 Orion Poplawski <orion@cora.nwra.com> - 1.0.71-2
- Add upstream patch for poppler 0.34 support

* Wed Jul 22 2015 Marek Kasik <mkasik@redhat.com> - 1.0.71-2
- Rebuild (poppler-0.34.0)

* Fri Jul 03 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.71-1
- 1.0.71

* Mon Jun 29 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.70-1
- 1.0.70

* Mon Jun 22 2015 Tim Waugh <twaugh@redhat.com> - 1.0.69-3
- Fixes for glib source handling (bug #1228555).

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.69-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Thu Jun 11 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.69-1
- 1.0.69

* Fri Jun  5 2015 Marek Kasik <mkasik@redhat.com> - 1.0.68-2
- Rebuild (poppler-0.33.0)

* Tue Apr 14 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.68-1
- 1.0.68

* Wed Mar 11 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.67-1
- 1.0.67

* Mon Mar 02 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.66-1
- 1.0.66

* Mon Feb 16 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.65-1
- 1.0.65

* Fri Jan 23 2015 Marek Kasik <mkasik@redhat.com> - 1.0.61-3
- Rebuild (poppler-0.30.0)

* Thu Nov 27 2014 Marek Kasik <mkasik@redhat.com> - 1.0.61-2
- Rebuild (poppler-0.28.1)

* Fri Oct 10 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.61-1
- 1.0.61 

* Tue Oct 07 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.60-1
- 1.0.60

* Sun Sep 28 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.59-1
- 1.0.59

* Thu Aug 21 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.58-1
- 1.0.58

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.55-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Aug 15 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.55-2
- Use %%_defaultdocdir instead of %%doc

* Mon Jul 28 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.55-1
- 1.0.55

* Fri Jun 13 2014 Tim Waugh <twaugh@redhat.com> - 1.0.54-4
- Really fix execmem issue (bug #1079534).

* Wed Jun 11 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.54-3
- Remove (F21) pdf-landscape.patch

* Wed Jun 11 2014 Tim Waugh <twaugh@redhat.com> - 1.0.54-2
- Fix build issue (bug #1106101).
- Don't use grep's -P switch in pstopdf as it needs execmem (bug #1079534).
- Return work-around patch for bug #768811.

* Mon Jun 09 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.54-1
- 1.0.54

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.53-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Jun 03 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.53-3
- Remove BuildRequires pkgconfig(lcms). pkgconfig(lcms2) is enough.

* Tue May 13 2014 Marek Kasik <mkasik@redhat.com> - 1.0.53-2
- Rebuild (poppler-0.26.0)

* Mon Apr 28 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.53-1
- 1.0.53

* Wed Apr 23 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.52-2
- Remove pdftoopvp and urftopdf in %%install instead of not building them.

* Tue Apr 08 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.52-1
- 1.0.52

* Wed Apr 02 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.51-1
- 1.0.51 (#1083327)

* Thu Mar 27 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.50-1
- 1.0.50

* Mon Mar 24 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.49-1
- 1.0.49

* Wed Mar 12 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.48-1
- 1.0.48

* Tue Mar 11 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.47-2
- Don't ship pdftoopvp (#1027557) and urftopdf (#1002947).

* Tue Mar 11 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.47-1
- 1.0.47: CVE-2013-6473 CVE-2013-6476 CVE-2013-6474 CVE-2013-6475 (#1074840)

* Mon Mar 10 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.46-3
- BuildRequires: pkgconfig(foo) instead of foo-devel

* Tue Mar  4 2014 Tim Waugh <twaugh@redhat.com> - 1.0.46-2
- The texttopdf filter requires a TrueType monospaced font
  (bug #1070729).

* Thu Feb 20 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.46-1
- 1.0.46

* Fri Feb 14 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.45-1
- 1.0.45

* Mon Jan 20 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.44-1
- 1.0.44

* Tue Jan 14 2014 Jiri Popelka <jpopelka@redhat.com> - 1.0.43-2
- add /usr/bin/foomatic-rip symlink, due to LSB3.2 (#1052452)

* Fri Dec 20 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.43-1
- 1.0.43: upstream fix for bug #768811 (pdf-landscape)

* Sat Nov 30 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.42-1
- 1.0.42: includes foomatic-rip (obsoletes foomatic-filters package)

* Tue Nov 19 2013 Tim Waugh <twaugh@redhat.com> - 1.0.41-4
- Adjust filter costs so application/vnd.adobe-read-postscript input
  doesn't go via pstotiff (bug #1008166).

* Thu Nov 14 2013 Jaromír Končický <jkoncick@redhat.com> - 1.0.41-3
- Fix memory leaks in cups-browsed (bug #1027317).

* Wed Nov  6 2013 Tim Waugh <twaugh@redhat.com> - 1.0.41-2
- Include dbus so that colord support works (bug #1026928).

* Wed Oct 30 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.41-1
- 1.0.41 - PPD-less printing support

* Mon Oct 21 2013 Tim Waugh <twaugh@redhat.com> - 1.0.40-4
- Fix socket leaks in the BrowsePoll code (bug #1021512).

* Wed Oct 16 2013 Tim Waugh <twaugh@redhat.com> - 1.0.40-3
- Ship the gstoraster MIME conversion rule now we provide that filter
  (bug #1019261).

* Fri Oct 11 2013 Tim Waugh <twaugh@redhat.com> - 1.0.40-2
- Fix PDF landscape printing (bug #768811).

* Fri Oct 11 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.40-1
- 1.0.40
- Use new "hybrid" pdftops renderer.

* Thu Oct 03 2013 Jaromír Končický <jkoncick@redhat.com> - 1.0.39-1
- 1.0.39
- Removed obsolete patches "pdf-landscape" and "browsepoll-notifications"

* Tue Oct  1 2013 Tim Waugh <twaugh@redhat.com> - 1.0.38-4
- Use IPP notifications for BrowsePoll when possible (bug #975241).

* Tue Oct  1 2013 Tim Waugh <twaugh@redhat.com> - 1.0.38-3
- Fixes for some printf-type format mismatches (bug #1014093).

* Tue Sep 17 2013 Tim Waugh <twaugh@redhat.com> - 1.0.38-2
- Fix landscape printing for PDFs (bug #768811).

* Wed Sep 04 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.38-1
- 1.0.38

* Thu Aug 29 2013 Jaromír Končický <jkoncick@redhat.com> - 1.0.37-1
- 1.0.37.

* Tue Aug 27 2013 Jaromír Končický <jkoncick@redhat.com> - 1.0.36-5
- Added build dependency - font required for running tests

* Tue Aug 27 2013 Jaromír Končický <jkoncick@redhat.com> - 1.0.36-4
- Added checking phase (make check)

* Wed Aug 21 2013 Tim Waugh <twaugh@redhat.com> - 1.0.36-3
- Upstream patch to re-work filter costs (bug #998977). No longer need
  text filter costs patch as paps gets used by default now if
  installed.

* Mon Aug 19 2013 Marek Kasik <mkasik@redhat.com> - 1.0.36-2
- Rebuild (poppler-0.24.0)

* Tue Aug 13 2013 Tim Waugh <twaugh@redhat.com> - 1.0.36-1
- 1.0.36.

* Tue Aug 13 2013 Tim Waugh <twaugh@redhat.com> - 1.0.35-7
- Upstream patch to move in filters from ghostscript.

* Tue Jul 30 2013 Tim Waugh <twaugh@redhat.com> - 1.0.35-6
- Set cost for text filters to 200 so that the paps filter gets
  preference for the time being (bug #988909).

* Wed Jul 24 2013 Tim Waugh <twaugh@redhat.com> - 1.0.35-5
- Handle page-label when printing n-up as well.

* Tue Jul 23 2013 Tim Waugh <twaugh@redhat.com> - 1.0.35-4
- Added support for page-label (bug #987515).

* Thu Jul 11 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.35-3
- Rebuild (qpdf-5.0.0)

* Mon Jul 01 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.35-2
- add cups-browsed(8) and cups-browsed.conf(5)
- don't reverse lookup IP address in URI (#975822)

* Wed Jun 26 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.35-1
- 1.0.35

* Mon Jun 24 2013 Marek Kasik <mkasik@redhat.com> - 1.0.34-9
- Rebuild (poppler-0.22.5)

* Wed Jun 19 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-8
- fix the note we add in cups-browsed.conf

* Wed Jun 12 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-7
- Obsolete cups-php (#971741)

* Wed Jun 05 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-6
- one more cups-browsed leak fixed (#959682)

* Wed Jun 05 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-5
- perl is actually not required by pstopdf, because the calling is in dead code

* Mon Jun 03 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-4
- fix resource leaks and other problems found by Coverity & Valgrind (#959682)

* Wed May 15 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-3
- ship ppdc/pcl.h because of cupsfilters.drv

* Tue May 07 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-2
- pstopdf requires bc (#960315)

* Thu Apr 11 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.34-1
- 1.0.34

* Fri Apr 05 2013 Fridolin Pokorny <fpokorny@redhat.com> - 1.0.33-1
- 1.0.33
- removed cups-filters-1.0.32-null-info.patch, accepted by upstream

* Thu Apr 04 2013 Fridolin Pokorny <fpokorny@redhat.com> - 1.0.32-2
- fixed segfault when info is NULL

* Thu Apr 04 2013 Fridolin Pokorny <fpokorny@redhat.com> - 1.0.32-1
- 1.0.32

* Fri Mar 29 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.31-3
- add note to cups-browsed.conf

* Thu Mar 28 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.31-2
- check cupsd.conf existence prior to grepping it (#928816)

* Fri Mar 22 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.31-1
- 1.0.31

* Tue Mar 19 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.30-4
- revert previous change

* Wed Mar 13 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.30-3
- don't ship banners for now (#919489)

* Tue Mar 12 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.30-2
- move BrowsePoll from cupsd.conf to cups-browsed.conf in %%post

* Fri Mar 08 2013 Jiri Popelka <jpopelka@redhat.com> - 1.0.30-1
- 1.0.30: CUPS browsing and broadcasting in cups-browsed

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.29-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Jan 19 2013 Rex Dieter <rdieter@fedoraproject.org> 1.0.29-3
- backport upstream buildfix for poppler-0.22.x

* Fri Jan 18 2013 Adam Tkac <atkac redhat com> - 1.0.29-2
- rebuild due to "jpeg8-ABI" feature drop

* Thu Jan 03 2013 Jiri Popelka <jpopelka@redhat.com> 1.0.29-1
- 1.0.29

* Wed Jan 02 2013 Jiri Popelka <jpopelka@redhat.com> 1.0.28-1
- 1.0.28: cups-browsed daemon and service

* Thu Nov 29 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.25-1
- 1.0.25

* Fri Sep 07 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.24-1
- 1.0.24

* Wed Aug 22 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.23-1
- 1.0.23: old pdftopdf removed

* Tue Aug 21 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.22-1
- 1.0.22: new pdftopdf (uses qpdf instead of poppler)

* Wed Aug 08 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.20-4
- rebuild

* Thu Aug 02 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.20-3
- commented multiple licensing breakdown (#832130)
- verbose build output

* Thu Aug 02 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.20-2
- BuildRequires: poppler-cpp-devel (to build against poppler-0.20)

* Mon Jul 23 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.20-1
- 1.0.20

* Tue Jul 17 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.19-1
- 1.0.19

* Wed May 30 2012 Jiri Popelka <jpopelka@redhat.com> 1.0.18-1
- initial spec file
