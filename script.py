import argparse
import subprocess
import os
import prettytable

parser = argparse.ArgumentParser()
parser.add_argument("server1", help="Name or ip of sevrer1")
parser.add_argument("server2", help="Name or ip of server2")
parser.add_argument("username", help="Username for accessing the servers")
parser.add_argument("sshkey", help="Path to ssh key for accessing the servers")
args = parser.parse_args()

pkgsonly1 = []
pkgsonly2 = []
pkgsdiff = {}

def package_list(server):
    try:
        process = subprocess.run("ssh -i " + args.sshkey + " " + args.username + "@" + server + " 'test -e /etc/lsb-release'", shell=True, check=True) # Test if OS is deb based
    except subprocess.CalledProcessError:
        process = False
    if process:
        command = ["ssh -i " + args.sshkey + " " + args.username + "@" + server + " \"dpkg -l | grep '^ii'\" | awk '{print $2, $3}' > " + server] # Command for deb based OS
    else:
        command = ["ssh -i " + args.sshkey + " " + args.username + "@" + server + " 'rpm -qa --qf \"%{NAME} %{VERSION}\n\"' > " + server] # Command for rpm based OS
    subprocess.run(command, shell=True)
    with open(server) as file1:
        serverdict = dict([line.split() for line in file1])
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

os.remove(args.server1)
os.remove(args.server2)