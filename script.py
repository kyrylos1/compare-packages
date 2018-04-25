import argparse
import subprocess
import prettytable

parser = argparse.ArgumentParser()
parser.add_argument("server1", help="Name or ip of sevrer1")
parser.add_argument("server2", help="Name or ip of server2")
parser.add_argument("username", help="Username for accessing the servers")
parser.add_argument("sshkey", help="Path to ssh key for accessing the servers")
args = parser.parse_args()

CMD_TEST = 'test -e /etc/lsb-release'
CMD_REDHAT = "rpm -qa --qf \"%{NAME} %{VERSION}\n\""
CMD_DEB = 'dpkg -l | grep "^ii" | awk "{print \$2, \$3}"'

pkgsonly1 = []
pkgsonly2 = []
pkgsdiff = {}

def package_list(server):
    cmd_ssh = 'ssh -i {} {}@{}'.format(args.sshkey, args.username, server)
    cmd_test = '{} \'{}\''.format(cmd_ssh, CMD_TEST)
    try:
        process = subprocess.run(cmd_test, timeout=10, shell=True, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        if err.returncode == 1:
            process = False
        else:
            print("Failed command execution for server {0}.\nError output: {1}\nFailed command: {2}".format(server, err.stderr.decode('utf-8').rstrip("\n"), cmd_test))
            exit(1)
    except subprocess.TimeoutExpired as err:
        print("Failed command execution for server {0}.\nTimeout expired (10s).\nFailed command: {1}".format(server, err.cmd))
        exit(1)
    if process:
        cmd_ = CMD_DEB
    else:
        cmd_ = CMD_REDHAT
    cmd_packages = '{} \'{}\''.format(cmd_ssh, cmd_)
    process = subprocess.run(cmd_packages, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stderr:
        print("Failed command execution for server {0}.\nError output: {1}\nFailed command: {2}".format(server, process.stderr.decode('utf-8').rstrip("\n"), cmd_packages))
        exit(1)
    process = process.stdout.decode('utf-8').rstrip().split("\n")
    serverdict = dict([line.split() for line in process])
    return serverdict


server1dict = package_list(args.server1)
server2dict = package_list(args.server2)

for key in server1dict:
    if key not in server2dict:
        pkgsonly1.append(key)
    else:
        if server1dict[key] != server2dict[key]:
            pkgsdiff[key] = [server1dict[key], server2dict[key]]

for key in server2dict:
    if key not in server1dict:
        pkgsonly2.append(key)
        
table = prettytable.PrettyTable(['Package name', args.server1, args.server2])

for item in pkgsdiff:
    table.add_row([item, pkgsdiff[item][0], pkgsdiff[item][1]])

print("\n" + "=" * 100 + "\n")
print("Packages only on {0}:\n\n{1}".format(args.server1, ", ".join(pkgsonly1)))
print("\n" + "=" * 100 + "\n")
print("Packages only on {0}:\n\n{1}".format(args.server2, ", ".join(pkgsonly2)))
print("\n" + "=" * 100 + "\n")
print("Different package versions")
print(table)
exit(0)