# gui-for-qemu
## Как использовать?
Для начала установите qemu на свой компьютер

### Windows
  Просто скачайте установщик с сайта https://www.qemu.org или посмотрите как установить из командной строки на https://www.qemu.org/download/#windows
### Debian/Ubuntu
  Для полноценной эмуляции системы: "apt-get install qemu-system"
  Для эмуляции бинарных опционов Linux: "apt-get install qemu-user-static"
### Arch
  "pacman -S qemu"
### Fedora
  "dnf install @virtualization"
### Gentoo
  "emerge --ask app-emulation/qemu"
### RHEL/CentOS
  "yum install qemu-kvm"
### SUSE
  "zypper install qemu"
### macOS
  "brew install qemu" или "sudo port install qemu"

После запустите программу Pxvirtual.exe, после запуска появится папка isos, положите в неё iso файл с любой операционной системой и нажмите внизу "Создать ВМ" настройте размер диска и размер оперативной памяти, после настройки выберете появившийся в списке вм виртуальную машину и нажмите кнопку "Запустить".
