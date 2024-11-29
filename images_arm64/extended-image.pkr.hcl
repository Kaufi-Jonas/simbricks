
variable "syscores" {
  type    = number
  default = 4
}

variable "memory" {
  type    = string
  default = "4096"
}

variable "outname" {
  type    = string
  default = "extended"
}

variable "base_img" {
  type    = string
  default = "base"
}

variable "compressed" {
  type    = bool
  default = false
}

locals {
  cpus = min(var.syscores, 8)
}

source "qemu" "autogenerated_1" {
  communicator     = "ssh"
  disk_image       = true
  disk_compression = "${var.compressed}"
  format           = "qcow2"
  headless         = true
  iso_checksum     = "none"
  iso_url          = "output-${var.base_img}/${var.base_img}"
  memory           = "${var.memory}"
  net_device       = "virtio-net"
  output_directory = "output-${var.outname}"
  qemuargs         = [["-machine", "virt"],
                      ["-drive", "if=pflash,format=raw,file=efi.img,readonly=on"],
                      ["-drive", "if=pflash,format=raw,file=varstore.img"],
                      ["-drive", "file=output-${var.outname}/${var.outname},if=virtio,cache=writeback,discard=ignore,format=qcow2"],
                      ["-drive", "file=scripts/user-data.img,format=raw"],
                      ["-cpu", "max"], ["-nographic"], ["-smp", "${local.cpus}"]]
  shutdown_command = "sudo shutdown --poweroff --no-wall now"
  ssh_password     = "ubuntu"
  ssh_username     = "ubuntu"
  use_backing_file = "true"
  vm_name          = "${var.outname}"
  ssh_timeout      = "20m"
  ssh_handshake_attempts = 100
}

build {
  sources = ["source.qemu.autogenerated_1"]

  provisioner "file" {
    direction = "upload"
    source = "input-${var.outname}"
    destination = "/tmp/input"
  }

  provisioner "shell" {
    execute_command = "{{ .Vars }} sudo -S -E bash '{{ .Path }}'"
    scripts         = ["scripts/install-${var.outname}.sh", "scripts/cleanup.sh"]
  }

}